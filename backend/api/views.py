import csv
import io
import json
import os
import traceback
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from amr_constants import UI_ANTIBIOTICS
from api import model_registry


def json_error(message, status=400):
    return JsonResponse({'error': message}, status=status)


def optional_threshold(value):
    """A threshold from the request, or None so the model uses the one it
    was validated at (its metrics.json), not a number typed in here."""
    if value is None or str(value).strip() == '':
        return None
    return float(value)


@method_decorator(csrf_exempt, name='dispatch')
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


@method_decorator(csrf_exempt, name='dispatch')
class ResistanceForecastView(View):
    """LightGBM AMR forecasting endpoint."""

    def post(self, request):
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


@method_decorator(csrf_exempt, name='dispatch')
class ResistancePredictionView(View):
    """K-mer CNN/MLP resistance prediction from FASTA."""

    def post(self, request):
        try:
            antibiotic = request.POST.get('antibiotic', '').strip()
            threshold = optional_threshold(request.POST.get('threshold'))

            fasta_text = ''
            if 'fasta_file' in request.FILES:
                fasta_file = request.FILES['fasta_file']
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


@method_decorator(csrf_exempt, name='dispatch')
class MutationTimelineView(View):
    """Bacterial mutation timeline endpoint."""

    def post(self, request):
        try:
            n_weeks_default = 8
            fasta_text = ''
            antibiotic = ''
            n_weeks = n_weeks_default

            if 'fasta_file' in request.FILES:
                fasta_file = request.FILES['fasta_file']
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


@method_decorator(csrf_exempt, name='dispatch')
class AntibioticListView(View):
    """Return list of supported antibiotics."""
    def get(self, request):
        return JsonResponse({'antibiotics': sorted(UI_ANTIBIOTICS)})


@method_decorator(csrf_exempt, name='dispatch')
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


@method_decorator(csrf_exempt, name='dispatch')
class ReloadModelsView(View):
    """Force reload all models from disk without restarting server."""
    def post(self, request):
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


@method_decorator(csrf_exempt, name='dispatch')
class TrainModelView(View):
    """Trigger model training asynchronously."""

    def post(self, request):
        try:
            if request.content_type and 'application/json' in request.content_type:
                body = json.loads(request.body.decode('utf-8'))
            else:
                body = request.POST

            model_name = body.get('model', 'lgbm')

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
