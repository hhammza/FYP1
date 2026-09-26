"""
LightGBM AMR Resistance Forecasting Model
Input: antibiotic, taxon_id, mic_value (optional), mic_sign (optional), genus, species
Output: Resistant/Susceptible prediction + probability
"""
import os
import re
import numpy as np
import pandas as pd
import joblib
import warnings

from ml_models.common import (TRAINING_DRUG_CLASS_MAP, load_metrics, load_species_map,
                              normalize_antibiotic)

warnings.filterwarnings('ignore')

# Drug classes as training assigned them (train_models.py). A promoted model
# carries its own copy in lgbm_meta.joblib, which takes precedence.
DRUG_CLASS_MAP = TRAINING_DRUG_CLASS_MAP

# Known resistance rates per antibiotic (from training data statistics)
RESISTANCE_RATES = {
    'ampicillin': 0.65, 'amoxicillin': 0.58, 'amoxicillin/clavulanic acid': 0.40,
    'piperacillin': 0.55, 'piperacillin/tazobactam': 0.25, 'oxacillin': 0.48,
    'cefazolin': 0.32, 'cefoxitin': 0.30, 'cefotaxime': 0.35,
    'ceftazidime': 0.38, 'ceftriaxone': 0.36, 'cefepime': 0.30,
    'cefuroxime': 0.33, 'cephalothin': 0.45, 'cefpodoxime': 0.32,
    'imipenem': 0.18, 'meropenem': 0.17, 'ertapenem': 0.15, 'doripenem': 0.14,
    'aztreonam': 0.34,
    'ciprofloxacin': 0.42, 'levofloxacin': 0.38, 'norfloxacin': 0.40,
    'nalidixic acid': 0.55, 'ofloxacin': 0.44,
    'gentamicin': 0.28, 'tobramycin': 0.25, 'amikacin': 0.12,
    'streptomycin': 0.52, 'neomycin': 0.30, 'kanamycin': 0.38,
    'tetracycline': 0.58, 'doxycycline': 0.40, 'minocycline': 0.22, 'tigecycline': 0.08,
    'sulfamethoxazole': 0.62, 'trimethoprim': 0.60,
    'trimethoprim/sulfamethoxazole': 0.48, 'chloramphenicol': 0.32,
    'azithromycin': 0.35, 'erythromycin': 0.42,
    'colistin': 0.05, 'polymyxin b': 0.06,
    'vancomycin': 0.10, 'teicoplanin': 0.08,
    'clindamycin': 0.28, 'nitrofurantoin': 0.15,
    'rifampicin': 0.20,
}


