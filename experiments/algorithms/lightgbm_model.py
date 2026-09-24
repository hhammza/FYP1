"""LightGBM, gradient-boosted decision trees.

The default for this project, and the algorithm behind every run so far.
It suits this dataset for two specific reasons:

  * native categorical handling - `Antibiotic` has 152 levels and `species`
    94; one-hot encoding them would be both wasteful and worse
  * native NaN handling, 93% of rows have no MIC, and LightGBM learns which
    branch missing values belong on rather than needing them imputed

Config:
    {"model": {"type": "lightgbm",
               "params": {"num_leaves": 127, "learning_rate": 0.03},
               "monotone_on": ["mic_value", "mic_log"]}}
"""


class LightGBMModel:
    name = 'lightgbm'

    #: Merged under whatever `model.params` a config supplies.
    DEFAULTS = {
        'objective': 'binary',      # binary log-loss
        'metric': 'auc',            # what early stopping watches
        'boosting_type': 'gbdt',
        'verbose': -1,
        'random_state': 42,
        'n_jobs': -1,
        'num_leaves': 63,           # capacity per tree
        'learning_rate': 0.05,
        'n_estimators': 500,        # upper bound; early stopping usually ends sooner
        'subsample': 0.8,           # row sampling per tree
        'colsample_bytree': 0.8,    # feature sampling per tree
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'is_unbalance': True,       # reweight for the 36.5% positive rate
        'cat_smooth': 10,           # shrink categorical splits on rare levels
        'max_cat_threshold': 32,
    }

    EARLY_STOPPING_ROUNDS = 30

    def __init__(self, params=None, monotone_on=None):
        self.params = {**self.DEFAULTS, **(params or {})}
        #: Features whose effect must be non-decreasing. Passing
        #: ["mic_value", "mic_log"] makes it structurally impossible for the
        #: model to predict *less* resistance at a higher MIC.
        self.monotone_on = monotone_on or []
        self.booster = None
        self.features = None

    def fit(self, X_tr, y_tr, X_val, y_val, cat_features):
        import lightgbm as lgb

        self.features = list(X_tr.columns)
        params = dict(self.params)

        if self.monotone_on:
            params['monotone_constraints'] = [
                1 if f in self.monotone_on else 0 for f in self.features]

        rounds = params.pop('n_estimators', 500)
        train_set = lgb.Dataset(X_tr, label=y_tr, categorical_feature=cat_features)
        val_set = lgb.Dataset(X_val, label=y_val, categorical_feature=cat_features,
                              reference=train_set)
        self.booster = lgb.train(
            params, train_set, num_boost_round=rounds, valid_sets=[val_set],
            callbacks=[lgb.early_stopping(self.EARLY_STOPPING_ROUNDS, verbose=False),
                       lgb.log_evaluation(100)])
        return self

    def predict_proba(self, X):
        return self.booster.predict(X[self.features])

    def save(self, path):
        self.booster.save_model(path + '.txt')

    @property
    def info(self):
        return {
            'kind': self.name,
            'n_trees': self.booster.num_trees(),
            'best_iteration': self.booster.best_iteration,
            'monotone_on': self.monotone_on,
        }
