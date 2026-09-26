"""
K-mer Frequency based Antibiotic Resistance Predictor
Input: FASTA sequence (raw text) + antibiotic name
Output: Resistant/Susceptible + confidence
Model: RandomForest on 4-mer frequency features (fast local alternative to CNN/MLP)
"""
import os
import re
import numpy as np
import pickle
import warnings
from itertools import product
from collections import Counter

from ml_models.common import load_metrics, normalize_antibiotic

warnings.filterwarnings('ignore')

NUCLEOTIDES = ['A', 'T', 'C', 'G']
K = 4
ALL_KMERS = [''.join(p) for p in product(NUCLEOTIDES, repeat=K)]
KMER_TO_IDX = {km: i for i, km in enumerate(ALL_KMERS)}
N_KMERS = len(ALL_KMERS)

_STRIP = str.maketrans('', '', ''.join(
    c for c in map(chr, range(256)) if c not in 'ATCG'
))

ANTIBIOTIC_RESISTANCE_PROFILES = {
    'ciprofloxacin': {'gc_weight': 1.2, 'base': 0.42},
    'ampicillin': {'gc_weight': 0.9, 'base': 0.65},
    'tetracycline': {'gc_weight': 0.8, 'base': 0.58},
    'trimethoprim/sulfamethoxazole': {'gc_weight': 1.1, 'base': 0.48},
    'gentamicin': {'gc_weight': 0.7, 'base': 0.28},
    'chloramphenicol': {'gc_weight': 1.0, 'base': 0.32},
    'cefotaxime': {'gc_weight': 1.1, 'base': 0.35},
    'imipenem': {'gc_weight': 1.3, 'base': 0.18},
    'colistin': {'gc_weight': 1.5, 'base': 0.05},
    'vancomycin': {'gc_weight': 0.6, 'base': 0.10},
}


def read_fasta_sequence(fasta_text, max_bp=500_000):
    """Parse FASTA text, return clean ATCG sequence."""
    lines = fasta_text.strip().split('\n')
    seq_parts = []
    total = 0
    for line in lines:
        if line.startswith('>'):
            continue
        chunk = line.strip().upper().translate(_STRIP)
        seq_parts.append(chunk)
        total += len(chunk)
        if total >= max_bp:
            break
    return ''.join(seq_parts)[:max_bp]


def kmer_freq_vector(sequence):
    """Compute 4-mer frequency vector from DNA sequence string."""
    if len(sequence) < K + 5:
        return None
    counter = Counter(sequence[i:i+K] for i in range(len(sequence) - K + 1))
    counts = np.array([counter.get(km, 0) for km in ALL_KMERS], dtype=np.float32)
    total = counts.sum()
    if total == 0:
        return None
    return counts / total


def compute_gc_content(sequence):
    """GC content as fraction."""
    if not sequence:
        return 0.5
    gc = sum(1 for c in sequence if c in 'GC')
    return gc / len(sequence)


def extract_features(sequence, antibiotic, ab_list):
    """Extract combined feature vector: k-mer + antibiotic one-hot + GC content."""
    kmer_vec = kmer_freq_vector(sequence)
    if kmer_vec is None:
        kmer_vec = np.zeros(N_KMERS, dtype=np.float32)

    N_AB = len(ab_list)
    ab_vec = np.zeros(N_AB, dtype=np.float32)
    ab_lower = antibiotic.lower().strip()
    for i, a in enumerate(ab_list):
        if a.lower() == ab_lower:
            ab_vec[i] = 1.0
            break

    gc = compute_gc_content(sequence)
    extra = np.array([gc, 1.0 - gc, len(sequence) / 500000.0], dtype=np.float32)

    return np.concatenate([kmer_vec, ab_vec, extra])


