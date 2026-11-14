"""Copy the served genome, timeline ML and RL models into the amrpredict package.

    python experiments/sync_library.py            # copy
    python experiments/sync_library.py --check    # only report what differs

promote.py --library copies the forecaster; this script copies the rest of
what amrpredict bundles since 0.3.0, from backend/trained_models/ into
amrpredict-lib/src/amrpredict/models/. Run it after promoting a genome model
(promote.py --genome), the timeline ML model or the RL agent, then bump the
library's version. backend/tests/test_library_parity.py fails while the two
differ.
"""
import argparse
import filecmp
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVED = os.path.join(ROOT, 'backend', 'trained_models')
LIBRARY = os.path.join(ROOT, 'amrpredict-lib', 'src', 'amrpredict', 'models')

# Only what the library reads: the split lists stay with the web app
FILES = {
    'genome': ['model.txt', 'feature_meta.json', 'genome_metrics.json'],
    'genome_genes': ['model.txt', 'feature_meta.json', 'genome_metrics.json', 'species_profiles.npz'],
    'timeline_ml': ['model.txt', 'timeline_ml.json', 'timeline_metrics.json'],
    'rl_agent': ['policy.npz', 'rl_agent.json'],
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='report differences, copy nothing')
    args = ap.parse_args()
    stale = []
    for folder, names in FILES.items():
        for name in names:
            src, dst = os.path.join(SERVED, folder, name), os.path.join(LIBRARY, folder, name)
            if not os.path.exists(src):
                print(f'[sync] missing in the backend: {folder}/{name}')
                continue
            if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
                continue
            stale.append(f'{folder}/{name}')
            if not args.check:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
    verb = 'differ' if args.check else 'copied'
    print(f'[sync] {len(stale)} file(s) {verb}' + (': ' + ', '.join(stale) if stale else ''))
    return 1 if args.check and stale else 0


if __name__ == '__main__':
    sys.exit(main())
