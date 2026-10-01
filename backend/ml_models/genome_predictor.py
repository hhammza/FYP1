"""Predictor for the Track B genome models (complete genomes).

Serves /predict once a genome model is promoted (experiments/promote.py
--genome <run_id>): api/model_registry.predict_model() picks it over the old
K-mer RandomForest. Two kinds of model can be promoted, each to its own folder:

    genome/        k-mer model: LightGBM on k-mer frequencies. Needs nothing
                   beyond Python.
    genome_genes/  gene model: LightGBM on the resistance genes and mutations
                   AMRFinderPlus finds in the upload (lab AUC 0.977 against
                   0.935 for k-mers). Needs the `amrfinder` program and its
                   database on the server.

GenomeModelPredictor(model_dir) serves the gene model when it is promoted and
AMRFinderPlus can run here, and the k-mer model otherwise, so a server without
AMRFinderPlus (a Windows laptop) keeps working unchanged. If AMRFinderPlus fails
on one upload, that request is answered by the k-mer model, with a warning.

How the gene model builds its input, matching training exactly:
  1. species: the upload's 6-mer profile against the mean profile of each of
     the 99 species in the training genomes (species_profiles.npz); right
     species for 98.0% and right genus for 99.8% of held-out genomes
  2. AMRFinderPlus with --organism for that species (or genus) when it is on
     AMRFinderPlus's list, as experiments/genome/features/run_amrfinder.py ran
     it for training; without it no point mutations are reported
  3. hits with Scope = core and Type = AMR (build_gene_matrix.py), turned
     into the 0/1 gene columns and the drug-aware counts of
     experiments/genome/genes.py (rules stored in feature_meta.json)

Also, as in training: k-mers are counted inside each contig, ACGT only, exactly
as experiments/genome/kmers.py counted them (a test checks the two agree); the
whole genome is read (no 500 kb cut).

Artifacts (each folder):
    model.txt             LightGBM booster
    feature_meta.json     features, category levels, threshold, k, gene rules
    genome_metrics.json   metrics, format in progress/formats/README.md
    species_profiles.npz  gene model only: species reference profiles

Environment (gene model):
    AMRFINDER_PATH        the amrfinder binary, if it is not on PATH or in a
                          conda env called `amrfinder`
    AMRFINDER_THREADS     threads per run (default 4)
    AMRFINDER_TIMEOUT     seconds before giving up (default 100, under the
                          120 s /predict waits)
    AMRFINDER_DATABASE    a database folder to use instead of the installed
                          one. Training used AMRFinderPlus 4.2.7 with database
                          2026-08-07.1 (gene_summary.md); a newer database can
                          rename or add genes the model never saw
"""
import json
import os
import shutil
import subprocess
import tempfile

import numpy as np
import pandas as pd

from ml_models.common import TRAINING_DRUG_CLASS_MAP, load_metrics, normalize_antibiotic

K_MAX = 6
BASES = 'ACGT'
_LUT = np.full(256, 4, dtype=np.uint8)
for _i, _c in enumerate(BASES):
    _LUT[ord(_c)] = _i
    _LUT[ord(_c.lower())] = _i

KMER_FOLDER = 'genome'
GENE_FOLDER = 'genome_genes'
# Above this cosine distance to every species profile the species is called
# unknown (within a species 99% of genomes are under 0.003; between species
# the distance is at least 0.0068)
SPECIES_MAX_DISTANCE = 0.01
# Genera AMRFinderPlus covers as one organism (run_amrfinder.py GENUS_ALIASES)
GENUS_ALIASES = {'Shigella': 'Escherichia'}


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


def genome_counts(fasta_text):
    """(6-mer counts, GC fraction, ACGT length) of a whole genome."""
    counts = np.zeros(4 ** K_MAX, dtype=np.int64)
    acgt = gc = 0
    for raw in contigs(fasta_text):
        codes = _LUT[np.frombuffer(raw, dtype=np.uint8)]
        counts += count_6mers(codes)
        acgt += int((codes < 4).sum())
        gc += int(((codes == 1) | (codes == 2)).sum())
    return counts, (gc / acgt if acgt else float('nan')), acgt


