"""Check the amrpredict library's gene model with the real AMRFinderPlus (CI docker job).

Runs inside the backend Docker image, which has AMRFinderPlus and its pinned
database, after the amrpredict wheel is installed there. Takes the genome and
the API's answer that scripts/ci_docker_smoke.py --save wrote, runs

    amrpredict.predict_fasta(genome, 'ciprofloxacin', use_genes=True)

and checks the library used the gene model (not the k-mer fallback) and gave
the same answer as /api/predict/: prediction, probability, model run, genes
found and species detected.

    python ci_library_genes.py DIR

Exits 1 on any difference.
"""
import json
import os
import sys
import time


def fail(message):
    print(f'FAIL: {message}')
    sys.exit(1)


def genes(result):
    return sorted((g.get('gene'), g.get('type')) for g in result.get('genes_found') or [])


def main(folder):
    import amrpredict

    with open(os.path.join(folder, 'genome.fna'), encoding='ascii', errors='ignore') as fh:
        fasta = fh.read()
    with open(os.path.join(folder, 'api.json'), encoding='utf-8') as fh:
        api = json.load(fh)

    status = amrpredict.status()['genome_resistance']
    print(f"amrpredict {amrpredict.__version__}: genome model {status.get('run_id')}, "
          f"searches_genes={status.get('searches_genes')}, amrfinder={status.get('amrfinder')}")
    if not status.get('searches_genes'):
        fail('the library did not find AMRFinderPlus in the image')

    start = time.time()
    lib = amrpredict.predict_fasta(fasta, api['antibiotic'], use_genes=True)
    seconds = time.time() - start
    if 'error' in lib:
        fail(f"the library's gene model gave an error: {lib['error']}")
    if lib.get('warning'):
        fail(f"the gene search failed and the k-mer model answered: {lib['warning']}")
    print(f"library: {lib['prediction']} (P={lib['probability']}) in {seconds:.0f} s, model {lib['model_used']}")
    print(f"library: species {lib.get('species_detected')}, {len(lib.get('genes_found') or [])} genes")

    checks = {
        'prediction': (lib.get('prediction'), api.get('prediction')),
        'probability': (lib.get('probability'), api.get('probability')),
        'model_run': (lib.get('model_run'), api.get('model_run')),
        'genes_found': (genes(lib), genes(api)),
        'species': ((lib.get('species_detected') or {}).get('species'),
                    (api.get('species_detected') or {}).get('species')),
    }
    wrong = [name for name, (a, b) in checks.items() if a != b]
    for name in wrong:
        print(f'  {name}: library {checks[name][0]!r}, API {checks[name][1]!r}')
    if wrong:
        fail('the library and the API disagree on ' + ', '.join(wrong))
    print(f"OK: the library's gene model ran AMRFinderPlus and matches /api/predict/ on genome {api.get('genome_id')}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
