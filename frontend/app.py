"""
Flask Frontend for AMR Prediction System
Serves HTML pages and proxies requests to Django backend (port 8000)
"""
import os
import json
import time
import requests
from flask import (Flask, Response, render_template, request, jsonify, redirect, url_for,
                   has_request_context)

app = Flask(__name__)
# No sessions or flash messages are used, so no secret key is needed; one is
# set only if given, never from a default committed here.
if os.environ.get('SECRET_KEY'):
    app.secret_key = os.environ['SECRET_KEY']

# Refuse bodies bigger than a 20 MB FASTA plus form fields before reading
# them. The backend checks the same limit (settings.MAX_FASTA_BYTES).
MAX_FASTA_MB = 20
app.config['MAX_CONTENT_LENGTH'] = (MAX_FASTA_MB + 1) * 1024 * 1024

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8000/api')

# Version of the companion `amrpredict` package documented on /library.
# Keep in step with amrpredict-lib/pyproject.toml.
LIB_VERSION = os.environ.get('LIB_VERSION', '0.1.0')

# Generated from backend/amr_constants.py (the frontend deploys without
# backend/); regenerate with `python backend/amr_constants.py`.
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'antibiotic_names.json'),
          encoding='utf-8') as _fh:
    _NAMES = json.load(_fh)
ANTIBIOTICS = _NAMES['antibiotics']
ANTIBIOTIC_ALIASES = _NAMES['aliases']

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


def _forward_headers(extra=None):
    """Headers for a backend call: the browser's IP, so the backend's rate
    limit counts each visitor rather than this server, plus any extras."""
    headers = dict(extra or {})
    if has_request_context():
        headers['X-Forwarded-For'] = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    return headers


def backend_get(endpoint, timeout=10):
    try:
        r = requests.get(f'{BACKEND_URL}/{endpoint}', headers=_forward_headers(), timeout=timeout)
        return _parse_response(r)
    except requests.exceptions.ConnectionError:
        return {'error': 'Django backend not running. Start it with: python manage.py runserver'}, 503
    except Exception as e:
        return {'error': str(e)}, 500


def backend_post(endpoint, data=None, files=None, json_data=None, timeout=30, headers=None):
    try:
        url = f'{BACKEND_URL}/{endpoint}'
        headers = _forward_headers(headers)
        if files:
            r = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
        elif json_data is not None:
            r = requests.post(url, json=json_data, headers=headers, timeout=timeout)
        else:
            r = requests.post(url, data=data, headers=headers, timeout=timeout)
        return _parse_response(r)
    except requests.exceptions.ConnectionError:
        return {'error': 'Django backend not running. Start it with: python manage.py runserver'}, 503
    except Exception as e:
        return {'error': str(e)}, 500


HEALTH_TTL = 60        # seconds, for a good answer
HEALTH_RETRY_TTL = 5   # seconds, for a failed one
_health_cache = {'at': 0.0, 'data': None}


def model_health():
    """The backend's /api/health/ response, cached for HEALTH_TTL seconds.

    Every page shows model numbers (the footer at least), so this keeps page
    loads from each waiting on the backend. A failed call is kept only briefly:
    the forms start their threshold sliders from this, and a backend that is
    still starting up should not leave them on the fallback value for a minute.
    """
    now = time.monotonic()
    ttl = HEALTH_TTL if _health_cache['data'] else HEALTH_RETRY_TTL
    if _health_cache['data'] is None or now - _health_cache['at'] > ttl:
        data, status = backend_get('health/', timeout=3)
        _health_cache['data'] = data if status == 200 else {}
        _health_cache['at'] = now
    return _health_cache['data']


def _pct(x):
    return f'{x * 100:.1f}%' if isinstance(x, (int, float)) else 'not measured'


def _compact(n):
    """1217307 → '1.2M', 6002 → '6.0K', for tiles too narrow for the full count."""
    if not n:
        return 'n/a'
    for size, unit in ((1_000_000, 'M'), (1_000, 'K')):
        if n >= size:
            return f'{n / size:.1f}{unit}'
    return str(n)


def summarize_metrics(status):
    """Display strings for one model, from the metrics.json that /api/health/
    passes through (format: progress/formats/README.md).

    Nothing here is typed in by hand: when the file is missing every value
    reads "not measured" instead of falling back to an old figure.
    """
    status = status or {}
    m = status.get('metrics') or {}
    test = m.get('test') or {}
    data = m.get('data') or {}
    auc = test.get('auc_roc')
    ci = test.get('auc_roc_ci') or []
    threshold = status.get('default_threshold', m.get('threshold'))
    out = {
        'measured': isinstance(auc, (int, float)),
        'auc': 'not measured',
        'auc_ci': 'not measured',
        'recall': _pct(test.get('recall')),
        'very_major_error': _pct(test.get('very_major_error')),
        'major_error': _pct(test.get('major_error')),
        'threshold': threshold,
        'threshold_rule': m.get('threshold_rule') or '',
        'run_id': m.get('run_id') or status.get('run_id') or '',
        'algorithm': m.get('algorithm') or '',
        'split': (m.get('evaluation') or {}).get('split') or '',
        'train_rows': f"{data['train_rows']:,}" if data.get('train_rows') else 'not measured',
        'train_rows_short': _compact(data.get('train_rows')),
        'train_genomes': f"{data['train_genomes']:,}" if data.get('train_genomes') else 'not measured',
        'antibiotics': data.get('antibiotics') or 'n/a',
    }
    if out['measured']:
        out['auc'] = f'{auc:.3f}'
        out['auc_ci'] = (f'{auc:.3f} [{ci[0]:.3f}–{ci[1]:.3f}]' if len(ci) == 2
                         else out['auc'])
    return out


