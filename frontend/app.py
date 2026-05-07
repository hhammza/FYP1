"""
Flask Frontend for AMR Prediction System
Serves HTML pages and proxies requests to Django backend (port 8000)
"""
import os
import json
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = 'fyp-flask-frontend-2024'

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8000/api')

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


def backend_get(endpoint, timeout=10):
    try:
        r = requests.get(f'{BACKEND_URL}/{endpoint}', timeout=timeout)
        return r.json(), r.status_code
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
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {'error': 'Django backend not running. Start it with: python manage.py runserver'}, 503
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/')
def index():
    health_data, _ = backend_get('health/')
    return render_template('index.html', health=health_data, antibiotics=ANTIBIOTICS)


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
        antibiotics=ANTIBIOTICS,
        bacteria_list=BACTERIA_LIST,
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
                                   form_data=form_data, antibiotics=ANTIBIOTICS)

        if status == 200:
            result = data
        else:
            error = data.get('error', 'Prediction failed')

    return render_template(
        'resistance_prediction.html',
        result=result,
        error=error,
        form_data=form_data,
        antibiotics=ANTIBIOTICS,
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
                                   form_data=form_data, antibiotics=ANTIBIOTICS)

        if status == 200:
            result = data
        else:
            error = data.get('error', 'Prediction failed')

    return render_template(
        'mutation_timeline.html',
        result=result,
        error=error,
        form_data=form_data,
        antibiotics=ANTIBIOTICS,
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


@app.route('/reload', methods=['POST'])
def reload_models():
    data, status = backend_post('reload/')
    return jsonify(data), status


@app.route('/datasets')
def datasets():
    return render_template('datasets.html', antibiotics=ANTIBIOTICS, bacteria_list=BACTERIA_LIST)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
