"""XGBoost, the other mainstream gradient-boosting library.

A like-for-like comparison against LightGBM: same family, different split
algorithm (level-wise rather than leaf-wise growth) and different categorical
handling. If the two land within each other's confidence intervals, that is
evidence the result is about the data rather than the library.

Needs `pip install xgboost`; the run exits with that hint if it is missing.

Config:
    {"model": {"type": "xgboost", "params": {"max_depth": 10}}}
"""


class XGBoostModel:
    name = 'xgboost'

    DEFAULTS = {
        'n_estimators': 600,
        'learning_rate': 0.05,
        'max_depth': 8,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'n_jobs': -1,
        'eval_metric': 'auc',
        'enable_categorical': True,   # accepts pandas categorical dtypes
        'tree_method': 'hist',        # required for categorical support
        'early_stopping_rounds': 30,
        'random_state': 42,
    }

    def __init__(self, params=None):
        self.params = params or {}
        self.model = None
        self.features = None

    def fit(self, X_tr, y_tr, X_val, y_val, cat_features):
        try:
            import xgboost as xgb
        except ImportError:
            raise SystemExit('xgboost not installed, pip install xgboost')

        self.features = list(X_tr.columns)
        n_pos = max(int((y_tr == 1).sum()), 1)
        params = {
            **self.DEFAULTS,
            # XGBoost has no `is_unbalance`; this is the equivalent.
            'scale_pos_weight': float((y_tr == 0).sum() / n_pos),
            **self.params,
        }
        self.model = xgb.XGBClassifier(**params)
        self.model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X[self.features])[:, 1]

    def save(self, path):
        self.model.save_model(path + '.json')

    @property
    def info(self):
        best = getattr(self.model, 'best_iteration', None)
        return {'kind': self.name, 'best_iteration': best}