class KmerResistancePredictor:
    METRICS_FILE = 'kmer_metrics.json'

    def __init__(self, model_dir):
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.ab_list = []
        self._ab_raw = {}
        self._ab_set = set()
        self.is_trained = False
        self.metrics = load_metrics(os.path.join(model_dir, self.METRICS_FILE))
        self._load()

    def _load(self):
        model_path = os.path.join(self.model_dir, 'kmer_resistance_model.pkl')
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    artifacts = pickle.load(f)
                self.model = artifacts['model']
                self.scaler = artifacts.get('scaler')
                self.ab_list = artifacts.get('ab_list', [])
                # Canonical name -> the spelling the model was trained on, so
                # 'rifampin' and 'rifampicin' reach the same one-hot column.
                self._ab_raw = {normalize_antibiotic(a): a for a in self.ab_list}
                self._ab_set = set(self._ab_raw)
                self.is_trained = True
                print(f"[K-mer] Model loaded. Antibiotics: {len(self.ab_list)}")
            except Exception as e:
                print(f"[K-mer] Could not load model: {e}")
        else:
            print("[K-mer] No trained model. Using heuristic predictions.")

    def _heuristic_predict(self, sequence, antibiotic):
        """Heuristic based on GC content and antibiotic profile."""
        gc = compute_gc_content(sequence)
        ab = antibiotic.lower().strip()

        profile = ANTIBIOTIC_RESISTANCE_PROFILES.get(ab, {'gc_weight': 1.0, 'base': 0.35})
        base = profile['base']
        gc_weight = profile['gc_weight']

        gc_deviation = abs(gc - 0.50)
        adjustment = gc_deviation * gc_weight * 0.3

        kmer_vec = kmer_freq_vector(sequence)
        if kmer_vec is not None:
            entropy = -np.sum(kmer_vec * np.log1p(kmer_vec))
            entropy_norm = entropy / np.log(N_KMERS + 1)
            adjustment += (entropy_norm - 0.5) * 0.15

        noise = np.random.uniform(-0.04, 0.04)
        prob = float(np.clip(base + adjustment + noise, 0.03, 0.97))
        return prob

    def predict(self, fasta_text, antibiotic, threshold=None):
        if threshold is None:
            threshold = self.default_threshold
        antibiotic = normalize_antibiotic(antibiotic)
        sequence = read_fasta_sequence(fasta_text)

        if len(sequence) < 100:
            return {
                'error': 'FASTA sequence too short (minimum 100 bp)',
                'sequence_length': len(sequence),
            }

        # Which path produced the number. Set from what actually ran, not from
        # whether the model loaded: a loaded model that fails at prediction
        # time must never be reported as the trained model.
        model_used = 'Heuristic (untrained)'
        if self.is_trained:
            try:
                feat = extract_features(sequence, self._ab_raw.get(antibiotic, antibiotic),
                                        self.ab_list)
                if self.scaler:
                    # The scaler was fitted on the k-mer block only
                    # (train_models.py), so only those columns are scaled.
                    feat[:N_KMERS] = self.scaler.transform(feat[:N_KMERS].reshape(1, -1))[0]
                prob = float(self.model.predict_proba(feat.reshape(1, -1))[0][1])
                model_used = 'RandomForest K-mer (trained)'
            except Exception as e:
                print(f"[K-mer] Prediction error: {e}")
                prob = self._heuristic_predict(sequence, antibiotic)
                model_used = 'Heuristic fallback'
        else:
            prob = self._heuristic_predict(sequence, antibiotic)

        label = 'Resistant' if prob >= threshold else 'Susceptible'
        confidence = prob if prob >= threshold else 1 - prob
        gc = compute_gc_content(sequence)
        kmer_vec = kmer_freq_vector(sequence)

        top_kmers = []
        if kmer_vec is not None:
            top_idx = np.argsort(kmer_vec)[-10:][::-1]
            top_kmers = [{'kmer': ALL_KMERS[i], 'frequency': round(float(kmer_vec[i]), 5)}
                         for i in top_idx]

        return {
            'prediction': label,
            'probability': round(prob, 4),
            'confidence': round(confidence * 100, 1),
            'antibiotic': antibiotic,
            'sequence_length': len(sequence),
            'gc_content': round(gc * 100, 2),
            'top_kmers': top_kmers,
            'model_used': model_used,
            'antibiotic_known': antibiotic in self._ab_set,
            'threshold': threshold,
        }

    @property
    def default_threshold(self):
        """The threshold the model was evaluated at, from metrics.json."""
        return float((self.metrics or {}).get('threshold', 0.5))

    @property
    def status(self):
        return {
            'trained': self.is_trained,
            'model_type': 'RandomForest on 4-mer Frequency Spectra',
            'antibiotics_known': len(self.ab_list),
            'feature_dim': N_KMERS,
            'description': 'Predicts resistance from bacterial genome FASTA using k-mer composition analysis',
            'default_threshold': self.default_threshold,
            # Measured numbers, read from metrics.json beside the artifact;
            # None when the file is missing, so the UI never shows a stale guess.
            'metrics': self.metrics,
        }
