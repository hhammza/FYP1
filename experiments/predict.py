"""Load a saved experiment model and predict with it.

    python experiments/predict.py A2_oof_grouped --antibiotic ciprofloxacin \
        --taxon-id 1005394 --genus Escherichia --species coli --mic 8 --mic-sign '>'

    from experiments.predict import load
    model = load('A2_oof_grouped')
    model.predict({'antibiotic': 'ciprofloxacin', 'mic_value': 8})

A saved booster is not a usable model on its own: three of its features are
resistance rates looked up per antibiotic / taxon / genus, and those lookups
must come from the same training rows the model saw. `model/rate_tables.joblib`
and `model/feature_meta.json` carry them, so this loader reconstructs exactly
the feature vector the run was trained on.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, 'results')


class SavedModel:
    def __init__(self, run_id):
        import joblib

        self.run_id = run_id
        model_dir = os.path.join(RESULTS_DIR, run_id, 'model')
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f'no saved run {run_id!r} in experiments/results/')

        with open(os.path.join(model_dir, 'feature_meta.json')) as fh:
            self.meta = json.load(fh)

        bundle = joblib.load(os.path.join(model_dir, 'rate_tables.joblib'))
        self.global_mean = bundle['global_mean']
        self.tables = bundle['tables']

        if self.meta['model_type'] == 'lightgbm':
            import lightgbm as lgb
            self.booster = lgb.Booster(model_file=os.path.join(model_dir, 'model.txt'))
            self._predict = lambda X: self.booster.predict(X)
        else:
            pipe = joblib.load(os.path.join(model_dir, 'model.joblib'))
            self._predict = lambda X: pipe.predict_proba(X)[:, 1]

    # ── Feature construction ────────────────────────────────────────────
    def _lookup(self, table_name, key, fallback):
        table = self.tables.get(table_name)
        if not table:
            return fallback
        return table.get(key, fallback)

    def build_row(self, inputs):
        """One input dict → the feature row this model expects."""
        antibiotic = str(inputs.get('antibiotic', '')).strip().lower()
        taxon_id = inputs.get('taxon_id')
        genus = inputs.get('genus') or 'unknown'
        species = inputs.get('species') or 'unknown'
        mic = inputs.get('mic_value')
        mic = float(mic) if mic not in (None, '') else np.nan

        ab_rate = self._lookup('ab_resistance_rate', (antibiotic,), self.global_mean)
        taxon_rate = ab_rate
        if taxon_id not in (None, ''):
            taxon_rate = self._lookup('taxon_ab_resistance_rate',
                                      (int(taxon_id), antibiotic), ab_rate)
        genus_rate = ab_rate
        if genus and genus != 'unknown':
            genus_rate = self._lookup('genus_ab_resistance_rate',
                                      (str(genus).capitalize(), antibiotic), ab_rate)

        row = {
            'Taxon ID': int(taxon_id) if taxon_id not in (None, '') else 0,
            'Antibiotic': antibiotic,
            'drug_class': inputs.get('drug_class', 'other'),
            'genus': genus,
            'species': species,
            'mic_sign': inputs.get('mic_sign') or 'unknown',
            'is_lab_confirmed': int(inputs.get('is_lab_confirmed', 0)),
            'computational_f1': float(inputs.get('computational_f1', 0.91)),
            'mic_value': mic,
            'mic_log': np.log1p(max(mic, 0)) if not np.isnan(mic) else np.nan,
            'has_mic': 0 if np.isnan(mic) else 1,
            'ab_resistance_rate': ab_rate,
            'taxon_ab_resistance_rate': taxon_rate,
            'genus_ab_resistance_rate': genus_rate,
        }
        if row['drug_class'] == 'other':
            from lib.data_prep import DRUG_CLASS_MAP
            row['drug_class'] = DRUG_CLASS_MAP.get(antibiotic, 'other')
        return row

    def predict(self, inputs):
        """inputs: one dict or a list of dicts."""
        records = [inputs] if isinstance(inputs, dict) else list(inputs)
        df = pd.DataFrame([self.build_row(r) for r in records])

        # Same category levels as training, so a string means the same code.
        for col, levels in self.meta['category_levels'].items():
            df[col] = pd.Categorical(df[col].astype(str), categories=levels)

        missing = [f for f in self.meta['features'] if f not in df.columns]
        if missing:
            raise ValueError(f'cannot build features: {missing}')

        probs = np.asarray(self._predict(df[self.meta['features']]))
        threshold = self.meta['threshold']
        out = [{
            'probability': round(float(p), 4),
            'prediction': 'Resistant' if p >= threshold else 'Susceptible',
            'threshold': threshold,
            'model': self.run_id,
        } for p in probs]
        return out[0] if isinstance(inputs, dict) else out

    def __repr__(self):
        t = self.meta['trained_on']
        return (f'<SavedModel {self.run_id} - {self.meta["model_type"]}, '
                f'{len(self.meta["features"])} features, '
                f'{t["rows"]:,} training rows, threshold {self.meta["threshold"]:.2f}>')


def load(run_id):
    return SavedModel(run_id)


def list_saved():
    rows = []
    for run_id in sorted(os.listdir(RESULTS_DIR)):
        meta = os.path.join(RESULTS_DIR, run_id, 'model', 'feature_meta.json')
        if os.path.exists(meta):
            with open(meta) as fh:
                m = json.load(fh)
            rows.append((run_id, m['model_type'], len(m['features']),
                         m['trained_on']['rows'], m['threshold']))
    return rows


def main():
    ap = argparse.ArgumentParser(description='Predict with a saved experiment model')
    ap.add_argument('run_id', nargs='?', help='a folder name under experiments/results/')
    ap.add_argument('--list', action='store_true', help='list loadable saved models')
    ap.add_argument('--antibiotic')
    ap.add_argument('--taxon-id', type=int)
    ap.add_argument('--genus')
    ap.add_argument('--species')
    ap.add_argument('--mic', type=float)
    ap.add_argument('--mic-sign')
    args = ap.parse_args()

    if args.list or not args.run_id:
        print(f'{"run":26s}{"type":12s}{"features":>9}{"train rows":>12}{"thr":>7}')
        for r in list_saved():
            print(f'{r[0]:26s}{r[1]:12s}{r[2]:>9}{r[3]:>12,}{r[4]:>7.2f}')
        return

    model = load(args.run_id)
    print(model)
    if not args.antibiotic:
        return
    print(model.predict({
        'antibiotic': args.antibiotic, 'taxon_id': args.taxon_id,
        'genus': args.genus, 'species': args.species,
        'mic_value': args.mic, 'mic_sign': args.mic_sign,
    }))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, HERE)
    main()
