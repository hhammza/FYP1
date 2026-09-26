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


def optional_threshold(value):
    """A threshold from the request, or None so the model uses the one it
    was validated at (its metrics.json), not a number typed in here."""
    if value is None or str(value).strip() == '':
        return None
    return float(value)


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
                body = request.body.decode('utf-8')
                data = json.loads(body) if body else {}

            antibiotic = data.get('antibiotic', '').strip()
            if not antibiotic:
                return json_error('antibiotic is required')

            taxon_id = data.get('taxon_id', None)
            mic_value = data.get('mic_value', None)
            mic_sign = data.get('mic_sign', None)
            genus = data.get('genus', 'unknown')
            species = data.get('species', 'unknown')
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

        except Exception as e:
            traceback.print_exc()
            return json_error(str(e), 500)


class ResistancePredictionView(View):
    """K-mer CNN/MLP resistance prediction from FASTA."""

    def post(self, request):
        refused = rate_limited(request, 'predict') or upload_too_large(request)
        if refused:
            return refused
        try:
            antibiotic = request.POST.get('antibiotic', '').strip()
            threshold = optional_threshold(request.POST.get('threshold'))

            fasta_text = ''
            if 'fasta_file' in request.FILES:
                fasta_file = request.FILES['fasta_file']
                if fasta_file.size > settings.MAX_FASTA_BYTES:
                    return fasta_too_large()
                fasta_text = fasta_file.read().decode('utf-8', errors='ignore')
            elif request.content_type and 'application/json' in request.content_type:
                body = json.loads(request.body.decode('utf-8'))
                fasta_text = body.get('fasta_text', '')
                antibiotic = body.get('antibiotic', antibiotic)
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
            return JsonResponse(result)

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
                antibiotic = request.POST.get('antibiotic', '').strip()
                n_weeks = int(request.POST.get('n_weeks', n_weeks_default))
            elif request.content_type and 'application/json' in request.content_type:
                body = json.loads(request.body.decode('utf-8'))
                fasta_text = body.get('fasta_text', '')
                antibiotic = body.get('antibiotic', '').strip()
                n_weeks = int(body.get('n_weeks', n_weeks_default))
            else:
                fasta_text = request.POST.get('fasta_text', '')
                antibiotic = request.POST.get('antibiotic', '').strip()
                n_weeks = int(request.POST.get('n_weeks', n_weeks_default))

            if not fasta_text:
                return json_error('FASTA sequence or file is required')
            if len(fasta_text) > settings.MAX_FASTA_BYTES:
                return fasta_too_large()
            if not antibiotic:
                return json_error('antibiotic is required')
            if n_weeks < 1 or n_weeks > 52:
                return json_error('n_weeks must be between 1 and 52')

            model = model_registry.get_timeline()
            if model is None:
                return json_error('Model not initialized', 503)

            result = model.predict(fasta_text, antibiotic, n_weeks=n_weeks)
            return JsonResponse(result)

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
        kmer = model_registry.get_kmer()
        timeline = model_registry.get_timeline()
        results = {}
        if lgbm:
            lgbm._load()
            results['lgbm'] = {'trained': lgbm.is_trained}
        if kmer:
            kmer._load()
            results['kmer'] = {'trained': kmer.is_trained}
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
                body = json.loads(request.body.decode('utf-8'))
            else:
                body = request.POST

            model_name = body.get('model', 'lgbm')
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
