"""Algorithms available to experiments, one file each.

    algorithms/
    ├── base.py                the contract + shared sklearn preprocessing
    ├── lightgbm_model.py      LightGBM        "type": "lightgbm"
    ├── logistic_model.py      LogisticRegr.   "type": "logistic"
    ├── random_forest_model.py RandomForest    "type": "random_forest"
    ├── xgboost_model.py       XGBoost         "type": "xgboost"
    └── catboost_model.py      CatBoost        "type": "catboost"

To add one: write a class with fit/predict_proba/save/info (see base.py), then
add a line to REGISTRY below. run.py needs no change, and every existing result
stays comparable because nothing else in the pipeline moves.
"""
from .base import CAT_FEATURES, align_categories, build_sklearn_preprocessor
from .catboost_model import CatBoostModel
from .lightgbm_model import LightGBMModel
from .logistic_model import LogisticModel
from .random_forest_model import RandomForestModel
from .xgboost_model import XGBoostModel

__all__ = ['CAT_FEATURES', 'align_categories', 'build_sklearn_preprocessor',
           'build_model', 'REGISTRY', 'LightGBMModel', 'LogisticModel',
           'RandomForestModel', 'XGBoostModel', 'CatBoostModel']

#: config "model": {"type": ...}  →  class
REGISTRY = {
    'lightgbm': LightGBMModel,
    'logistic': LogisticModel,
    'random_forest': RandomForestModel,
    'xgboost': XGBoostModel,
    'catboost': CatBoostModel,
}


def build_model(spec):
    """Instantiate the algorithm a config asks for."""
    kind = spec.get('type', 'lightgbm')
    if kind not in REGISTRY:
        raise ValueError(f'unknown model type {kind!r} - '
                         f'available: {", ".join(sorted(REGISTRY))}')
    cls = REGISTRY[kind]
    params = spec.get('params', {})
    if kind == 'lightgbm':
        return cls(params, spec.get('monotone_on'))
    return cls(params)
