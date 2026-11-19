"""A guided tour of the amrpredict library: every model, one call each.

    pip install amrpredict
    python demo.py              # all sections (downloads one genome, about 5 MB)
    python demo.py --no-genome  # skip the genome sections (no internet needed)

Needs only the amrpredict package and Python's standard library. The genome
is BV-BRC 108619.160 (Salmonella enterica), which is in the test set of both
genome models: no model was trained on it. Its laboratory results are printed
beside the predictions.
"""
import argparse
import os
import sys
import time
import urllib.request

import amrpredict

GENOME_ID = '108619.160'
# Laboratory results for this genome (BV-BRC, the project's cleaned table v7)
LAB = {'amoxicillin/clavulanic acid': 'Susceptible', 'ampicillin': 'Resistant', 'azithromycin': 'Susceptible',
       'cefoxitin': 'Susceptible', 'ceftiofur': 'Susceptible', 'ceftriaxone': 'Susceptible',
       'chloramphenicol': 'Resistant', 'ciprofloxacin': 'Susceptible', 'gentamicin': 'Resistant',
       'nalidixic acid': 'Susceptible', 'streptomycin': 'Resistant', 'sulfisoxazole': 'Resistant',
       'tetracycline': 'Resistant', 'trimethoprim/sulfamethoxazole': 'Resistant'}


# Some consoles (Windows' default) cannot print every character; never crash on one
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')


def plain(text):
    return str(text).replace('→', '->')


def title(text):
    print('\n' + '=' * 78 + '\n' + text + '\n' + '=' * 78)


def pause(args):
    if args.step:
        input('\n[press Enter for the next section] ')


def get_genome():
    path = f'{GENOME_ID}.fna'
    if not os.path.exists(path):
        print(f'downloading genome {GENOME_ID} from BV-BRC (about 5 MB)...')
        url = f'https://www.bv-brc.org/api/genome_sequence/?eq(genome_id,{GENOME_ID})&limit(100000)'
        req = urllib.request.Request(url, headers={'Accept': 'application/dna+fasta',
                                                   'User-Agent': 'amrpredict-demo/1.0'})
        with urllib.request.urlopen(req, timeout=180) as r, open(path, 'wb') as fh:
            fh.write(r.read())
    return open(path).read()


def main():
    ap = argparse.ArgumentParser(description='A guided tour of the amrpredict library.')
    ap.add_argument('--no-genome', action='store_true', help='skip the sections that need a genome download')
    ap.add_argument('--step', action='store_true', help='wait for Enter between sections')
    args = ap.parse_args()

    title(f'amrpredict {amrpredict.__version__}  (Python {sys.version.split()[0]})')
    print('Models bundled in the package:')
    for name, s in amrpredict.status().items():
        if isinstance(s, dict):
            kind = s.get('model_type') or s.get('description') or ''
            print(f"  {name:20s} trained={str(s.get('trained')):5s} {kind[:60]}")
    print('Antibiotics known:', {m: len(amrpredict.antibiotics(model=m)) for m in ['forecast', 'genome', 'trend', 'rl']})
    pause(args)

    title('1. Forecaster (LightGBM): will this isolate resist?   = website /forecast')
    for drug, taxon, mic, organism in [('ciprofloxacin', 562, 4, 'E. coli'), ('ciprofloxacin', 562, 0.015, 'E. coli'),
                                       ('ampicillin', 562, 32, 'E. coli'), ('meropenem', 573, 0.25, 'K. pneumoniae')]:
        r = amrpredict.forecast(drug, taxon_id=taxon, mic_value=mic)
        print(f"  {organism:14s} {drug:14s} MIC {mic:<6} -> {r['prediction']:11s} P={r['probability']:.4f}")
    print('  (E. coli + ciprofloxacin, MIC 4 gives Resistant 0.7055 on the website too)')
    pause(args)

    if not args.no_genome:
        t = time.time()
        fasta = get_genome()
        bp = sum(len(line) for line in fasta.splitlines() if not line.startswith('>'))
        title('2. Genome model: will this genome resist?   = website /predict')
        print(f'Genome {GENOME_ID}: {fasta.count(">")} contigs, {bp:,} bp ({time.time() - t:.0f} s)')
        print('Species from its 6-mer profile:', amrpredict.identify_species(fasta))
        right = 0
        for drug, truth in LAB.items():
            p = amrpredict.predict_fasta(fasta, drug)
            ok = p['prediction'] == truth
            right += ok
            print(f"  {drug:30s} lab {truth:11s} model {p['prediction']:11s} P={p['probability']:.3f} {'ok' if ok else 'MISS'}")
        print(f'  {right} of {len(LAB)} correct, model: {p["model_used"]}')
        print('  (one genome is an illustration; the measured result is lab AUC 0.935 on 4,481 unseen genomes,')
        print('   or 0.977 for the gene model where NCBI AMRFinderPlus is installed)')
        pause(args)

    title('3. Timeline ML model (LightGBM): how will resistance change?   = website /timeline')
    tr = amrpredict.forecast_trend('Streptococcus', 'penicillin', years_ahead=5)
    print('Streptococcus + penicillin, observed (last 6 years with data):')
    for h in tr['history'][-6:]:
        print(f"  {h['year']}  {h['resistant_pct']:5.1f}% resistant  ({h['n']} lab results)")
    print('Forecast:')
    for f in tr['forecast']:
        print(f"  {f['year']}  {f['resistant_pct']:5.1f}%   80% band {f['lo']}-{f['hi']}%")
    print(f"Mean error on years it never saw (2017-2022): {tr['metrics']['model']['mae_pct']} percentage points")
    pause(args)

    title('4. RL agent (PPO, trained on the simulation): which drug each week?   = website /timeline')
    plan = amrpredict.plan_treatment('ciprofloxacin', n_weeks=52)
    for p in plan['policies']:
        fw = p['failure_week'] if p['failure_week'] is not None else 'none'
        print(f"  {plain(p['label'])[:45]:45s} first failed week: {fw}")
    print('  best:', plan['best'], '| agent plan, first 8 weeks:', ', '.join(plan['policies'][0]['policy'][:8]))
    pause(args)

    if not args.no_genome:
        title('5. Biological simulation (NOT a trained model): week by week   = website /timeline')
        sim = amrpredict.simulate_timeline(fasta, 'ciprofloxacin', n_weeks=8)
        for w in sim['timeline']:
            print(f"  week {w['week']}: {w['resistant_fraction']:5.1f}% resistant, treatment effective: {w['treatment_effective']}")
        print('  model_used:', sim['model_used'], '| simulation:', sim['simulation'])

    title('Done. The same from the command line, for example:')
    print('  amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4')
    print('  amrpredict trend Streptococcus penicillin --years 5')
    print('  amrpredict plan ciprofloxacin --weeks 52')
    print('  (if Windows blocks amrpredict.exe:  python -m amrpredict.cli status)')


if __name__ == '__main__':
    main()
