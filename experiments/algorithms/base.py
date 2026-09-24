"""The contract every algorithm file implements, plus what they share.

An algorithm file defines one class with four methods:

    fit(X_tr, y_tr, X_val, y_val, cat_features) -> self
        Train. The validation set is for early stopping only, never for
        threshold choice (run.py does that) and never for final metrics.

    predict_proba(X) -> np.ndarray
        Probability of the positive class (Resistant), one per row.

    save(path) -> None
        Write the artifact. `path` has no extension; add your own.

    info -> dict
        Whatever belongs in metrics.json about how training went.

Register it in algorithms/__init__.py and it becomes usable from any config
via {"model": {"type": "<name>"}} with no change to run.py.
"""
import pandas as pd

# Columns treated as categorical throughout the pipeline.
CAT_FEATURES = ['Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign']


def align_categories(train_df, *other_dfs, columns=CAT_FEATURES):
    """Give train and test identical category levels.

    Without this each frame builds its own codes, so the same string can mean
    a different integer on either side of the split. That silently makes a
    model look worse (or better) than it is.
    """
    out = [df.copy() for df in [train_df] + list(other_dfs)]
    for col in columns:
        if col not in train_df.columns:
            continue
        levels = pd.Index(sorted(train_df[col].astype(str).unique()))
        for df in out:
            df[col] = pd.Categorical(df[col].astype(str), categories=levels)
    return out


def build_sklearn_preprocessor(X, cat_features, min_frequency=20):
    """Sparse one-hot for categoricals + imputed, scaled numerics.

    Shared by the scikit-learn estimators (logistic regression, random
    forest). Unlike the boosting libraries, they cannot take raw categorical
    columns or NaNs.
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    cats = [c for c in cat_features if c in X.columns]
    nums = [c for c in X.columns if c not in cats]
    return ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore', min_frequency=min_frequency), cats),
        ('num', Pipeline([('impute', SimpleImputer(strategy='median')),
                          ('scale', StandardScaler(with_mean=False))]), nums),
    ])


class SklearnEstimatorModel:
    """Base for scikit-learn estimators: shared preprocessing, one estimator.

    A subclass supplies `name` and `make_estimator()`. Everything else is
    identical across them and lives here: stringifying categoricals, fitting
    the pipeline, predicting and saving.
    """

    name = 'sklearn'

    def __init__(self, params=None):
        self.params = params or {}
        self.pipe = None
        self.features = None

    def make_estimator(self):
        raise NotImplementedError

    def _as_strings(self, X, cat_features):
        X = X.copy()
        for c in cat_features:
            if c in X.columns:
                X[c] = X[c].astype(str)
        return X

    def fit(self, X_tr, y_tr, X_val, y_val, cat_features):
        from sklearn.pipeline import Pipeline

        self.features = list(X_tr.columns)
        self.cat_features = list(cat_features)
        X_tr = self._as_strings(X_tr, cat_features)
        pre = build_sklearn_preprocessor(X_tr, cat_features)
        self.pipe = Pipeline([('pre', pre), ('clf', self.make_estimator())]).fit(X_tr, y_tr)
        return self

    def predict_proba(self, X):
        X = self._as_strings(X[self.features], getattr(self, 'cat_features', CAT_FEATURES))
        return self.pipe.predict_proba(X)[:, 1]

    def save(self, path):
        import joblib
        joblib.dump(self.pipe, path + '.joblib')

    @property
    def info(self):
        return {'kind': self.name, 'params': self.params}