@app.context_processor
def inject_model_numbers():
    """`metrics.lgbm` and `metrics.kmer` in every template."""
    models = (model_health() or {}).get('models') or {}
    return {'metrics': {
        'lgbm': summarize_metrics(models.get('lgbm_forecasting')),
        'kmer': summarize_metrics(models.get('kmer_resistance')),
    }}


TOOL_TEMPLATES = {'/predict': 'resistance_prediction.html', '/timeline': 'mutation_timeline.html',
                  '/forecast': 'resistance_forecast.html'}


@app.errorhandler(413)
def upload_too_large(_e):
    """An oversized upload returns to its page with a message, not a bare 413."""
    message = f'The file is too large: the limit is {MAX_FASTA_MB} MB.'
    template = TOOL_TEMPLATES.get(request.path)
    if template is None:
        return jsonify({'error': message}), 413
    return render_template(template, result=None, error=message, form_data={}), 413


@app.route('/')
def index():
    return render_template('index.html', health=model_health())


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
            # Empty = let the backend use the model's validated threshold.
            'threshold': request.form.get('threshold', ''),
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
    form_data = {'antibiotic': '', 'threshold': ''}

    if request.method == 'POST':
        antibiotic = request.form.get('antibiotic', '').strip()
        threshold = request.form.get('threshold', '')
        form_data = {'antibiotic': antibiotic, 'threshold': threshold}

        fasta_file = request.files.get('fasta_file')
        fasta_text = request.form.get('fasta_text', '').strip()

        if fasta_file and fasta_file.filename:
            files = {'fasta_file': (fasta_file.filename, fasta_file.stream, 'text/plain')}
            post_data = {'antibiotic': antibiotic}
            if threshold:
                post_data['threshold'] = threshold
            data, status = backend_post('predict/', data=post_data, files=files)
        elif fasta_text:
            data, status = backend_post('predict/', json_data={
                'fasta_text': fasta_text, 'antibiotic': antibiotic,
                **({'threshold': float(threshold)} if threshold else {}),
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
        data, status = backend_post('train/', json_data={'model': model_name},
                                    headers={'X-Admin-Token': request.form.get('admin_token', '')})
        if status == 200:
            result = data
        else:
            error = data.get('error', 'Training failed to start')

    return render_template('train.html', result=result, error=error)


@app.route('/favicon.ico')
def favicon():
    # Browsers ask for /favicon.ico directly, whatever the page links
    return app.send_static_file('favicon.ico')


@app.route('/api/health')
def health_proxy():
    data, status = backend_get('health/')
    return jsonify(data), status


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
        # Offer each drug once, under its canonical name; names the cleaning
        # drops (drug classes such as 'carbapenem') are not offered at all
        canonical = [ANTIBIOTIC_ALIASES.get(n, n) for n in names]
        return jsonify(list(dict.fromkeys(n for n in canonical if n)))
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
    data, status = backend_post('reload/',
                                headers={'X-Admin-Token': request.headers.get('X-Admin-Token', '')})
    if status == 200:
        _vocab_cache.pop('data', None)
        _health_cache['data'] = None
    return jsonify(data), status


@app.route('/models')
def model_report():
    """Evaluation results for every model, served by the Django API."""
    report, status = backend_get('models/')
    if status != 200 or 'error' in report:
        return render_template('models.html', report=None,
                               error=report.get('error', f'Backend returned HTTP {status}'))
    return render_template('models.html', report=report, error=None)


@app.route('/genes')
def gene_report():
    """AMRFinderPlus resistance genes, served by the Django API."""
    report, status = backend_get('genes/')
    if status != 200 or 'error' in report:
        return render_template('genes.html', report=None,
                               error=report.get('error', f'Backend returned HTTP {status}'))
    return render_template('genes.html', report=report, error=None)


@app.route('/genes/<any("matrix.csv", "info.csv"):name>')
def gene_csv(name):
    """Pass a gene CSV download through from the backend unchanged."""
    try:
        r = requests.get(f'{BACKEND_URL}/genes/{name}', timeout=60)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Backend not reachable: {e}'}), 503
    if r.status_code != 200:
        return Response(r.content, status=r.status_code, mimetype='application/json')
    return Response(r.content, mimetype='text/csv',
                    headers={'Content-Disposition': r.headers.get('Content-Disposition',
                                                                  f'attachment; filename="{name}"')})


@app.route('/api/genes/<genome_id>')
def gene_lookup_api(genome_id):
    data, status = backend_get(f'genes/{genome_id}/')
    return jsonify(data), status


@app.route('/compare')
def model_compare():
    """Deployed vs experimental models and the data each trained on."""
    report, status = backend_get('models/')
    if status != 200 or 'error' in report:
        return render_template('compare.html', report=None,
                               error=report.get('error', f'Backend returned HTTP {status}'))
    return render_template('compare.html', report=report, error=None)


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
    # debug=True locally (no PORT set); False in production (Railway sets PORT).
    # The debugger can run code, so in debug mode listen on this machine only.
    debug = not bool(os.environ.get('PORT'))
    app.run(debug=debug, port=port, host='127.0.0.1' if debug else '0.0.0.0')