def kmer_frequencies(counts6, k=4):
    ck = counts6.reshape((4,) * K_MAX).sum(axis=tuple(range(k, K_MAX))).reshape(-1).astype(np.float64)
    total = ck.sum()
    return ck / total if total else ck


def genome_features(fasta_text, k=4):
    """(k-mer frequencies, GC fraction, ACGT length) of a whole genome."""
    counts, gc, length = genome_counts(fasta_text)
    return kmer_frequencies(counts, k), gc, length


def kmer_names(k):
    names = ['']
    for _ in range(k):
        names = [n + b for n in names for b in BASES]
    return [f'k{k}_{n}' for n in names]


# ── AMRFinderPlus ────────────────────────────────────────────────────────

def find_amrfinder():
    """Path of the amrfinder binary, or None."""
    home = os.path.expanduser('~')
    candidates = [os.environ.get('AMRFINDER_PATH'), shutil.which('amrfinder')] + [
        os.path.join(home, base, 'envs', 'amrfinder', 'bin', 'amrfinder')
        for base in ('anaconda3', 'miniconda3', 'miniforge3')] + [
        '/opt/anaconda3/envs/amrfinder/bin/amrfinder', '/opt/conda/envs/amrfinder/bin/amrfinder',
        '/opt/conda/bin/amrfinder']
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def amrfinder_env(amrfinder):
    """Its folder first on PATH (it calls blast and hmmer) and CONDA_PREFIX set
    to its env, which is where it looks for its database (run_amrfinder.py)."""
    env = dict(os.environ)
    env['PATH'] = os.path.dirname(amrfinder) + os.pathsep + env.get('PATH', '')
    env.setdefault('CONDA_PREFIX', os.path.dirname(os.path.dirname(amrfinder)))
    return env


_ORGANISMS = {}


def supported_organisms(amrfinder):
    """AMRFinderPlus's --organism options (asked once per binary)."""
    if amrfinder not in _ORGANISMS:
        out = subprocess.run([amrfinder, '--list_organisms'], capture_output=True, text=True,
                             env=amrfinder_env(amrfinder), timeout=60)
        line = next((l for l in (out.stdout + out.stderr).splitlines() if 'organism options' in l), '')
        _ORGANISMS[amrfinder] = {o.strip() for o in line.split(':', 1)[1].split(',')} if ':' in line else set()
    return _ORGANISMS[amrfinder]


def organism_for(species_name, genus_name, supported):
    """The --organism value for a genome, or None (run_amrfinder.py)."""
    if isinstance(species_name, str) and species_name.replace(' ', '_') in supported:
        return species_name.replace(' ', '_')
    genus = GENUS_ALIASES.get(genus_name, genus_name)
    return genus if genus in supported else None


# AMRFinderPlus 3.x column names -> 4.x (the names build_gene_matrix.py read)
_OLD_COLUMNS = {'Gene symbol': 'Element symbol', 'Sequence name': 'Element name',
                'Element type': 'Type', 'Element subtype': 'Subtype'}


def parse_amrfinder(tsv_text, point_subtypes=('POINT', 'POINT_DISRUPT')):
    """Core AMR hits of one AMRFinderPlus report: one row per symbol with
    symbol, name, class, subclass, type ('gene' or 'point_mutation')."""
    import io
    df = pd.read_csv(io.StringIO(tsv_text), sep='\t', dtype=str).rename(columns=_OLD_COLUMNS)
    df = df[(df['Scope'] == 'core') & (df['Type'] == 'AMR')].drop_duplicates('Element symbol')
    return pd.DataFrame({
        'symbol': df['Element symbol'].to_numpy(),
        'name': df['Element name'].fillna('').to_numpy() if 'Element name' in df else '',
        'class': df['Class'].fillna('').to_numpy(),
        'subclass': df['Subclass'].fillna('').to_numpy(),
        'type': np.where(df['Subtype'].isin(point_subtypes), 'point_mutation', 'gene'),
    })


