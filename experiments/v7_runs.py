"""Run the experiments again on cleaning v7 (the complete BV-BRC export), and
watch them live.

Each config configs/<id>_v7.json is a copy of a v5 config with its own id and
"source": "amr_full", so the v5 results are never overwritten and every v7
run sits next to its v5 twin in results/registry.csv.

Run from the project root:
    .venv/bin/python experiments/v7_runs.py make      # v7 copies of every tabular config
    nohup .venv/bin/python -u experiments/v7_runs.py run >> experiments/results/logs/run_v7.log 2>&1 &
    .venv/bin/python experiments/v7_runs.py watch     # live status, Ctrl+C closes the view only

`run` skips experiments that already have results, so run it again after a
stop to carry on. It keeps the Mac awake while it works.
"""
import csv
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = os.path.join(HERE, 'configs')
RESULTS = os.path.join(HERE, 'results')
REGISTRY = os.path.join(RESULTS, 'registry.csv')
LOG = os.path.join(RESULTS, 'logs', 'run_v7.log')
PY = sys.executable

# Most useful first; any other *_v7 config runs after these, alphabetically.
ORDER = ['A2_oof_grouped', 'A6_lab_only', 'A6b_lab_only_no_mic', 'A_ablation_drug_only',
         'A12_species_holdout', 'A10_monotonic_mic', 'D3_forecaster_deploy', 'A1_oof_random',
         'A0_baseline_leaky', 'A_ablation_no_mic']
# Tabular configs worth a v7 copy; the genome (B) runs use their own genome set.
TABULAR = ('A', 'D3', 'LC')


def queue():
    ids = [os.path.basename(f)[:-len('_v7.json')] for f in glob.glob(os.path.join(CONFIGS, '*_v7.json'))]
    return [i for i in ORDER if i in ids] + sorted(i for i in ids if i not in ORDER)


def make():
    made = 0
    for f in sorted(glob.glob(os.path.join(CONFIGS, '*.json'))):
        base = os.path.basename(f)[:-5]
        if base.endswith('_v7') or not base.startswith(TABULAR):
            continue
        out = os.path.join(CONFIGS, f'{base}_v7.json')
        if os.path.exists(out):
            continue
        cfg = json.load(open(f))
        cfg['id'] = f'{base}_v7'
        cfg['description'] = (f'{base} on cleaning v7 (the complete BV-BRC export); '
                              f'compare with the v5 run {base}')
        cfg.setdefault('data', {})['source'] = 'amr_full'
        with open(out, 'w') as fh:
            json.dump(cfg, fh, indent=2)
            fh.write('\n')
        made += 1
        print(f'made configs/{base}_v7.json')
    print(f'{made} new v7 configs; {len(queue())} in the queue')


def registry():
    rows = {}
    if os.path.exists(REGISTRY):
        with open(REGISTRY, newline='') as fh:
            for r in csv.DictReader(fh):
                rows[r['id']] = r          # the last row of an id wins
    return rows


def finished(run_id):
    return os.path.exists(os.path.join(RESULTS, run_id, 'metrics.json'))


def running_ids():
    out = subprocess.run(['pgrep', '-fl', 'run.py'], capture_output=True, text=True).stdout
    return {os.path.basename(tok)[:-5] for line in out.splitlines()
            for tok in line.split() if tok.endswith('_v7.json')}


def run():
    if running_ids():
        sys.exit(f'Already running: {", ".join(running_ids())}. Use "watch" instead.')
    if sys.platform == 'darwin':
        subprocess.Popen(['caffeinate', '-i', '-s', '-w', str(os.getpid())])
    for base in queue():
        run_id = f'{base}_v7'
        if finished(run_id):
            print(f'===== {run_id} already done, skipped', flush=True)
            continue
        print(f'===== {run_id} {datetime.now():%H:%M:%S}', flush=True)
        code = subprocess.call([PY, '-u', 'run.py', f'configs/{run_id}.json'], cwd=HERE)
        if code:
            print(f'FAILED {run_id} (exit {code})', flush=True)
    print(f'===== all done {datetime.now():%H:%M:%S}', flush=True)


def started_at(log_lines):
    """Start time of each run, from the '===== <id> HH:MM:SS' markers."""
    out = {}
    for line in log_lines:
        parts = line.split()
        if len(parts) == 3 and parts[0] == '=====' and parts[1].endswith('_v7'):
            out[parts[1]] = parts[2]
    return out


def auc(row, key='auc_roc'):
    try:
        return f'{float(row[key]):.4f}'
    except (KeyError, TypeError, ValueError):
        return '-'


def watch(every=10):
    try:
        while True:
            reg = registry()
            lines = open(LOG, errors='ignore').read().splitlines() if os.path.exists(LOG) else []
            starts = started_at(lines)
            live = running_ids()
            q = queue()
            done = sum(finished(f'{b}_v7') for b in q)
            out = [f'Experiments on cleaning v7   {datetime.now():%H:%M:%S}   '
                   f'{done} of {len(q)} done   (Ctrl+C closes this view only)', '',
                   f'{"Experiment":28s} {"Status":22s} {"v7 AUC":>8s} {"95% CI":>17s} '
                   f'{"v5 AUC":>8s} {"v7 lab AUC":>10s}', '-' * 98]
            for base in q:
                rid = f'{base}_v7'
                r7, r5 = reg.get(rid, {}), reg.get(base, {})
                if finished(rid):
                    status = 'done'
                elif rid in live:
                    t0 = starts.get(rid)
                    mins = ''
                    if t0:
                        start = datetime.combine(datetime.now().date(),
                                                 datetime.strptime(t0, '%H:%M:%S').time())
                        mins = f' {max((datetime.now() - start).seconds // 60, 0)} min'
                    status = 'RUNNING' + mins
                elif any(l.startswith(f'FAILED {rid}') for l in lines):
                    status = 'FAILED (see log)'
                else:
                    status = 'waiting'
                ci = (f'[{auc(r7, "auc_ci_low")}-{auc(r7, "auc_ci_high")}]'
                      if r7.get('auc_ci_low') else '')
                out.append(f'{base:28s} {status:22s} {auc(r7):>8s} {ci:>17s} '
                           f'{auc(r5):>8s} {auc(r7, "auc_roc_lab"):>10s}')
            ps = subprocess.run(['ps', '-axo', 'pcpu,rss,command'], capture_output=True, text=True).stdout
            procs = [l.split(None, 2) for l in ps.splitlines() if 'run.py' in l and 'grep' not in l]
            if procs:
                cpu = sum(float(p[0]) for p in procs)
                mem = sum(int(p[1]) for p in procs) / 1e6
                out += ['', f'Working: yes   CPU {cpu:.0f}%   memory {mem:.1f} GB']
            else:
                out += ['', 'Working: no' + ('' if done == len(q) else
                                               '   (start or resume with the "run" command)')]
            out += ['', 'Last log lines:'] + ['  ' + l[:110] for l in lines[-5:]]
            print('\033[2J\033[H' + '\n'.join(out), flush=True)
            time.sleep(every)
    except KeyboardInterrupt:
        print()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'watch'
    {'make': make, 'run': run, 'watch': watch}.get(cmd, lambda: sys.exit(__doc__))()
