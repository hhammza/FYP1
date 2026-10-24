"""Was a genome in a served model's training data, or is it a fair test?

For the "fill from Genome ID" helper on /forecast (Suleman): a user who tries
the model on a genome it trained on sees a far better score than on a new one
(the first forecaster: AUC 0.94 on its training genomes, 0.64 on unseen ones),
so the page should say which it is.

experiments/promote.py writes, for each served model, the Genome IDs on each
side of its train/test split, rebuilt from the run's config and checked
against the run's test-row count:

    trained_models/lgbm_split_genomes.json.gz           /forecast
    trained_models/genome/split_genomes.json.gz          /predict, k-mer model
    trained_models/genome_genes/split_genomes.json.gz    /predict, gene model

    {"run_id": ..., "split": "grouped", "clean_version": "v7",
     "train": ["1000561.3", ...], "test": [...]}

Usage:
    from ml_models.training_genomes import genome_status
    genome_status(settings.TRAINED_MODELS_DIR, '562.1234')

Genome IDs are compared as text ('195.304' and '195.3040' are two genomes).
"""
import gzip
import json
import os

FILES = {
    'forecast': 'lgbm_split_genomes.json.gz',
    'genome_kmers': os.path.join('genome', 'split_genomes.json.gz'),
    'genome_genes': os.path.join('genome_genes', 'split_genomes.json.gz'),
}

ROLE_TEXT = {
    'test': 'not used in training: a fair test of the model',
    'train': 'used to train the model: its prediction will look better than on a new genome',
    None: 'not in this model\'s data',
}

_cache = {}


def load_split(path):
    """{'run_id', 'split', 'train': set, 'test': set} or None if the file is
    missing. Read once per file and kept; a re-promotion writes a new file
    with a new modification time, which is read again."""
    if not os.path.exists(path):
        return None
    key = (path, os.path.getmtime(path))
    if key not in _cache:
        with gzip.open(path, 'rt', encoding='utf-8') as fh:
            data = json.load(fh)
        if len(_cache) > 6:      # old versions of re-promoted files
            _cache.clear()
        _cache[key] ={'run_id': data.get('run_id'), 'split': data.get('split'),
                       'clean_version': data.get('clean_version'),
                       'train': set(data['train']), 'test': set(data['test'])}
    return _cache[key]


def role_of(split, genome_id):
    """'train', 'test' or None (not in the model's data)."""
    gid = str(genome_id).strip()
    if gid in split['test']:
        return 'test'
    if gid in split['train']:
        return 'train'
    return None


def genome_status(model_dir, genome_id):
    """For each served model whose split file exists:
    {'run_id', 'role': 'train' | 'test' | None, 'detail': plain sentence}."""
    out = {}
    for name, rel in FILES.items():
        split = load_split(os.path.join(str(model_dir), rel))
        if split is None:
            continue
        role = role_of(split, genome_id)
        out[name] = {'run_id': split['run_id'], 'role': role, 'detail': ROLE_TEXT[role]}
    return out