def run_amrfinder(fasta_text, organism=None, amrfinder=None):
    """AMRFinderPlus on one genome: (core AMR hits, report text). Raises
    RuntimeError if it fails or times out."""
    amrfinder = amrfinder or find_amrfinder()
    if not amrfinder:
        raise RuntimeError('AMRFinderPlus is not installed on this server')
    threads = os.environ.get('AMRFINDER_THREADS', '4')
    timeout = float(os.environ.get('AMRFINDER_TIMEOUT', '100'))
    with tempfile.TemporaryDirectory() as tmp:
        fna, out = os.path.join(tmp, 'upload.fna'), os.path.join(tmp, 'hits.tsv')
        with open(fna, 'w') as fh:
            fh.write(fasta_text)
        cmd = [amrfinder, '-n', fna, '--threads', str(threads), '-o', out]
        if organism:
            cmd += ['--organism', organism]
        if os.environ.get('AMRFINDER_DATABASE'):
            cmd += ['--database', os.environ['AMRFINDER_DATABASE']]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                  env=amrfinder_env(amrfinder))
        except subprocess.TimeoutExpired:
            raise RuntimeError(f'AMRFinderPlus took longer than {timeout:.0f} s')
        if proc.returncode != 0 or not os.path.exists(out):
            last = (proc.stderr.strip().splitlines() or ['no message'])[-1]
            raise RuntimeError(f'AMRFinderPlus failed: {last}')
        with open(out) as fh:
            report = fh.read()
    return parse_amrfinder(report), report


# ── Features from the hits (experiments/genome/genes.py, for one genome) ─

def amr_classes(cls):
    return {c.strip() for c in str(cls).split('/') if c.strip()} if cls else set()


def gene_features(hits, antibiotic, drug_class, rules, features):
    """The gene columns of one (genome, antibiotic) row, as genes.attach()
    builds them: raw 0/1 `g_<symbol>` columns and the drug-aware counts."""
    symbols = set(hits['symbol'])
    row = {f: float(f[2:] in symbols) for f in features if f.startswith('g_')}
    classes = [amr_classes(c) for c in hits['class']]
    is_mut = (hits['type'] == 'point_mutation').to_numpy()
    targets = set(rules['class_to_amrfinder'].get(drug_class, []))
    covers = np.array([bool(c & targets) for c in classes], dtype=bool)
    prefixes = rules['key_determinants'].get(antibiotic, [])
    efflux = set(rules.get('efflux_classes', ['EFFLUX', 'MULTIDRUG']))
    gene_n = float((covers & ~is_mut).sum())
    mut_n = float((covers & is_mut).sum())
    row.update({
        'gene_class_n': gene_n,
        'mutation_class_n': mut_n,
        'gene_class_any': float(gene_n + mut_n > 0),
        'key_determinant': float(any(s.startswith(p) for s in symbols for p in prefixes)),
        'amr_genes_total': float(len(symbols)),
        'efflux_n': float(sum(bool(c & efflux) for c in classes)),
    })
    return row


def genes_found(hits, drug_class, rules):
    """`genes_found` for the response (progress/formats/README.md §2): every
    core AMR gene and mutation, `relevant` when its class covers the drug."""
    targets = set(rules['class_to_amrfinder'].get(drug_class, []))
    out = []
    for symbol, name, cls, subclass, kind in zip(hits['symbol'], hits['name'], hits['class'],
                                                 hits['subclass'], hits['type']):
        out.append({'gene': symbol, 'drug_class': str(cls).lower(), 'type': kind,
                    'relevant': bool(amr_classes(cls) & targets),
                    'subclass': str(subclass).lower(), 'name': name})
    return sorted(out, key=lambda g: (not g['relevant'], g['gene']))


class SpeciesProfiles:
    """Nearest species by cosine distance of 6-mer profiles."""

    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.species = z['species_name'].astype(str)
        self.genus = z['genus_name'].astype(str)
        p = z['profile'].astype(np.float64)
        self.unit = p / np.linalg.norm(p, axis=1, keepdims=True)

    def identify(self, counts6):
        f = counts6.astype(np.float64)
        norm = np.linalg.norm(f)
        if not norm:
            return None
        d = 1 - self.unit @ (f / norm)
        j = int(d.argmin())
        if d[j] > SPECIES_MAX_DISTANCE:
            return {'species': None, 'genus': None, 'distance': round(float(d[j]), 5)}
        return {'species': self.species[j], 'genus': self.genus[j], 'distance': round(float(d[j]), 5)}


