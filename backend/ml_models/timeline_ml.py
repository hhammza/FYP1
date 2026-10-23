"""The timeline ML model for /api/timeline/: observed yearly resistance and a forecast.

Trained by experiments/timeline_ml/timeline_model.py on the BV-BRC laboratory
results with a collection year (yearly resistant share per genus and
antibiotic). Its response block is `ml_forecast` (progress/formats/README.md
section 8), sent beside the simulation, which stays as the what-if tool.

The organism comes from the request's `genus`, or else from the uploaded
genome's 6-mer profile (the gene model's species reference,
trained_models/genome_genes/species_profiles.npz). No forecast when the genus
and antibiotic have fewer than two years of history, or the genome matches no
species.

Artifacts, in trained_models/timeline_ml/:
    model.txt               LightGBM booster (predicts the change from the last value)
    timeline_ml.json        features, categories, interval width, every series' history
    timeline_metrics.json   held-out errors against the baselines, ECDC check
"""
import json
import os

import numpy as np
import pandas as pd

from ml_models.common import load_metrics, normalize_antibiotic

FOLDER = 'timeline_ml'
YEARS_AHEAD = 5


def history_features(years, pcts, ns, t):
    """Features for predicting year t from the points before t; the same as
    experiments/timeline_ml/timeline_model.py (a test checks they agree)."""
    past = [(y, p, n) for y, p, n in zip(years, pcts, ns) if y < t]
    if len(past) < 1:
        return None
    py = np.array([p[0] for p in past], float)
    pp = np.array([p[1] for p in past], float)
    last3y, last3p = py[-3:], pp[-3:]
    slope = float(np.polyfit(last3y, last3p, 1)[0]) if len(last3y) >= 2 else 0.0
    lag = lambda k: float(pp[-k]) if len(pp) >= k else np.nan
    return {
        'lag1': lag(1), 'lag2': lag(2), 'lag3': lag(3),
        'gap1': float(t - py[-1]),
        'slope3': slope,
        'mean_past': float(pp.mean()),
        'n_past': float(len(pp)),
        'log_n1': float(np.log1p(past[-1][2])),
    }


class TimelineMLForecaster:
    def __init__(self, model_dir):
        self.dir = os.path.join(model_dir, FOLDER)
        self.model_dir = model_dir
        self.model = None
        self.meta = {}
        self.metrics = load_metrics(os.path.join(self.dir, 'timeline_metrics.json'))
        self.species = None
        path = os.path.join(self.dir, 'model.txt')
        if os.path.exists(path):
            import lightgbm as lgb
            self.model = lgb.Booster(model_file=path)
            with open(os.path.join(self.dir, 'timeline_ml.json'), encoding='utf-8') as fh:
                self.meta = json.load(fh)
            # genus names as the series spell them, looked up case-insensitively
            self.genera = {g.lower(): g for g in self.meta['history']}

    @property
    def is_trained(self):
        return self.model is not None

    def _series(self, genus, antibiotic):
        g = self.genera.get(str(genus or '').strip().lower())
        if not g:
            return None, None
        ab = normalize_antibiotic(antibiotic)
        s = self.meta['history'][g].get(ab)
        return (g, ab, s) if s else (g, ab, None)

    def forecast(self, genus, antibiotic, years_ahead=YEARS_AHEAD):
        """The `ml_forecast` block, or None when there is not enough history."""
        if not self.is_trained:
            return None
        found = self._series(genus, antibiotic)
        if len(found) < 3 or found[2] is None:
            return None
        g, ab, s = found
        points = s['points']
        if len(points) < self.meta.get('min_history', 2):
            return None
        ys = [p['year'] for p in points]
        ps = [p['resistant_pct'] for p in points]
        ns = [p['n'] for p in points]
        cats = self.meta['categories']
        q80 = self.meta.get('q80_abs_error_pp', 0.0)
        out = []
        for h in range(1, years_ahead + 1):
            t = ys[-1] + 1
            f = history_features(ys, ps, ns, t)
            X = pd.DataFrame([{**f, 'genus': g, 'Antibiotic': ab, 'drug_class': s['drug_class']}])
            for c in self.meta['categorical']:
                X[c] = pd.Categorical(X[c], categories=cats[c])
            p = float(np.clip(X['lag1'].iloc[0] + self.model.predict(X[self.meta['features']])[0], 0, 100))
            band = q80 * np.sqrt(h)
            out.append({'year': t, 'resistant_pct': round(p, 1),
                        'lo': round(max(0.0, p - band), 1), 'hi': round(min(100.0, p + band), 1)})
            ys.append(t); ps.append(p); ns.append(ns[-1])
        m = self.metrics or {}
        mae = m.get('test_mae_pp', {})
        return {
            'model_run': self.meta.get('run_id'),
            'organism': g,
            'antibiotic': ab,
            'history': [{'year': p['year'], 'resistant_pct': round(p['resistant_pct'], 1), 'n': p['n']}
                        for p in points],
            'forecast': out,
            'metrics': {k.replace(' ', '_'): {'mae_pct': round(v[0], 2), 'ci': [round(v[1][0], 2), round(v[1][1], 2)]}
                        for k, v in mae.items()},
            'label': self.meta.get('label', 'ML model trained on BV-BRC laboratory results'),
        }

    def genus_of(self, fasta_text):
        """Genus of an uploaded genome from its 6-mer profile, or None."""
        if self.species is None:
            from ml_models.genome_predictor import GENE_FOLDER, SpeciesProfiles
            path = os.path.join(self.model_dir, GENE_FOLDER, 'species_profiles.npz')
            self.species = SpeciesProfiles(path) if os.path.exists(path) else False
        if not self.species:
            return None
        from ml_models.genome_predictor import genome_counts
        counts, _, length = genome_counts(fasta_text)
        if length < 100_000:          # too short to tell the species reliably
            return None
        found = self.species.identify(counts)
        return found['genus'] if found and found.get('genus') else None

    def for_request(self, fasta_text, antibiotic, genus=None):
        """The block for /api/timeline/: the given genus, else the genome's. Never
        raises, so the simulation's answer is never lost to this extra."""
        try:
            genus = genus or self.genus_of(fasta_text)
            return self.forecast(genus, antibiotic) if genus else None
        except Exception as e:      # noqa: BLE001
            print(f'[TimelineML] forecast skipped: {e}')
            return None


_forecaster = {}


def get_forecaster(model_dir):
    """One forecaster per model folder, loaded on first use."""
    if model_dir not in _forecaster:
        _forecaster[model_dir] = TimelineMLForecaster(model_dir)
    return _forecaster[model_dir]
