"""Helpers shared by the prediction engines.

Antibiotic names and drug classes come from amr_constants.py, the same table
the training rows went through, so a user's input is spelled the way the
training rows were. The species map lives in train_models.py.
"""
import json
import os

from amr_constants import ANTIBIOTIC_ALIASES, normalize_antibiotic  # noqa: F401
from amr_constants import DRUG_CLASS_MAP as TRAINING_DRUG_CLASS_MAP  # noqa: F401

try:
    from train_models import load_species_map
except ImportError:  # backend/ not on sys.path, e.g. a bare `python -c`
    def load_species_map():
        return {}


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
