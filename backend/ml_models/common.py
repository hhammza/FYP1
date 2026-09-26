"""Helpers shared by the prediction engines.

The antibiotic aliases and the species map live in train_models.py, which is
what the served models were trained with; reading them from there keeps a
user's input spelled the way the training rows were.
"""
import json
import os

try:
    from train_models import ANTIBIOTIC_ALIASES, load_species_map
except ImportError:  # backend/ not on sys.path, e.g. a bare `python -c`
    ANTIBIOTIC_ALIASES = {'rifampin': 'rifampicin'}

    def load_species_map():
        return {}


def normalize_antibiotic(name):
    """Lower-case, strip, and map a spelling variant to its canonical name.

    Names the alias table drops from training (drug classes such as
    'carbapenem') are returned unchanged; the model then reports them as
    unrecognised instead of silently answering for a different drug.
    """
    if name in (None, ''):
        return name
    ab = str(name).strip().lower()
    return ANTIBIOTIC_ALIASES.get(ab) or ab


def load_metrics(path):
    """metrics.json written beside a model artifact, or None if absent.

    The format is described in progress/formats/README.md.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        print(f"[metrics] Could not read {path}: {e}")
        return None
