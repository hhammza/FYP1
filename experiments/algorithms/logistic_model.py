"""Logistic regression, the interpretable linear baseline.

Its job is to answer "is gradient boosting earning its complexity?" On the
identical 400k sample, LightGBM scores 0.8201 and this scores 0.8024, a real
gap (the intervals do not overlap) but a modest one, which says most of the
signal here is linear in the features rather than in their interactions.

`saga` is the solver because the design matrix is sparse (one-hot over 152
antibiotics, 94 species, 41 genera) and it handles that efficiently.

Config:
    {"model": {"type": "logistic", "params": {"C": 0.5}}}
"""
from .base import SklearnEstimatorModel


class LogisticModel(SklearnEstimatorModel):
    name = 'logistic'

    DEFAULTS = {
        'max_iter': 200,
        'class_weight': 'balanced',   # counter the 36.5% positive rate
        'solver': 'saga',             # handles sparse one-hot input
        'n_jobs': -1,
    }

    def make_estimator(self):
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(**{**self.DEFAULTS, **self.params})
