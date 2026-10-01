"""Predictor for the Track B genome models (k-mers on complete genomes).

Serves /predict once a genome model is promoted (experiments/promote.py
--genome <run_id>): api/model_registry.predict_model() picks it over the old
K-mer RandomForest. A gene model is not served until the server runs
AMRFinderPlus (is_trained stays False).

Differences from resistance_predictor.py, which serves the old model:
  * the whole genome is read; no 500 kb cut. The old model was trained on the
    first 500 kb of partial FASTAs, so its predictor keeps that cut, but these
    models were trained on complete assemblies
  * k-mers are counted inside each contig, ACGT only, exactly as
    experiments/genome/kmers.py counted them for training (a test checks the
    two agree)
  * gene features would need AMRFinderPlus run on the uploaded genome; a
    model that uses them reports `needs_amrfinder` in its status instead of
    guessing

Artifacts, in backend/trained_models/genome/:
    model.txt            LightGBM booster
    feature_meta.json    features, category levels, threshold, k
    genome_metrics.json  metrics, format in progress/formats/README.md
"""
import json
import os

import numpy as np
import pandas as pd

from ml_models.common import TRAINING_DRUG_CLASS_MAP, load_metrics, normalize_antibiotic

K_MAX = 6
BASES = 'ACGT'
_LUT = np.full(256, 4, dtype=np.uint8)
for _i, _c in enumerate(BASES):
    _LUT[ord(_c)] = _i
    _LUT[ord(_c.lower())] = _i


def contigs(fasta_text):
    """Each contig of FASTA text as bytes."""
    chunks = []
    for line in fasta_text.splitlines():
        if line.startswith('>'):
            if chunks:
                yield ''.join(chunks).encode()
            chunks = []
        else:
            chunks.append(line.strip())
    if chunks:
        yield ''.join(chunks).encode()


def count_6mers(codes):
    """6-mer counts (4096,) of one contig given as 0..4 codes (4 = not ACGT)."""
    n = len(codes) - K_MAX + 1
    if n <= 0:
        return np.zeros(4 ** K_MAX, dtype=np.int64)
    c = codes.astype(np.int64)
    csum = np.concatenate([[0], np.cumsum(codes == 4)])
    ok = (csum[K_MAX:] - csum[:-K_MAX]) == 0
    idx = np.zeros(n, dtype=np.int64)
    for j in range(K_MAX):
        idx = idx * 4 + np.minimum(c[j:j + n], 3)
    return np.bincount(idx[ok], minlength=4 ** K_MAX)


def genome_features(fasta_text, k=4):
    """(k-mer frequencies, GC fraction, ACGT length) of a whole genome."""
    counts = np.zeros(4 ** K_MAX, dtype=np.int64)
    acgt = gc = 0
    for raw in contigs(fasta_text):
        codes = _LUT[np.frombuffer(raw, dtype=np.uint8)]
        counts += count_6mers(codes)
        acgt += int((codes < 4).sum())
        gc += int(((codes == 1) | (codes == 2)).sum())
    ck = counts.reshape((4,) * K_MAX).sum(axis=tuple(range(k, K_MAX))).reshape(-1).astype(np.float64)
    total = ck.sum()
    freq = ck / total if total else ck
    return freq, (gc / acgt if acgt else float('nan')), acgt


def kmer_names(k):
    names = ['']
    for _ in range(k):
        names = [n + b for n in names for b in BASES]
    return [f'k{k}_{n}' for n in names]


