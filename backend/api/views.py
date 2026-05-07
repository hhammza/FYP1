import json
import traceback
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from api import model_registry


def json_error(message, status=400):
    return JsonResponse({'error': message}, status=status)


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
            threshold = float(data.get('threshold', 0.40))

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
            threshold = float(request.POST.get('threshold', 0.5))

            fasta_text = ''
            if 'fasta_file' in request.FILES:
                fasta_file = request.FILES['fasta_file']
                fasta_text = fasta_file.read().decode('utf-8', errors='ignore')
            elif request.content_type and 'application/json' in request.content_type:
                body = json.loads(request.body.decode('utf-8'))
                fasta_text = body.get('fasta_text', '')
                antibiotic = body.get('antibiotic', antibiotic)
                threshold = float(body.get('threshold', threshold))
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
        antibiotics = [
            'ampicillin', 'amoxicillin', 'amoxicillin/clavulanic acid',
            'piperacillin', 'piperacillin/tazobactam', 'oxacillin',
            'cefazolin', 'cefoxitin', 'cefotaxime', 'ceftazidime',
            'ceftriaxone', 'cefepime', 'cefuroxime', 'cephalothin',
            'imipenem', 'meropenem', 'ertapenem', 'doripenem',
            'aztreonam', 'ciprofloxacin', 'levofloxacin', 'norfloxacin',
            'nalidixic acid', 'ofloxacin', 'gentamicin', 'tobramycin',
            'amikacin', 'streptomycin', 'neomycin', 'kanamycin',
            'tetracycline', 'doxycycline', 'minocycline', 'tigecycline',
            'sulfamethoxazole', 'trimethoprim', 'trimethoprim/sulfamethoxazole',
            'chloramphenicol', 'azithromycin', 'erythromycin',
            'colistin', 'polymyxin b', 'vancomycin', 'teicoplanin',
            'clindamycin', 'nitrofurantoin', 'rifampicin', 'rifampin',
        ]
        return JsonResponse({'antibiotics': sorted(antibiotics)})


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

            def train_in_background(model_name, model_dir, data_dir):
                try:
                    sys.path.insert(0, str(settings.BASE_DIR))
                    from train_models import train_lgbm, train_kmer
                    if model_name == 'lgbm':
                        train_lgbm(data_dir, model_dir)
                        model_registry.get_lgbm()._load()
                    elif model_name == 'kmer':
                        train_kmer(data_dir, model_dir)
                        model_registry.get_kmer()._load()
                except Exception as e:
                    print(f"[Training] Error: {e}")
                    traceback.print_exc()

            thread = threading.Thread(
                target=train_in_background,
                args=(model_name, str(settings.TRAINED_MODELS_DIR), str(settings.DATA_DIR)),
                daemon=True,
            )
            thread.start()

            return JsonResponse({
                'status': 'Training started',
                'model': model_name,
                'message': f'Training {model_name} model in background. Check /api/health/ for status.',
            })

        except Exception as e:
            traceback.print_exc()
            return json_error(str(e), 500)
