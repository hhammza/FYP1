"""
Flask Frontend for AMR Prediction System
Serves HTML pages and proxies requests to Django backend (port 8000)
"""
import os
import json
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fyp-flask-frontend-2024')

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8000/api')

# Version of the companion `amrpredict` package documented on /library.
# Keep in step with amrpredict-lib/pyproject.toml.
LIB_VERSION = os.environ.get('LIB_VERSION', '0.1.0')

ANTIBIOTICS = [
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

BACTERIA_LIST = [
    'Escherichia coli', 'Klebsiella pneumoniae', 'Pseudomonas aeruginosa',
    'Acinetobacter baumannii', 'Staphylococcus aureus', 'Enterococcus faecium',
    'Salmonella enterica', 'Streptococcus pneumoniae', 'Mycobacterium tuberculosis',
    'Campylobacter jejuni', 'Campylobacter coli', 'Helicobacter pylori',
    'Shigella flexneri', 'Enterobacter cloacae', 'Proteus mirabilis',
]


def _parse_response(r):
    try:
        return r.json(), r.status_code
    except (ValueError, requests.exceptions.JSONDecodeError):
        preview = r.text[:200] if r.text else '(empty)'
        return {'error': f'Backend returned non-JSON response (HTTP {r.status_code}): {preview}'}, r.status_code


def backend_get(endpoint, timeout=10):
    try:
        r = requests.get(f'{BACKEND_URL}/{endpoint}', timeout=timeout)
        return _parse_response(r)
    except requests.exceptions.ConnectionError:
        return {'error': 'Django backend not running. Start it with: python manage.py runserver'}, 503
    except Exception as e:
        return {'error': str(e)}, 500


def backend_post(endpoint, data=None, files=None, json_data=None, timeout=30):
    try:
        url = f'{BACKEND_URL}/{endpoint}'
        if files:
            r = requests.post(url, data=data, files=files, timeout=timeout)
        elif json_data is not None:
            r = requests.post(url, json=json_data, timeout=timeout)
        else:
            r = requests.post(url, data=data, timeout=timeout)
        return _parse_response(r)
    except requests.exceptions.ConnectionError:
        return {'error': 'Django backend not running. Start it with: python manage.py runserver'}, 503
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/')
def index():
    health_data, _ = backend_get('health/')
    return render_template('index.html', health=health_data)


@app.route('/forecast', methods=['GET', 'POST'])
def resistance_forecast():
    result = None
    error = None
    form_data = {}

    if request.method == 'POST':
        form_data = {
            'antibiotic': request.form.get('antibiotic', ''),
            'taxon_id': request.form.get('taxon_id', ''),
            'mic_value': request.form.get('mic_value', ''),
            'mic_sign': request.form.get('mic_sign', ''),
            'genus': request.form.get('genus', 'unknown'),
            'species': request.form.get('species', 'unknown'),
            'threshold': request.form.get('threshold', '0.40'),
        }
        payload = {k: v for k, v in form_data.items() if v and v != 'unknown'}
        data, status = backend_post('forecast/', json_data=payload)
        if status == 200:
            result = data
        else:
            error = data.get('error', 'Prediction failed')

    return render_template(
        'resistance_forecast.html',
        result=result,
        error=error,
        form_data=form_data,
    )


@app.route('/predict', methods=['GET', 'POST'])
def resistance_prediction():
    result = None
    error = None
    form_data = {'antibiotic': '', 'threshold': '0.5'}

    if request.method == 'POST':
        antibiotic = request.form.get('antibiotic', '').strip()
        threshold = request.form.get('threshold', '0.5')
        form_data = {'antibiotic': antibiotic, 'threshold': threshold}

        fasta_file = request.files.get('fasta_file')
        fasta_text = request.form.get('fasta_text', '').strip()

        if fasta_file and fasta_file.filename:
            files = {'fasta_file': (fasta_file.filename, fasta_file.stream, 'text/plain')}
            post_data = {'antibiotic': antibiotic, 'threshold': threshold}
            data, status = backend_post('predict/', data=post_data, files=files)
        elif fasta_text:
            data, status = backend_post('predict/', json_data={
                'fasta_text': fasta_text, 'antibiotic': antibiotic, 'threshold': float(threshold)
            })
        else:
            error = 'Please provide a FASTA file or paste FASTA sequence text.'
            return render_template('resistance_prediction.html', result=result, error=error,
                                   form_data=form_data)

        if status == 200:
            result = data
        else:
            error = data.get('error', 'Prediction failed')

    return render_template(
        'resistance_prediction.html',
        result=result,
        error=error,
        form_data=form_data,
    )


@app.route('/timeline', methods=['GET', 'POST'])
def mutation_timeline():
    result = None
    error = None
    form_data = {'antibiotic': '', 'n_weeks': '8'}

    if request.method == 'POST':
        antibiotic = request.form.get('antibiotic', '').strip()
        n_weeks = request.form.get('n_weeks', '8')
        form_data = {'antibiotic': antibiotic, 'n_weeks': n_weeks}

        fasta_file = request.files.get('fasta_file')
        fasta_text = request.form.get('fasta_text', '').strip()

        if fasta_file and fasta_file.filename:
            files = {'fasta_file': (fasta_file.filename, fasta_file.stream, 'text/plain')}
            post_data = {'antibiotic': antibiotic, 'n_weeks': n_weeks}
            data, status = backend_post('timeline/', data=post_data, files=files)
        elif fasta_text:
            data, status = backend_post('timeline/', json_data={
                'fasta_text': fasta_text, 'antibiotic': antibiotic, 'n_weeks': int(n_weeks)
            })
        else:
            error = 'Please provide a FASTA file or paste FASTA sequence text.'
            return render_template('mutation_timeline.html', result=result, error=error,
                                   form_data=form_data)

        if status == 200:
            result = data
        else:
            error = data.get('error', 'Prediction failed')

    return render_template(
        'mutation_timeline.html',
        result=result,
        error=error,
        form_data=form_data,
    )


@app.route('/train', methods=['GET', 'POST'])
def train_model():
    result = None
    error = None

    if request.method == 'POST':
        model_name = request.form.get('model', 'lgbm')
        data, status = backend_post('train/', json_data={'model': model_name})
        if status == 200:
            result = data
        else:
            error = data.get('error', 'Training failed to start')

    return render_template('train.html', result=result, error=error)


@app.route('/api/health')
def health_proxy():
    data, status = backend_get('health/')
    return jsonify(data), status


# Spellings that exist in the training vocabulary but should not be offered as
# choices: a drug class rather than a drug, two misspellings, and duplicate
# separator variants of combinations that also appear in canonical '/' form.
# Excluding them keeps the dropdown honest (everything listed is a value the
# model recognises) without showing the same drug three times.
VOCAB_EXCLUDE = {
    'carbapenem',                     # a class, not a drug
    'geamycin',                       # misspelling of gentamicin
    'trimotheprim',                   # misspelling of trimethoprim
    'ampicillin-sulbactam',           # → ampicillin/sulbactam
    'ampicillin_clavulanic_acid',     # → amoxicillin/clavulanic acid
    'piperacillin-tazobactam',        # → piperacillin/tazobactam
    'trimethoprim-sulfamethoxazole',  # → trimethoprim/sulfamethoxazole
    'sulfamethoxazole/trimethoprim',  # → trimethoprim/sulfamethoxazole
    'co_trimoxazole',                 # → trimethoprim/sulfamethoxazole
}

_vocab_cache = {}


def model_vocabulary():
    """Vocabulary of the trained models, cached for the process lifetime.

    Falls back to the static lists when the backend is unreachable or the
    models are untrained, so the forms still render.
    """
    if 'data' not in _vocab_cache:
        data, status = backend_get('vocabulary/')
        _vocab_cache['data'] = data if status == 200 else {}
    return _vocab_cache['data'] or {}


@app.route('/api/antibiotics')
def antibiotics_api():
    """Antibiotics for a dropdown.

    ?model=lgbm | kmer returns only the names that model was trained on —
    picking anything else silently degrades the prediction to a population
    average, so those names are never offered in the first place.
    """
    model = request.args.get('model', '')
    vocab = model_vocabulary()
    names = (vocab.get(model) or {}).get('antibiotics') if model else None
    if names:
        return jsonify([n for n in names if n not in VOCAB_EXCLUDE])
    return jsonify(ANTIBIOTICS)


@app.route('/api/vocabulary')
def vocabulary_api():
    vocab = model_vocabulary()
    if not vocab:
        return jsonify({'lgbm': None, 'kmer': None})
    return jsonify(vocab)


@app.route('/api/organisms')
def organisms_api():
    return jsonify(BACTERIA_LIST)


@app.route('/reload', methods=['POST'])
def reload_models():
    _vocab_cache.pop('data', None)
    data, status = backend_post('reload/')
    return jsonify(data), status


@app.route('/datasets')
def datasets():
    return render_template('datasets.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/library')
def library():
    """Documentation for the amrpredict Python package."""
    return render_template('library.html', lib_version=LIB_VERSION)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # debug=True locally (no PORT set); False in production (Railway sets PORT)
    debug = not bool(os.environ.get('PORT'))
    app.run(debug=debug, port=port, host='0.0.0.0')