class GenomeModelPredictor:
    FOLDER = 'genome'
    MIN_BP = 100_000   # a complete bacterial genome is 1-12 Mb

    def __init__(self, model_dir):
        self.dir = os.path.join(model_dir, self.FOLDER)
        self.model = None
        self.meta = {}
        self.metrics = load_metrics(os.path.join(self.dir, 'genome_metrics.json'))
        self.is_trained = False
        self._load()

    def _load(self):
        path = os.path.join(self.dir, 'model.txt')
        if not os.path.exists(path):
            print('[Genome] No promoted genome model.')
            return
        import lightgbm as lgb
        self.model = lgb.Booster(model_file=path)
        with open(os.path.join(self.dir, 'feature_meta.json'), encoding='utf-8') as fh:
            self.meta = json.load(fh)
        self.k = int(self.meta.get('kmer_k', 4))
        self.features = self.meta['features']
        self.levels = {c: {str(v).lower(): v for v in lv}
                       for c, lv in self.meta.get('category_levels', {}).items()}
        self.uses_genes = any(f.startswith('g_') or f in ('gene_class_n', 'key_determinant')
                              for f in self.features)
        self.is_trained = not self.uses_genes
        print(f"[Genome] Loaded {self.meta.get('run_id')} (k={self.k}"
              f"{', needs AMRFinderPlus' if self.uses_genes else ''}).")

    @property
    def threshold(self):
        return float(self.meta.get('threshold', 0.5))

    def features_frame(self, fasta_text, antibiotic, genus=None, species=None):
        """The model input for one genome and antibiotic, built as in training."""
        freq, gc, length = genome_features(fasta_text, self.k)
        row = dict(zip(kmer_names(self.k), freq))
        row['genome_gc'] = gc
        row['genome_length_mb'] = length / 1e6
        ab = normalize_antibiotic(antibiotic)
        row['Antibiotic'] = ab
        # The map the model was trained with, stored in its bundle
        row['drug_class'] = self.meta.get('drug_class_map', TRAINING_DRUG_CLASS_MAP).get(ab, 'other')
        row['genus'] = genus or 'unknown'
        row['species'] = species or 'unknown'
        X = pd.DataFrame([row])
        for col, lv in self.levels.items():
            if col in X:
                # A value the model never saw (e.g. an unknown antibiotic) goes in
                # as missing, as LightGBM treats it; pandas will refuse it as a
                # value outside the categories
                value = lv.get(str(X[col].iloc[0]).lower())
                X[col] = pd.Categorical([value], categories=list(lv.values()))
        return X[self.features], length

    def predict(self, fasta_text, antibiotic, threshold=None, genus=None, species=None):
        if not self.is_trained:
            return {'error': 'no genome model is served' if self.model is None else
                    'this genome model needs AMRFinderPlus, which the server does not run'}
        X, length = self.features_frame(fasta_text, antibiotic, genus, species)
        if length < self.MIN_BP:
            return {'error': f'genome too short ({length:,} bp): upload a complete assembly',
                    'sequence_length': length}
        threshold = self.threshold if threshold is None else float(threshold)
        prob = float(self.model.predict(X)[0])
        ab = normalize_antibiotic(antibiotic)
        known = ab in self.levels.get('Antibiotic', {})
        kmer_cols = [c for c in self.features if c.startswith(f'k{self.k}_')]
        freq = X[kmer_cols].iloc[0]
        top = freq.sort_values(ascending=False).head(10)
        return {
            'prediction': 'Resistant' if prob >= threshold else 'Susceptible',
            'probability': round(prob, 4),
            'confidence': round((prob if prob >= threshold else 1 - prob) * 100, 1),
            'antibiotic': ab,
            'antibiotic_known': known,
            'sequence_length': length,
            # Same fields as the old K-mer predictor, so /predict's page and
            # charts work unchanged
            'gc_content': round(float(X['genome_gc'].iloc[0]) * 100, 2) if 'genome_gc' in X else None,
            'top_kmers': [{'kmer': c.split('_', 1)[1], 'frequency': round(float(v), 5)}
                          for c, v in top.items()],
            'threshold': threshold,
            'model_used': f"LightGBM on {self.k}-mers ({self.meta.get('run_id')})",
        }

    @property
    def ab_list(self):
        """Antibiotics the model was trained on (the /predict dropdown)."""
        return sorted(self.levels.get('Antibiotic', {}).values())

    @property
    def status(self):
        return {
            'trained': self.is_trained,
            'model_type': f'LightGBM on {getattr(self, "k", 4)}-mer frequencies of the complete genome',
            'description': 'Predicts resistance from a complete genome assembly (FASTA)',
            'run_id': self.meta.get('run_id'),
            'antibiotics_known': len(self.ab_list),
            'feature_dim': len(getattr(self, 'features', [])),
            'needs_amrfinder': getattr(self, 'uses_genes', False),
            'default_threshold': self.threshold,
            'metrics': self.metrics,
        }
