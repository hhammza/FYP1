"""Random forest, bagged trees, the non-boosted tree baseline.

Useful as a contrast to LightGBM: same family of learner, no boosting. If a
forest matches the booster, the gain was from ensembling rather than from
sequentially correcting errors. It is also the algorithm the k-mer genome
model uses in the backend, so a forest here keeps the two comparable.

Depth is capped because the one-hot design matrix is wide and unbounded trees
memorise rare categories.

Config:
    {"model": {"type": "random_forest", "params": {"n_estimators": 400}}}
"""
from .base import SklearnEstimatorModel


class RandomForestModel(SklearnEstimatorModel):
    name = 'random_forest'

    DEFAULTS = {
        'n_estimators': 200,
        'max_depth': 18,
        'n_jobs': -1,
        'class_weight': 'balanced',
        'random_state': 42,
    }

    def make_estimator(self):
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(**{**self.DEFAULTS, **self.params})
