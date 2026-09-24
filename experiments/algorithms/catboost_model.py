"""CatBoost, gradient boosting with ordered target statistics.

The most interesting comparison in this folder. CatBoost's headline feature is
*ordered* target statistics: it encodes a category using only rows that come
earlier in a random permutation, which is a principled, built-in solution to
exactly the leakage that `encoders.py` handles by hand with out-of-fold folds.

So the natural experiment is CatBoost with `target_encoding: "none"` against
LightGBM with `target_encoding: "oof"`, does the library's own method beat the
hand-rolled one?

Needs `pip install catboost`.

Config:
    {"model": {"type": "catboost", "params": {"depth": 10}},
     "features": {"target_encoding": "none"}}
"""


class CatBoostModel:
    name = 'catboost'

    DEFAULTS = {
        'iterations': 1500,
        'learning_rate': 0.05,
        'depth': 8,
        'eval_metric': 'AUC',
        'auto_class_weights': 'Balanced',
        'random_seed': 42,
        'verbose': 200,
    }

    EARLY_STOPPING_ROUNDS = 50

    def __init__(self, params=None):
        self.params = params or {}
        self.model = None
        self.features = None
        self.cat_features = []

    def _as_strings(self, X):
        X = X.copy()
        for c in self.cat_features:
            if c in X.columns:
                X[c] = X[c].astype(str)
        return X

    def fit(self, X_tr, y_tr, X_val, y_val, cat_features):
        try:
            from catboost import CatBoostClassifier, Pool
        except ImportError:
            raise SystemExit('catboost not installed, pip install catboost')

        self.features = list(X_tr.columns)
        self.cat_features = list(cat_features)
        # CatBoost wants categoricals as strings, not pandas categorical codes.
        X_tr, X_val = self._as_strings(X_tr), self._as_strings(X_val)

        self.model = CatBoostClassifier(**{**self.DEFAULTS, **self.params})
        self.model.fit(Pool(X_tr, y_tr, cat_features=self.cat_features),
                       eval_set=Pool(X_val, y_val, cat_features=self.cat_features),
                       early_stopping_rounds=self.EARLY_STOPPING_ROUNDS)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(self._as_strings(X[self.features]))[:, 1]

    def save(self, path):
        self.model.save_model(path + '.cbm')

    @property
    def info(self):
        return {'kind': self.name,
                'best_iteration': getattr(self.model, 'best_iteration_', None),
                'tree_count': getattr(self.model, 'tree_count_', None)}
