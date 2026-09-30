"""Gene-lookup rule, the baseline a genome model has to beat.

What a lab without machine learning does with AMRFinderPlus (or ResFinder)
output: call a genome resistant to a drug when it carries a gene or point
mutation of that drug's class. Nothing is learned; the score is 1 or 0, read
from one of the drug-aware columns that experiments/genome/genes.py builds:

    gene_class_any     a gene or mutation whose AMRFinderPlus class covers the drug
    key_determinant    a named, well-known determinant for the drug (16 drugs only)

Several columns are joined with OR. A drug with no class mapping scores 0, as
the rule would. Run it with the same data and split as the B6 genome model so
the two sit side by side in registry.csv (Paper B in progress/RESEARCH_PLAN.md).

Config:
    {"model": {"type": "gene_rule", "params": {"columns": ["gene_class_any"]}}}
    with "features": {"genes": {"raw": false, "drug_aware": true}}
"""
import joblib
import numpy as np


class GeneRuleModel:
    name = 'gene_rule'

    def __init__(self, params=None):
        self.params = dict(params or {})
        self.columns = list(self.params.get('columns', ['gene_class_any']))

    def fit(self, X_tr, y_tr, X_val, y_val, cat_features):
        missing = [c for c in self.columns if c not in X_tr.columns]
        if missing:
            raise ValueError(f'gene_rule needs {missing}; set features.genes.drug_aware = true')
        return self

    def predict_proba(self, X):
        hit = np.zeros(len(X), dtype=bool)
        for c in self.columns:
            hit |= X[c].to_numpy(dtype=float) > 0
        return hit.astype(float)

    def save(self, path):
        joblib.dump({'type': self.name, 'columns': self.columns}, path + '.joblib')

    @property
    def info(self):
        return {'type': self.name, 'columns': self.columns, 'trained': False}