class LGBMResistancePredictor:
    METRICS_FILE = 'lgbm_metrics.json'
    DEFAULT_THRESHOLD = 0.40   # used only when no metrics.json / meta says otherwise

    def __init__(self, model_dir):
        self.model_dir = model_dir
        self.model = None
        self.ab_rate = None
        self.taxon_rate = None
        self.genus_rate = None
        self.global_mean = 0.31
        self.is_trained = False
        # Written by experiments/promote.py; absent for the July artifacts,
        # which then behave exactly as before.
        self.calibration = None
        self.taxon_level = 'strain'
        self.threshold = self.DEFAULT_THRESHOLD
        self.drug_class_map = DRUG_CLASS_MAP
        self.species_map = {}
        self.metrics = load_metrics(os.path.join(model_dir, self.METRICS_FILE))
        # lower-case value -> the exact category level the booster was trained on
        self.levels = {}
        self.FINAL_FEATURES = [
            'Taxon ID', 'Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign',
            'is_lab_confirmed', 'computational_f1', 'mic_value', 'mic_log', 'has_mic',
            'ab_resistance_rate', 'taxon_ab_resistance_rate', 'genus_ab_resistance_rate',
        ]
        self.CAT_FEATURES = ['Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign']
        # Category values the booster was actually trained on. Anything outside
        # these sets is passed to LightGBM as an unknown category, which is
        # indistinguishable from leaving the field blank — hence the evidence
        # report built in predict().
        self.known = {c: set() for c in self.CAT_FEATURES}
        self.known_taxon_pairs = set()
        self._load()

    def _load(self):
        model_path = os.path.join(self.model_dir, 'amr_lgbm_final_model.txt')
        ab_rate_path = os.path.join(self.model_dir, 'ab_rate_full.joblib')

        if os.path.exists(model_path):
            try:
                import lightgbm as lgb
                self.model = lgb.Booster(model_file=model_path)
                if os.path.exists(ab_rate_path):
                    self.ab_rate = joblib.load(ab_rate_path)
                taxon_path = os.path.join(self.model_dir, 'taxon_ab_rate_full.joblib')
                genus_path = os.path.join(self.model_dir, 'genus_ab_rate_full.joblib')
                if os.path.exists(taxon_path):
                    df_t = joblib.load(taxon_path)
                    if hasattr(df_t, 'iterrows'):
                        # DataFrame with columns: ['Taxon ID', 'Antibiotic', 'taxon_ab_resistance_rate']
                        self.taxon_rate = {
                            (int(r['Taxon ID']), str(r['Antibiotic'])): float(r['taxon_ab_resistance_rate'])
                            for _, r in df_t.iterrows()
                        }
                    else:
                        self.taxon_rate = {(int(t), str(a)): float(v)
                                           for (t, a), v in dict(df_t).items()}
                if os.path.exists(genus_path):
                    df_g = joblib.load(genus_path)
                    if hasattr(df_g, 'iterrows'):
                        # DataFrame with columns: ['genus', 'Antibiotic', 'genus_ab_resistance_rate']
                        pairs = ((r['genus'], r['Antibiotic'], r['genus_ab_resistance_rate'])
                                 for _, r in df_g.iterrows())
                    else:
                        pairs = ((g, a, v) for (g, a), v in dict(df_g).items())
                    # Keyed lower-case: the July table stored 'Escherichia' but
                    # was looked up as 'escherichia', so it never matched.
                    self.genus_rate = {(str(g).lower(), str(a)): float(v) for g, a, v in pairs}
                # The booster stores the pandas category levels seen at training,
                # in the order the categorical columns appear in FINAL_FEATURES.
                pandas_cats = getattr(self.model, 'pandas_categorical', None) or []
                for col, levels in zip(self.CAT_FEATURES, pandas_cats):
                    self.known[col] = {str(v).lower() for v in levels}
                    self.levels[col] = {str(v).lower(): v for v in levels}
                if self.taxon_rate:
                    self.known_taxon_pairs = set(self.taxon_rate.keys())

                meta_path = os.path.join(self.model_dir, 'lgbm_meta.joblib')
                if os.path.exists(meta_path):
                    meta = joblib.load(meta_path)
                    self.global_mean = float(meta.get('global_mean', 0.31))
                    self.calibration = meta.get('calibration')
                    self.taxon_level = meta.get('taxon_level', 'strain')
                    self.threshold = float(meta.get('threshold', self.DEFAULT_THRESHOLD))
                    self.drug_class_map = meta.get('drug_class_map', DRUG_CLASS_MAP)
                if self.taxon_level == 'species':
                    self.species_map = load_species_map()
                self.is_trained = True
                print(f"[LightGBM] Model loaded from disk "
                      f"(run {self.run_id or 'unrecorded'}, taxon level {self.taxon_level}, "
                      f"calibration {(self.calibration or {}).get('method', 'none')}).")
            except Exception as e:
                print(f"[LightGBM] Could not load model: {e}")
        else:
            print("[LightGBM] No trained model found. Using heuristic predictions.")

    def _heuristic_predict(self, antibiotic, taxon_id, mic_value=None, mic_sign=None, genus=None):
        """Rule-based fallback when no trained model exists."""
        ab = self._normalize_antibiotic(antibiotic)
        base_rate = RESISTANCE_RATES.get(ab, 0.35)

        # MIC-based adjustment
        if mic_value is not None:
            try:
                mic = float(mic_value)
                if mic >= 32:
                    base_rate = min(base_rate + 0.30, 0.95)
                elif mic >= 8:
                    base_rate = min(base_rate + 0.15, 0.90)
                elif mic <= 0.25:
                    base_rate = max(base_rate - 0.25, 0.05)
                elif mic <= 1:
                    base_rate = max(base_rate - 0.10, 0.05)
            except (ValueError, TypeError):
                pass

        # Sign adjustment
        if mic_sign == '>=' or mic_sign == '>':
            base_rate = min(base_rate + 0.10, 0.95)
        elif mic_sign == '<=' or mic_sign == '<':
            base_rate = max(base_rate - 0.10, 0.05)

        # Add small noise for realism
        noise = np.random.uniform(-0.05, 0.05)
        prob = float(np.clip(base_rate + noise, 0.02, 0.98))
        return prob

    # Comparators a user may type or pick that the booster has no category for.
    # Mapping them onto the nearest learned sign beats silently dropping the
    # value into the unknown bucket, which reads as "no MIC sign given".
    MIC_SIGN_ALIASES = {'>=': '>', '\u2265': '>', '\u2264': '<=', '=<': '<=', '=>': '>'}

    def _normalize_antibiotic(self, antibiotic):
        # Same alias table the training rows went through (train_models.py)
        return normalize_antibiotic(antibiotic)

    def _species_taxon(self, taxon_id):
        """The Taxon ID the model was trained on: species level for promoted models."""
        if taxon_id in (None, '', 0):
            return None
        try:
            tid = int(float(taxon_id))
        except (TypeError, ValueError):
            return None
        if self.taxon_level == 'species':
            return int(self.species_map.get(tid, tid))
        return tid

    def _level(self, col, value):
        """The booster's own spelling of a category ('coli' \u2192 'coli',
        'escherichia' \u2192 'Escherichia'); unknown values pass through."""
        if value is None:
            return value
        return self.levels.get(col, {}).get(str(value).strip().lower(), value)

    def _calibrate(self, prob):
        cal = self.calibration
        prob = np.asarray(prob, dtype=float)
        if not cal:
            return prob
        if cal['method'] == 'isotonic':
            return np.interp(prob, cal['x'], cal['y'])
        if cal['method'] == 'platt':
            eps = 1e-6
            logit = np.log(np.clip(prob, eps, 1 - eps) / np.clip(1 - prob, eps, 1 - eps))
            return 1.0 / (1.0 + np.exp(-(cal['a'] * logit + cal['b'])))
        return prob

    def features_frame(self, records):
        """Model input for many isolates at once, built exactly as predict() does.

        `records` is a DataFrame with columns antibiotic, taxon_id, mic_value,
        mic_sign, genus, species (missing columns count as not provided).
        experiments/evaluate_shipped.py scores the served model through this,
        so its numbers describe what /forecast actually runs.
        """
        n = len(records)
        col = lambda c: records[c] if c in records else pd.Series([None] * n, index=records.index)
        ab = col('antibiotic').map(self._normalize_antibiotic)
        taxon = col('taxon_id').map(self._species_taxon)
        mic = pd.to_numeric(col('mic_value'), errors='coerce').astype(float)
        sign = col('mic_sign').map(lambda s: self._normalize_mic_sign(s)[0])
        genus = col('genus').fillna('unknown').astype(str).str.strip()
        species = col('species').fillna('unknown').astype(str).str.strip()

        ab_rate = ab.map(self.ab_rate if self.ab_rate is not None else {}).astype(float)
        ab_rate = ab_rate.fillna(self.global_mean)
        tax_rate = pd.Series([self.taxon_rate.get((t, a)) if (self.taxon_rate and t) else None
                              for t, a in zip(taxon, ab)], index=records.index, dtype=float)
        gen_rate = pd.Series([self.genus_rate.get((g.lower(), a)) if self.genus_rate else None
                              for g, a in zip(genus, ab)], index=records.index, dtype=float)

        X = pd.DataFrame({
            'Taxon ID': taxon.fillna(0).astype('int64'),
            'Antibiotic': ab.map(lambda v: self._level('Antibiotic', v)),
            'drug_class': ab.map(lambda v: self.drug_class_map.get(v, 'other')),
            'genus': genus.map(lambda v: self._level('genus', v)),
            'species': species.map(lambda v: self._level('species', v)),
            'mic_sign': sign,
            # The form has no provenance fields; a user's isolate is scored as
            # an unconfirmed computational-quality record.
            'is_lab_confirmed': 0,
            'computational_f1': 0.85,
            'mic_value': mic,
            'mic_log': np.log1p(mic.clip(lower=0)),
            'has_mic': mic.notna().astype(int),
            'ab_resistance_rate': ab_rate,
            'taxon_ab_resistance_rate': tax_rate.fillna(ab_rate),
            'genus_ab_resistance_rate': gen_rate.fillna(ab_rate),
        }, index=records.index)
        for c in self.CAT_FEATURES:
            X[c] = X[c].astype(str).astype('category')
        return X[self.FINAL_FEATURES]

    def predict_frame(self, records):
        """Calibrated P(resistant) for each row of `records` (trained model only)."""
        raw = self.model.predict(self.features_frame(records))
        return self._calibrate(raw)

    @property
    def run_id(self):
        return (self.metrics or {}).get('run_id')

    def _normalize_mic_sign(self, mic_sign):
        """Return (value_sent_to_model, was_rewritten)."""
        if not mic_sign:
            return 'unknown', False
        sign = str(mic_sign).strip()
        if sign.lower() in self.known['mic_sign']:
            return sign, False
        alias = self.MIC_SIGN_ALIASES.get(sign)
        if alias and alias.lower() in self.known['mic_sign']:
            return alias, True
        return sign, False

    def _evidence(self, *, antibiotic, taxon_id, genus, species, mic_value,
                  mic_sign_in, mic_sign_used, sign_rewritten, rates, taxon_used=None):
        """Per-field account of what the model recognised, ignored or inferred.

        Every optional field that is blank, or holds a value the model has no
        category for, contributes nothing to the prediction. Without this the
        two cases look identical in the UI, which is the whole point of the
        report: the user should never have to guess which of their inputs
        actually moved the number.
        """
        known = self.known
        inputs = []

        ab_known = antibiotic in known['Antibiotic'] if known['Antibiotic'] else True
        inputs.append({
            'field': 'Antibiotic',
            'value': antibiotic,
            'state': 'used' if ab_known else 'unrecognized',
            'detail': (
                f"Population resistance rate {rates['drug'] * 100:.1f}%"
                if ab_known else
                'Not in the training data — the model is falling back to the '
                f"overall resistance rate ({self.global_mean * 100:.1f}%)"
            ),
        })

        if taxon_id in (None, '', 0):
            inputs.append({
                'field': 'Taxon ID', 'value': None, 'state': 'missing',
                'detail': 'Not provided — using the drug-level rate instead of '
                          'an organism-specific one',
            })
        else:
            if taxon_used is None:
                taxon_used = self._species_taxon(taxon_id)
            matched = taxon_used is not None and (taxon_used, antibiotic) in self.known_taxon_pairs
            detail = (
                f"Organism-specific rate for this drug: {rates['taxon'] * 100:.1f}%"
                if matched else
                'No training records for this organism and drug together — '
                'this field did not affect the result'
            )
            try:
                typed = int(float(taxon_id))
            except (TypeError, ValueError):
                typed = taxon_id
            if taxon_used is not None and taxon_used != typed:
                detail = f"Read as species {taxon_used}. " + detail
            inputs.append({
                'field': 'Taxon ID',
                'value': typed,
                'state': 'used' if matched else 'unrecognized',
                'detail': detail,
            })

        for field, value, vocab_key in (('Genus', genus, 'genus'), ('Species', species, 'species')):
            if not value or value == 'unknown':
                inputs.append({
                    'field': field, 'value': None, 'state': 'missing',
                    'detail': 'Not provided',
                })
                continue
            vocab = known[vocab_key]
            recognized = (not vocab) or str(value).lower() in vocab
            detail = 'Recognised by the model'
            if field == 'Genus' and recognized:
                detail = f"Genus-level rate for this drug: {rates['genus'] * 100:.1f}%"
            elif not recognized:
                detail = 'Not among the organisms in the training data — this ' \
                         'field did not affect the result'
            inputs.append({
                'field': field, 'value': value,
                'state': 'used' if recognized else 'unrecognized',
                'detail': detail,
            })

        if mic_value in (None, ''):
            inputs.append({
                'field': 'MIC', 'value': None, 'state': 'missing',
                'detail': 'Not provided — the strongest available signal is absent',
            })
        else:
            detail = f"{mic_value} mg/L"
            state = 'used'
            if sign_rewritten:
                detail += f" — sign '{mic_sign_in}' has no match in the training " \
                          f"data and was read as '{mic_sign_used}'"
                state = 'normalized'
            elif mic_sign_used == 'unknown':
                detail += ' — no comparator given'
            else:
                detail += f" (comparator '{mic_sign_used}')"
            inputs.append({'field': 'MIC', 'value': mic_value, 'state': state, 'detail': detail})

        has_mic = mic_value not in (None, '')
        # Species alone carries no rate lookup, so it does not lift the estimate
        # to organism level on its own — only a matched taxon or genus does.
        has_organism = any(i['state'] == 'used' and
                           i['field'] in ('Taxon ID', 'Genus') for i in inputs)

        if has_mic and has_organism:
            level, label = 'full', 'Isolate-level estimate'
            summary = ('Based on a measured MIC and organism-specific resistance '
                       'rates — the model is using every signal it has.')
        elif has_mic:
            level, label = 'mic', 'MIC-driven estimate'
            summary = ('Based on the measured MIC for this drug. No organism was '
                       'recognised, so population-level rates stand in for the species.')
        elif has_organism:
            level, label = 'organism', 'Organism-level estimate'
            summary = ('Based on historical resistance rates for this organism and '
                       'drug. Without an MIC, this reflects the population, not this isolate.')
        else:
            level, label = 'drug_only', 'Population-level estimate'
            summary = ('Based only on the historical resistance rate for this drug. '
                       'Nothing about this specific isolate informed the number — '
                       'add an MIC value for an isolate-level prediction.')

        return {
            'level': level,
            'label': label,
            'summary': summary,
            'inputs': inputs,
            'used_count': sum(1 for i in inputs if i['state'] in ('used', 'normalized')),
            'total_count': len(inputs),
            'rates': {k: round(v, 4) for k, v in rates.items()},
        }

    def predict(self, antibiotic, taxon_id=None, mic_value=None, mic_sign=None,
                genus='unknown', species='unknown', threshold=None):
        if threshold is None:
            threshold = self.threshold
        antibiotic = self._normalize_antibiotic(antibiotic)
        drug_class = self.drug_class_map.get(antibiotic, 'other')
        taxon_used = self._species_taxon(taxon_id)

        mic_sign_used, sign_rewritten = self._normalize_mic_sign(mic_sign)
        rates = {'drug': self.global_mean, 'taxon': self.global_mean, 'genus': self.global_mean}

        # Set from what actually ran, so a failure is never shown as the model.
        model_used = 'Heuristic (untrained)'
        if self.is_trained:
            try:
                rec = pd.DataFrame([{'antibiotic': antibiotic, 'taxon_id': taxon_id,
                                     'mic_value': mic_value, 'mic_sign': mic_sign,
                                     'genus': genus, 'species': species}])
                X = self.features_frame(rec)
                rates = {'drug': float(X['ab_resistance_rate'].iloc[0]),
                         'taxon': float(X['taxon_ab_resistance_rate'].iloc[0]),
                         'genus': float(X['genus_ab_resistance_rate'].iloc[0])}
                prob = float(self._calibrate(self.model.predict(X))[0])
                model_used = 'LightGBM (trained)'
            except Exception as e:
                print(f"[LightGBM] Prediction error: {e}")
                prob = self._heuristic_predict(antibiotic, taxon_id, mic_value, mic_sign, genus)
                model_used = 'Heuristic fallback'
        else:
            prob = self._heuristic_predict(antibiotic, taxon_id, mic_value, mic_sign, genus)

        label = 'Resistant' if prob >= threshold else 'Susceptible'
        confidence = prob if prob >= threshold else 1 - prob

        return {
            'prediction': label,
            'probability': round(prob, 4),
            'confidence': round(confidence * 100, 1),
            'antibiotic': antibiotic,
            'drug_class': drug_class,
            'threshold': threshold,
            'model_used': model_used,
            'model_run': self.run_id,
            'calibrated': bool(self.calibration) and model_used == 'LightGBM (trained)',
            'evidence': self._evidence(
                antibiotic=antibiotic, taxon_id=taxon_id, taxon_used=taxon_used,
                genus=genus, species=species,
                mic_value=mic_value, mic_sign_in=mic_sign, mic_sign_used=mic_sign_used,
                sign_rewritten=sign_rewritten, rates=rates,
            ),
        }

    @property
    def vocabulary(self):
        """The values this model can actually distinguish, for the UI to offer."""
        taxa = sorted({t for t, _ in self.known_taxon_pairs})
        antibiotics = sorted({self._normalize_antibiotic(ab) for ab in self.known['Antibiotic']})
        return {
            'antibiotics': antibiotics,
            'genera': sorted(g.capitalize() for g in self.known['genus']),
            'species': sorted(self.known['species']),
            'mic_signs': sorted(self.known['mic_sign'] - {'unknown', 'exact'}),
            'taxon_ids': taxa,
            'taxon_id_range': [taxa[0], taxa[-1]] if taxa else None,
        }

    def batch_predict(self, records):
        """Predict for a list of records."""
        results = []
        for rec in records:
            r = self.predict(**rec)
            results.append(r)
        return results

    def get_drug_class_summary(self, antibiotic):
        ab = self._normalize_antibiotic(antibiotic)
        dc = self.drug_class_map.get(ab, 'other')
        related = [k for k, v in self.drug_class_map.items() if v == dc and k != ab][:5]
        return {'drug_class': dc, 'related_antibiotics': related}

    @property
    def status(self):
        return {
            'trained': self.is_trained,
            'model_type': 'LightGBM Gradient Boosting',
            'description': 'Forecasts antibiotic resistance from genome metadata and MIC values',
            'features': self.FINAL_FEATURES,
            'run_id': self.run_id,
            'default_threshold': self.threshold,
            'calibration': (self.calibration or {}).get('method'),
            'taxon_level': self.taxon_level,
            # Measured numbers, read from lgbm_metrics.json beside the artifact;
            # None when the file is missing, so the UI never shows a stale guess.
            'metrics': self.metrics,
        }
