"""The JSON API behind the Flask frontend.

No CSRF protection is needed, and none is installed: CSRF abuses credentials a
browser sends by itself (cookies), and this API uses none. It is called by the
Flask server, and its two admin endpoints need an X-Admin-Token header, which
a browser never adds on its own.
"""
import csv
import hmac
import io
import json
import os
import traceback
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django_ratelimit.core import is_ratelimited
from amr_constants import UI_ANTIBIOTICS
from api import model_registry


def json_error(message, status=400):
    return JsonResponse({'error': message}, status=status)


def client_ip(group, request):
    """The caller's IP for rate limiting. The Flask frontend passes the
    browser's address in X-Forwarded-For; a direct caller can set that header
    too, so this limits casual abuse, not a determined attacker."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return forwarded.split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')


def rate_limited(request, group):
    """429 response once this IP passes settings.RATE_LIMITS[group], else None."""
    if is_ratelimited(request, group=group, key=client_ip,
                      rate=settings.RATE_LIMITS[group], increment=True):
        return json_error(f'Too many requests ({settings.RATE_LIMITS[group]} per IP). '
                          'Wait a minute and try again.', 429)
    return None


def upload_too_large(request):
    """413 response when the request body could hold a FASTA over the limit,
    checked before the body is read, else None."""
    try:
        size = int(request.META.get('CONTENT_LENGTH') or 0)
    except ValueError:
        size = 0
    if size > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
        return fasta_too_large()
    return None


def fasta_too_large():
    mb = settings.MAX_FASTA_BYTES // (1024 * 1024)
    return json_error(f'FASTA is too large: the limit is {mb} MB.', 413)


def admin_denied(request):
    """401/503 response unless the request carries the admin token, else None."""
    token = settings.ADMIN_TOKEN
    if not token:
        return json_error('Admin endpoints are switched off: set ADMIN_TOKEN on the backend.', 503)
    sent = request.headers.get('X-Admin-Token', '')
    if not hmac.compare_digest(sent.encode(), token.encode()):
        return json_error('Admin token missing or wrong.', 401)
    return None


class BadInput(ValueError):
    """A request field that cannot be used. Every view answers it with a 400
    and this message, instead of a 500 with a raw Python error."""


def read_json(request):
    """The request body as a JSON object ({} when empty)."""
    try:
        body = request.body.decode('utf-8')
        data = json.loads(body) if body.strip() else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise BadInput('The request body is not valid JSON.')
    if not isinstance(data, dict):
        raise BadInput('The request body must be a JSON object.')
    return data


def text_field(data, name, default=''):
    """A text field, stripped; `default` when missing or null."""
    value = data.get(name, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise BadInput(f'{name} must be text.')
    return value.strip()


def optional_number(data, name, whole=False):
    """A positive number (a whole one if `whole`), or None when left out."""
    value = data.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    kind = 'a positive whole number' if whole else 'a positive number'
    if isinstance(value, bool):
        raise BadInput(f'{name} must be {kind}.')
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise BadInput(f'{name} must be {kind}, not "{value}".')
    if not 0 < number < float('inf') or (whole and number != int(number)):
        raise BadInput(f'{name} must be {kind}, not "{value}".')
    return int(number) if whole else number


def whole_number(data, name, default, low, high):
    """A whole number from `low` to `high`; `default` when left out."""
    value = data.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    message = f'{name} must be a whole number from {low} to {high}.'
    if isinstance(value, bool):
        raise BadInput(message)
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise BadInput(message)
    if number != number or not low <= number <= high or number != int(number):   # NaN, range, fraction
        raise BadInput(message)
    return int(number)


def optional_threshold(value):
    """A threshold from the request, or None so the model uses the one it
    was validated at (its metrics.json), not a number typed in here."""
    if value is None or str(value).strip() == '':
        return None
    message = 'threshold must be a number between 0 and 1.'
    if isinstance(value, bool):
        raise BadInput(message)
    try:
        threshold = float(value)
    except (TypeError, ValueError):
        raise BadInput(message)
    if not 0 < threshold < 1:                 # also rejects NaN and infinity
        raise BadInput(message)
    return threshold


class HealthView(View):
    def get(self, request):
        lgbm = model_registry.get_lgbm()
        kmer = model_registry.get_kmer()
        timeline = model_registry.get_timeline()
        return JsonResponse({
            'status': 'running',
            'models': {
                'lgbm_forecasting': lgbm.status if lgbm else {'trained': False},
                'kmer_resistance': kmer.status if kmer else {'trained': False},
                'mutation_timeline': timeline.status if timeline else {'trained': False},
            }
        })


class ResistanceForecastView(View):
    """LightGBM AMR forecasting endpoint."""

    def post(self, request):
        limited = rate_limited(request, 'forecast')
        if limited:
            return limited
        try:
            if request.content_type and 'multipart' in request.content_type:
                data = request.POST
            else:
                data = read_json(request)

            antibiotic = text_field(data, 'antibiotic')
            if not antibiotic:
                return json_error('antibiotic is required')

            taxon_id = optional_number(data, 'taxon_id', whole=True)
            mic_value = optional_number(data, 'mic_value')
            mic_sign = text_field(data, 'mic_sign') or None
            if mic_sign and mic_sign not in MIC_SIGNS:
                raise BadInput(f'mic_sign must be one of = < <= > >=, not "{mic_sign}".')
            genus = text_field(data, 'genus') or 'unknown'
            species = text_field(data, 'species') or 'unknown'
            threshold = optional_threshold(data.get('threshold'))

            model = model_registry.get_lgbm()
            if model is None:
                return json_error('Model not initialized', 503)

            result = model.predict(
                antibiotic=antibiotic,
                taxon_id=taxon_id,
                mic_value=mic_value,
                mic_sign=mic_sign,
                genus=genus,
                species=species,
                threshold=threshold,
            )
            drug_info = model.get_drug_class_summary(antibiotic)
            result.update(drug_info)

            # Multi-antibiotic comparison
            common_antibiotics = [
                'ampicillin', 'ciprofloxacin', 'tetracycline',
                'gentamicin', 'imipenem', 'trimethoprim/sulfamethoxazole',
                'chloramphenicol', 'cefotaxime'
            ]
            comparison = []
            for ab in common_antibiotics:
                r = model.predict(
                    antibiotic=ab,
                    taxon_id=taxon_id,
                    mic_value=None,
                    genus=genus,
                    species=species,
                )
                comparison.append({'antibiotic': ab, 'resistance_probability': r['probability'] * 100})

            result['comparison_chart'] = comparison
            return JsonResponse(result)

        except BadInput as e:
            return json_error(str(e), 400)
        except Exception as e:
            traceback.print_exc()
            return json_error(str(e), 500)


MIC_SIGNS = {'=', '==', '<', '<=', '>', '>=', '\u2264', '\u2265', '=<', '=>'}


def check_batch_row(row, known_antibiotics, normalize):
    """(clean record, None) or (None, error message) for one CSV row."""
    rec = {k: (row.get(k) or '').strip() for k in settings.BATCH_COLUMNS}
    ab = normalize(rec['antibiotic'])
    if not ab:
        return None, 'antibiotic is required'
    if known_antibiotics and ab not in known_antibiotics:
        return None, f'unknown antibiotic "{rec["antibiotic"]}" (the model was not trained on it)'
    out = {'antibiotic': ab, 'genus': rec['genus'] or 'unknown', 'species': rec['species'] or 'unknown',
           'taxon_id': None, 'mic_value': None, 'mic_sign': rec['mic_sign'] or None}
    if rec['taxon_id']:
        try:
            out['taxon_id'] = int(float(rec['taxon_id']))
            if out['taxon_id'] < 1:
                raise ValueError
        except ValueError:
            return None, f'taxon_id must be a positive whole number, not "{rec["taxon_id"]}"'
    if rec['mic_value']:
        try:
            out['mic_value'] = float(rec['mic_value'])
            if not out['mic_value'] > 0:
                raise ValueError
        except ValueError:
            return None, f'mic_value must be a positive number, not "{rec["mic_value"]}"'
    if out['mic_sign'] and out['mic_sign'] not in MIC_SIGNS:
        return None, f'mic_sign must be one of = < <= > >=, not "{rec["mic_sign"]}"'
    if out['mic_value'] is None:
        out['mic_sign'] = None        # a sign alone says nothing; /forecast ignores it too
    return out, None


class BatchForecastView(View):
    """Many isolates at once from a CSV upload (field `file`).

    Columns: antibiotic (required), genus, species, taxon_id, mic_value,
    mic_sign. Each input row gets one result row, with `error` set instead of
    a prediction when the row is invalid. Valid rows are predicted in one call.
    """

    def post(self, request):
        refused = rate_limited(request, 'batch')
        if refused:
            return refused
        mb = settings.BATCH_MAX_BYTES // (1024 * 1024)
        too_large = json_error(f'CSV is too large: the limit is {mb} MB.', 413)
        try:
            size = int(request.META.get('CONTENT_LENGTH') or 0)
        except ValueError:
            size = 0
        if size > settings.BATCH_MAX_BYTES + 64 * 1024:
            return too_large
        upload = request.FILES.get('file')
        if upload is None:
            return json_error('Upload a CSV file in the field "file".')
        if upload.size > settings.BATCH_MAX_BYTES:
            return too_large

        model = model_registry.get_lgbm()
        if model is None or not model.is_trained:
            return json_error('The forecasting model is not loaded.', 503)

        try:
            text = upload.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return json_error('The CSV must be UTF-8 text.')
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            return json_error('The CSV is empty.')
        reader.fieldnames = [(f or '').strip().lower() for f in reader.fieldnames]
        if 'antibiotic' not in reader.fieldnames:
            return json_error('The CSV needs an "antibiotic" column. Columns: '
                              + ', '.join(settings.BATCH_COLUMNS))
        rows = []
        for row in reader:
            if not any(isinstance(v, str) and v.strip() for v in row.values()):
                continue                      # blank line
            if len(rows) >= settings.BATCH_MAX_ROWS:
                return json_error(f'Too many rows: the limit is {settings.BATCH_MAX_ROWS:,}.', 413)
            rows.append(row)
        if not rows:
            return json_error('The CSV has a header but no rows.')

        known = set(model.vocabulary['antibiotics'])
        checked = [check_batch_row(r, known, model._normalize_antibiotic) for r in rows]
        valid = [(i, rec) for i, (rec, err) in enumerate(checked) if rec]
        probs = {}
        if valid:
            import pandas as pd
            try:
                p = model.predict_frame(pd.DataFrame([rec for _, rec in valid]))
            except Exception:
                traceback.print_exc()
                return json_error('The model failed on this file.', 500)
            probs = {i: float(v) for (i, _), v in zip(valid, p)}

        threshold = model.threshold
        results = []
        for i, (row, (rec, err)) in enumerate(zip(rows, checked)):
            out = {'row': i + 1}
            out.update({k: (row.get(k) or '').strip() for k in settings.BATCH_COLUMNS})
            if err:
                out.update(prediction='', probability=None, error=err)
            else:
                out.update(antibiotic=rec['antibiotic'],
                           prediction='Resistant' if probs[i] >= threshold else 'Susceptible',
                           probability=round(probs[i], 4), error='')
            results.append(out)

        by_ab = {}
        for r in results:
            if not r['error']:
                d = by_ab.setdefault(r['antibiotic'], {'antibiotic': r['antibiotic'], 'n': 0, 'resistant': 0})
                d['n'] += 1
                d['resistant'] += r['prediction'] == 'Resistant'
        n_ok = sum(1 for r in results if not r['error'])
        n_res = sum(d['resistant'] for d in by_ab.values())
        return JsonResponse({
            'rows': results,
            'summary': {
                'rows': len(results), 'predicted': n_ok, 'errors': len(results) - n_ok,
                'resistant': n_res, 'susceptible': n_ok - n_res,
                'by_antibiotic': sorted(by_ab.values(), key=lambda d: (-d['n'], d['antibiotic'])),
            },
            'threshold': threshold,
            'model_run': model.run_id,
            'calibrated': bool(model.calibration),
        })


class ResistancePredictionView(View):
    """K-mer CNN/MLP resistance prediction from FASTA."""

    def post(self, request):
        refused = rate_limited(request, 'predict') or upload_too_large(request)
        if refused:
            return refused
        try:
            antibiotic = text_field(request.POST, 'antibiotic')
            threshold = optional_threshold(request.POST.get('threshold'))

            fasta_text = ''
            if 'fasta_file' in request.FILES:
                fasta_file = request.FILES['fasta_file']
                if fasta_file.size > settings.MAX_FASTA_BYTES:
                    return fasta_too_large()
                fasta_text = fasta_file.read().decode('utf-8', errors='ignore')
            elif request.content_type and 'application/json' in request.content_type:
                body = read_json(request)
                fasta_text = text_field(body, 'fasta_text')
                antibiotic = text_field(body, 'antibiotic', antibiotic)
                if body.get('threshold') is not None:
                    threshold = optional_threshold(body.get('threshold'))
            else:
                fasta_text = request.POST.get('fasta_text', '')

            if not fasta_text:
                return json_error('FASTA sequence or file is required')
            if len(fasta_text) > settings.MAX_FASTA_BYTES:
                return fasta_too_large()
            if not antibiotic:
                return json_error('antibiotic is required')

            model = model_registry.get_kmer()
            if model is None:
                return json_error('Model not initialized', 503)

            result = model.predict(fasta_text, antibiotic, threshold=threshold)
            if 'error' in result:
                # the genome model refuses rather than guesses (e.g. a genome
                # under 100 kb): a 400 with the reason, not a prediction
                return JsonResponse(result, status=400)
            return JsonResponse(result)

        except BadInput as e:
            return json_error(str(e), 400)
        except Exception as e:
            traceback.print_exc()
            return json_error(str(e), 500)


class MutationTimelineView(View):
    """Bacterial mutation timeline endpoint."""

    def post(self, request):
        refused = rate_limited(request, 'timeline') or upload_too_large(request)
        if refused:
            return refused
        try:
            n_weeks_default = 8
            fasta_text = ''
            antibiotic = ''
            n_weeks = n_weeks_default

            if 'fasta_file' in request.FILES:
                fasta_file = request.FILES['fasta_file']
                if fasta_file.size > settings.MAX_FASTA_BYTES:
                    return fasta_too_large()
                fasta_text = fasta_file.read().decode('utf-8', errors='ignore')
                fields = request.POST
            elif request.content_type and 'application/json' in request.content_type:
                fields = read_json(request)
                fasta_text = text_field(fields, 'fasta_text')
            else:
                fields = request.POST
                fasta_text = request.POST.get('fasta_text', '')
            antibiotic = text_field(fields, 'antibiotic')
            n_weeks = whole_number(fields, 'n_weeks', n_weeks_default, 1, 52)

            if not fasta_text:
                return json_error('FASTA sequence or file is required')
            if len(fasta_text) > settings.MAX_FASTA_BYTES:
                return fasta_too_large()
            if not antibiotic:
                return json_error('antibiotic is required')

            model = model_registry.get_timeline()
            if model is None:
                return json_error('Model not initialized', 503)

            result = model.predict(fasta_text, antibiotic, n_weeks=n_weeks)
            return JsonResponse(result)

        except BadInput as e:
            return json_error(str(e), 400)
        except Exception as e:
            traceback.print_exc()
            return json_error(str(e), 500)


class AntibioticListView(View):
    """Return list of supported antibiotics."""
    def get(self, request):
        return JsonResponse({'antibiotics': sorted(UI_ANTIBIOTICS)})


class VocabularyView(View):
    """What each model can actually distinguish.

    The forms populate themselves from this, so a user cannot enter a value
    the model has no category for and then wonder why it changed nothing.
    """
    def get(self, request):
        lgbm = model_registry.get_lgbm()
        kmer = model_registry.get_kmer()
        return JsonResponse({
            'lgbm': lgbm.vocabulary if lgbm and lgbm.is_trained else None,
            'kmer': {'antibiotics': sorted(kmer.ab_list)} if kmer and kmer.ab_list else None,
        })


class GeneReportView(View):
    """AMRFinderPlus run summary, built by experiments/genome/features/export_gene_report.py."""
    def get(self, request):
        path = os.path.join(str(settings.TRAINED_MODELS_DIR), 'gene_report.json')
        if not os.path.exists(path):
            return json_error('gene_report.json not found. Run: '
                              'python experiments/genome/features/export_gene_report.py', status=404)
        with open(path) as fh:
            return JsonResponse(json.load(fh))


_gene_hits = {}


def load_gene_hits():
    """gene_hits.json, read once; None if it has not been built."""
    if 'data' not in _gene_hits:
        path = os.path.join(str(settings.TRAINED_MODELS_DIR), 'gene_hits.json')
        if not os.path.exists(path):
            return None
        with open(path) as fh:
            _gene_hits['data'] = json.load(fh)
    return _gene_hits['data']


GENE_HITS_MISSING = ('gene_hits.json not found. Run: '
                     'python experiments/genome/features/export_gene_report.py')


def csv_download(rows, filename):
    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)
    response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class GeneMatrixCSVView(View):
    """The gene matrix as CSV: one row per genome, one 0/1 column per gene or
    mutation. Same content as experiments/genome/features/gene_matrix.parquet."""
    def get(self, request):
        data = load_gene_hits()
        if data is None:
            return json_error(GENE_HITS_MISSING, status=404)
        symbols = sorted(data['symbols'])
        column = {s: i for i, s in enumerate(symbols)}
        rows = [['Genome ID'] + symbols]
        for genome_id in sorted(data['genomes']):
            values = [0] * len(symbols)
            for hit in data['genomes'][genome_id]['hits']:
                values[column[hit[0]]] = 1
            rows.append([genome_id] + values)
        return csv_download(rows, 'gene_matrix.csv')


class GeneInfoCSVView(View):
    """One row per matrix column: what each gene or mutation is."""
    def get(self, request):
        data = load_gene_hits()
        if data is None:
            return json_error(GENE_HITS_MISSING, status=404)
        carriers = {}
        for genome in data['genomes'].values():
            for symbol in {hit[0] for hit in genome['hits']}:
                carriers[symbol] = carriers.get(symbol, 0) + 1
        rows = [['symbol', 'type', 'class', 'subclass', 'genomes', 'name']]
        for symbol in sorted(data['symbols']):
            kind, cls, subclass, name = data['symbols'][symbol]
            rows.append([symbol, kind, cls, subclass, carriers.get(symbol, 0), name])
        return csv_download(rows, 'gene_info.csv')


class GeneLookupView(View):
    """Every core AMR gene and mutation AMRFinderPlus found in one genome."""
    def get(self, request, genome_id):
        data = load_gene_hits()
        if data is None:
            return json_error(GENE_HITS_MISSING, status=404)
        genome_id = genome_id.strip()
        entry = data['genomes'].get(genome_id)
        if entry is None:
            # Not searched: no complete assembly, or the run has not reached it
            return JsonResponse({'genome_id': genome_id, 'searched': False, 'genes': []})
        genes = []
        for symbol, identity, coverage, method in entry['hits']:
            kind, cls, subclass, name = data['symbols'].get(symbol, [None, None, None, None])
            genes.append({'gene': symbol, 'name': name, 'type': kind, 'class': cls, 'subclass': subclass,
                          'identity': identity, 'coverage': coverage, 'method': method})
        return JsonResponse({'genome_id': genome_id, 'searched': True, 'species': entry['species'],
                             'genes': genes})


class ReloadModelsView(View):
    """Force reload all models from disk without restarting server."""
    def post(self, request):
        denied = admin_denied(request)
        if denied:
            return denied
        lgbm = model_registry.get_lgbm()
        timeline = model_registry.get_timeline()
        results = {}
        if lgbm:
            lgbm._load()
            results['lgbm'] = {'trained': lgbm.is_trained}
        # chosen again, not just re-read: a genome model promoted since start-up takes over /predict
        kmer = model_registry.reload_kmer()
        if kmer:
            results['kmer'] = {'trained': kmer.is_trained,
                               'run_id': getattr(kmer, 'meta', {}).get('run_id')}
        if timeline:
            timeline._load()
            results['timeline'] = {'trained': timeline.is_trained}
        return JsonResponse({'status': 'reloaded', 'models': results})


class TrainModelView(View):
    """Trigger model training asynchronously."""

    def post(self, request):
        denied = admin_denied(request)
        if denied:
            return denied
        try:
            if request.content_type and 'application/json' in request.content_type:
                body = read_json(request)
            else:
                body = request.POST

            model_name = text_field(body, 'model', 'lgbm')
            if model_name not in ('lgbm', 'kmer'):
                return json_error("model must be 'lgbm' or 'kmer'")

            import threading
            import sys
            import os
            from django.conf import settings

            # Fail now rather than report "Training started" for a thread
            # that will find no data.
            sys.path.insert(0, str(settings.BASE_DIR))
            from train_models import resolve_data_dir
            if resolve_data_dir(str(settings.DATA_DIR)) is None:
                return json_error('Training data not found. Expected Data/amr_output/ '
                                  'and Data/mapped_output/ in the project root.', 503)

            # Train into a separate folder and leave the served model loaded.
            # The trainer writes neither the promoted model's threshold and
            # calibration nor its metrics.json, so training over the served
            # files would swap the model while the UI kept its old numbers.
            candidate_dir = settings.CANDIDATE_MODELS_DIR / model_name
            os.makedirs(candidate_dir, exist_ok=True)

            def train_in_background(model_name, model_dir, data_dir):
                try:
                    sys.path.insert(0, str(settings.BASE_DIR))
                    from train_models import train_lgbm, train_kmer
                    if model_name == 'lgbm':
                        train_lgbm(data_dir, model_dir)
                    elif model_name == 'kmer':
                        train_kmer(data_dir, model_dir)
                    print(f"[Training] {model_name} candidate saved to {model_dir}")
                except Exception as e:
                    print(f"[Training] Error: {e}")
                    traceback.print_exc()

            thread = threading.Thread(
                target=train_in_background,
                args=(model_name, str(candidate_dir), str(settings.DATA_DIR)),
                daemon=True,
            )
            thread.start()

            rel = os.path.relpath(candidate_dir, settings.BASE_DIR).replace(os.sep, '/')
            return JsonResponse({
                'status': 'Training started',
                'model': model_name,
                'candidate_dir': rel,
                'message': (f'Training a {model_name} candidate in the background, saved to '
                            f'backend/{rel}/. The served model is not changed; to serve the '
                            f'candidate it must be evaluated and promoted with experiments/promote.py.'),
            })

        except BadInput as e:
            return json_error(str(e), 400)
        except Exception as e:
            traceback.print_exc()
            return json_error(str(e), 500)


class ModelReportView(View):
    """Evaluation results for every model, built by experiments/export_report.py."""
    def get(self, request):
        path = os.path.join(str(settings.TRAINED_MODELS_DIR), 'model_report.json')
        if not os.path.exists(path):
            return json_error('model_report.json not found. Run: '
                              'python experiments/export_report.py', status=404)
        with open(path) as fh:
            report = json.load(fh)
        lgbm = model_registry.get_lgbm()
        kmer = model_registry.get_kmer()
        report['live'] = {
            'lgbm_loaded': bool(lgbm and lgbm.is_trained),
            'kmer_loaded': bool(kmer and kmer.is_trained),
        }
        return JsonResponse(report)
