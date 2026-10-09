"""Check the backend Docker image serves the gene model (GitHub Actions, docker job).

Hamza's check (his handover, 2026-10-04): in the image, /api/health/ must say
models.kmer_resistance.searches_genes = true, and one complete genome the gene
model did not train on must come back from /api/predict/ with genes_found and
species_detected.

    python scripts/ci_docker_smoke.py [--base http://127.0.0.1:8000]

Picks a test genome of the served gene model (backend/trained_models/
genome_genes/split_genomes.json.gz, format section 7), downloads its complete
assembly from BV-BRC (as experiments/genome/features/download_genomes.py does),
posts it, and prints what came back and how long it took. Standard library
only. Exits 1 on any failure.
"""
import argparse
import gzip
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT = os.path.join(ROOT, 'backend', 'trained_models', 'genome_genes', 'split_genomes.json.gz')
BVBRC = 'https://www.bv-brc.org/api'
MAX_BYTES = 18 * 1024 * 1024          # under the backend's 20 MB upload limit
# BV-BRC's Cloudflare refuses Python's default "Python-urllib" signature (error
# 1010); identify the project as download_genomes.py does
USER_AGENT = 'amr-fyp-ci-smoke/1.0 (COMSATS FYP)'


def http(url, data=None, accept='application/json', timeout=60, content_type=None):
    req = urllib.request.Request(url, data=data, headers={'Accept': accept, 'User-Agent': USER_AGENT})
    if content_type:
        req.add_header('Content-Type', content_type)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def fail(message):
    print(f'FAIL: {message}')
    sys.exit(1)


def wait_for_health(base, seconds):
    start = time.time()
    while time.time() - start < seconds:
        try:
            status, body = http(f'{base}/api/health/', timeout=10)
            if status == 200:
                return json.loads(body)
        except OSError:
            pass
        time.sleep(5)
    fail(f'/api/health/ did not answer within {seconds} s')


def test_genomes():
    with gzip.open(SPLIT, 'rt', encoding='utf-8') as fh:
        split = json.load(fh)
    # a fixed order, so every CI run tries the same genomes
    return split.get('run_id'), sorted(split['test'])


def download(genome_id):
    """The complete assembly as FASTA bytes, or None if BV-BRC's copy looks incomplete."""
    q = urllib.parse.quote(f'eq(genome_id,{genome_id})', safe='(),')
    status, meta = http(f'{BVBRC}/genome/?{q}&select(genome_id,genome_length)', timeout=60)
    rows = json.loads(meta) if status == 200 else []
    if not rows or not rows[0].get('genome_length'):
        return None
    expected = int(rows[0]['genome_length'])
    status, fasta = http(f'{BVBRC}/genome_sequence/?{q}&limit(100000)', accept='application/dna+fasta', timeout=180)
    if status != 200:
        return None
    length = sum(len(line.strip()) for line in fasta.splitlines() if not line.startswith(b'>'))
    if abs(length - expected) > 0.01 * expected or len(fasta) > MAX_BYTES:
        return None
    return fasta


def main(base, wait):
    health = wait_for_health(base, wait)
    model = health['models']['kmer_resistance']
    print(f"health: served {model.get('run_id')}, searches_genes={model.get('searches_genes')}")
    if model.get('searches_genes') is not True:
        fail('the image does not serve the gene model (searches_genes is not true): is AMRFinderPlus on PATH?')

    run_id, candidates = test_genomes()
    fasta = genome_id = None
    for gid in candidates[:15]:
        fasta = download(gid)
        if fasta:
            genome_id = gid
            break
        print(f'  {gid}: BV-BRC copy unavailable or incomplete, trying the next test genome')
    if not fasta:
        fail('could not download a complete test genome from BV-BRC')
    print(f'genome: {genome_id}, a test genome of {run_id} (never trained on), {len(fasta) / 1e6:.1f} MB')

    body = json.dumps({'fasta_text': fasta.decode('ascii', errors='ignore'), 'antibiotic': 'ciprofloxacin'}).encode()
    start = time.time()
    status, raw = http(f'{base}/api/predict/', data=body, content_type='application/json', timeout=170)
    seconds = time.time() - start
    try:
        result = json.loads(raw)
    except ValueError:
        fail(f'/api/predict/ answered {status} with non-JSON: {raw[:300]!r}')
    if status != 200:
        fail(f'/api/predict/ answered {status}: {result}')
    print(f"predict: {result.get('prediction')} (P={result.get('probability')}) in {seconds:.0f} s, "
          f"model {result.get('model_used')}")
    if result.get('warning'):
        fail(f"the gene search failed and the k-mer model answered: {result['warning']}")
    genes = result.get('genes_found')
    if not isinstance(genes, list):
        fail('no genes_found in the response')
    species = (result.get('species_detected') or {}).get('species')
    print(f'species_detected: {species}; genes_found: {len(genes)}: '
          + ', '.join(g.get('gene', '?') for g in genes[:12]) + (' ...' if len(genes) > 12 else ''))
    if seconds > 120:
        fail(f'{seconds:.0f} s is over the page\'s 120 s wait (frontend PREDICT_TIMEOUT)')
    print('OK: the image serves the gene model')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--base', default='http://127.0.0.1:8000')
    ap.add_argument('--wait', type=int, default=300, help='seconds to wait for the backend to start')
    a = ap.parse_args()
    main(a.base.rstrip('/'), a.wait)