class GenomeModelPredictor:
    FOLDER = KMER_FOLDER
    MIN_BP = 100_000   # a complete bacterial genome is 1-12 Mb

    def __init__(self, model_dir, folder=None):
        self.model_dir = model_dir
        if folder is None:
            folder = GENE_FOLDER if self.gene_model_servable(model_dir) else KMER_FOLDER
        self.folder = folder
        self.dir = os.path.join(model_dir, folder)
        self.model = None
        self.meta = {}
        self.metrics = load_metrics(os.path.join(self.dir, 'genome_metrics.json'))
        self.is_trained = False
        self.uses_genes = False
        self.amrfinder = None
        self.species_profiles = None
        self.fallback = None
        self._load()

    @staticmethod
    def gene_model_servable(model_dir):
        """A gene model is promoted and AMRFinderPlus can run here."""
        return (os.path.exists(os.path.join(model_dir, GENE_FOLDER, 'model.txt'))
                and find_amrfinder() is not None)

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
        self.uses_kmers = any(f.startswith(f'k{self.k}_') for f in self.features)
        self.uses_genes = any(f.startswith('g_') or f in ('gene_class_n', 'key_determinant')
                              for f in self.features)
        if self.uses_genes:
            # Served only with AMRFinderPlus and the rules to build its features
            self.amrfinder = find_amrfinder()
            self.rules = self.meta.get('gene_features')
            profiles = os.path.join(self.dir, 'species_profiles.npz')
            if os.path.exists(profiles):
                self.species_profiles = SpeciesProfiles(profiles)
            self.is_trained = bool(self.amrfinder and self.rules)
            if self.folder != KMER_FOLDER and os.path.exists(os.path.join(self.model_dir, KMER_FOLDER, 'model.txt')):
                self.fallback = GenomeModelPredictor(self.model_dir, folder=KMER_FOLDER)
        else:
            self.is_trained = True
        print(f"[Genome] Loaded {self.meta.get('run_id')} from {self.folder}/"
              f"{' (AMRFinderPlus ' + (self.amrfinder or 'not found') + ')' if self.uses_genes else ''}.")

    @property
    def threshold(self):
        return float(self.meta.get('threshold', 0.5))

    def features_frame(self, fasta_text, antibiotic, genus=None, species=None, hits=None, counts=None):
        """The model input for one genome and antibiotic, built as in training.
        Gene models need `hits` (run_amrfinder); `counts` saves recounting."""
        counts6, gc, length = counts if counts is not None else genome_counts(fasta_text)
        row = dict(zip(kmer_names(self.k), kmer_frequencies(counts6, self.k)))
        row['genome_gc'] = gc
        row['genome_length_mb'] = length / 1e6
        ab = normalize_antibiotic(antibiotic)
        row['Antibiotic'] = ab
        # The map the model was trained with, stored in its bundle
        drug_class = self.meta.get('drug_class_map', TRAINING_DRUG_CLASS_MAP).get(ab, 'other')
        row['drug_class'] = drug_class
        row['genus'] = genus or 'unknown'
        row['species'] = species or 'unknown'
        if self.uses_genes:
            row.update(gene_features(hits, ab, drug_class, self.rules, self.features))
        X = pd.DataFrame([row])
        for col, lv in self.levels.items():
            if col in X:
                # A value the model never saw (e.g. an unknown antibiotic) goes in
                # as missing, as LightGBM treats it; pandas will refuse it as a
                # value outside the categories
                value = lv.get(str(X[col].iloc[0]).lower())
                X[col] = pd.Categorical([value], categories=list(lv.values()))
        return X[self.features], length

    def detect_species(self, counts6):
        return self.species_profiles.identify(counts6) if self.species_profiles else None

    def predict(self, fasta_text, antibiotic, threshold=None, genus=None, species=None):
        if not self.is_trained:
            return {'error': 'no genome model is served' if self.model is None else
                    'this genome model needs AMRFinderPlus, which the server does not run'}
        counts = genome_counts(fasta_text)
        length = counts[2]
        if length < self.MIN_BP:
            return {'error': f'genome too short ({length:,} bp): upload a complete assembly',
                    'sequence_length': length}

        hits = detected = None
        organism = None
        if self.uses_genes:
            detected = self.detect_species(counts[0])
            if detected and detected['species']:
                try:
                    organism = organism_for(detected['species'], detected['genus'],
                                            supported_organisms(self.amrfinder))
                except (OSError, subprocess.SubprocessError):
                    organism = None
            try:
                hits, _ = run_amrfinder(fasta_text, organism, self.amrfinder)
            except (RuntimeError, OSError) as e:
                if self.fallback and self.fallback.is_trained:
                    result = self.fallback.predict(fasta_text, antibiotic, threshold, genus, species)
                    result['warning'] = f'{e}; answered by the k-mer model instead'
                    return result
                return {'error': str(e)}

        threshold = self.threshold if threshold is None else float(threshold)
        X, length = self.features_frame(fasta_text, antibiotic, genus, species, hits=hits, counts=counts)
        prob = float(self.model.predict(X)[0])
        ab = normalize_antibiotic(antibiotic)
        known = ab in self.levels.get('Antibiotic', {})
        result = {
            'prediction': 'Resistant' if prob >= threshold else 'Susceptible',
            'probability': round(prob, 4),
            'confidence': round((prob if prob >= threshold else 1 - prob) * 100, 1),
            'antibiotic': ab,
            'antibiotic_known': known,
            'sequence_length': length,
            'gc_content': round(float(counts[1]) * 100, 2),
            'threshold': threshold,
            'model_used': self.model_label,
            'model_run': self.meta.get('run_id'),
        }
        if self.uses_kmers:
            # Same fields as the old K-mer predictor, so /predict's page and
            # charts work unchanged; a gene-only model sends none (the page
            # then hides the k-mer cards)
            kmer_cols = [c for c in self.features if c.startswith(f'k{self.k}_')]
            top = X[kmer_cols].iloc[0].sort_values(ascending=False).head(10)
            result['top_kmers'] = [{'kmer': c.split('_', 1)[1], 'frequency': round(float(v), 5)}
                                   for c, v in top.items()]
        if self.uses_genes:
            drug_class = X['drug_class'].iloc[0] if 'drug_class' in X else \
                self.meta.get('drug_class_map', TRAINING_DRUG_CLASS_MAP).get(ab, 'other')
            result['genes_found'] = genes_found(hits, str(drug_class), self.rules)
            result['species_detected'] = dict(detected or {}, amrfinder_organism=organism)
        return result

    @property
    def model_label(self):
        run = self.meta.get('run_id')
        if self.uses_genes:
            return f'LightGBM on AMRFinderPlus resistance genes ({run})'
        return f'LightGBM on {self.k}-mers ({run})'

    @property
    def ab_list(self):
        """Antibiotics the model was trained on (the /predict dropdown)."""
        return sorted(self.levels.get('Antibiotic', {}).values()) if hasattr(self, 'levels') else []

    @property
    def status(self):
        if self.uses_genes:
            model_type = 'LightGBM on AMRFinderPlus resistance genes and mutations of the complete genome'
        else:
            model_type = f'LightGBM on {getattr(self, "k", 4)}-mer frequencies of the complete genome'
        return {
            'trained': self.is_trained,
            'model_type': model_type,
            'description': 'Predicts resistance from a complete genome assembly (FASTA)',
            'run_id': self.meta.get('run_id'),
            'antibiotics_known': len(self.ab_list),
            'feature_dim': len(getattr(self, 'features', [])),
            'needs_amrfinder': self.uses_genes,
            'amrfinder': bool(self.amrfinder) if self.uses_genes else None,
            'searches_genes': self.uses_genes and self.is_trained,
            'default_threshold': self.threshold,
            'metrics': self.metrics,
        }
