"""Contract tests for the public API."""
import pytest

import amrpredict


def test_version_exposed():
    assert amrpredict.__version__


def test_bundled_models_are_found():
    import os
    d = amrpredict.default_model_dir()
    assert os.path.isdir(d)
    assert os.path.exists(os.path.join(d, 'amr_lgbm_final_model.txt'))


def test_status_reports_trained_models():
    st = amrpredict.status()
    assert st['lgbm_forecasting']['trained'] is True
    assert st['kmer_resistance']['trained'] is True
    # The timeline is a simulation, not a trained model — asserted so that a
    # future change to that claim has to be deliberate.
    assert st['mutation_timeline']['trained'] is False


def test_antibiotics_list_is_populated():
    ab = amrpredict.antibiotics()
    assert len(ab) > 50
    assert 'ciprofloxacin' in ab
    assert ab == sorted(ab)


def test_forecast_shape_and_range():
    r = amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4,
                            genus='Escherichia', species='coli')
    assert r['prediction'] in ('Resistant', 'Susceptible')
    assert 0.0 <= r['probability'] <= 1.0
    assert r['drug_class'] == 'fluoroquinolone'


def test_forecast_is_deterministic():
    kw = dict(taxon_id=562, mic_value=4)
    assert (amrpredict.forecast('ciprofloxacin', **kw)['probability']
            == amrpredict.forecast('ciprofloxacin', **kw)['probability'])


def test_antibiotic_name_is_case_insensitive():
    a = amrpredict.forecast('Ciprofloxacin', taxon_id=562)['probability']
    b = amrpredict.forecast('ciprofloxacin', taxon_id=562)['probability']
    assert a == b


def test_threshold_controls_the_call():
    """A threshold of 0 must call everything resistant, and 1 nothing."""
    assert amrpredict.forecast('ciprofloxacin', taxon_id=562,
                               threshold=0.0)['prediction'] == 'Resistant'
    assert amrpredict.forecast('ciprofloxacin', taxon_id=562,
                               threshold=1.0)['prediction'] == 'Susceptible'


def test_unknown_antibiotic_still_returns_a_result():
    r = amrpredict.forecast('notarealdrug', taxon_id=562)
    assert r['prediction'] in ('Resistant', 'Susceptible')
    assert r['drug_class'] == 'other'


def test_registry_returns_one_shared_instance():
    assert amrpredict.registry.lgbm() is amrpredict.registry.lgbm()


def test_registry_reset_rebuilds():
    first = amrpredict.registry.lgbm()
    amrpredict.registry.reset()
    assert amrpredict.registry.lgbm() is not first


def test_forecast_uses_the_promoted_threshold_and_calibration():
    """v0.2.0: the bundled forecaster is a promoted run, scored as the web app
    scores it (calibrated, species-level taxa, the run's own threshold)."""
    st = amrpredict.status()['lgbm_forecasting']
    assert st['run_id']
    r = amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)
    assert r['threshold'] == st['default_threshold']
    assert r['model_run'] == st['run_id']
    assert r['calibrated'] is (st['calibration'] is not None)


def test_status_carries_measured_metrics():
    m = amrpredict.status()['lgbm_forecasting']['metrics']
    assert m['run_id'] == amrpredict.status()['lgbm_forecasting']['run_id']
    assert 0.5 < m['test']['auc_roc'] <= 1.0


def test_strain_taxon_is_read_as_its_species():
    """A strain-level Taxon ID gets its species' rates when the model was
    trained on species-level taxa."""
    if amrpredict.status()['lgbm_forecasting']['taxon_level'] != 'species':
        pytest.skip('bundled model uses strain-level taxa')
    r = amrpredict.forecast('ciprofloxacin', taxon_id=1045010)   # an E. coli strain
    taxon = [i for i in r['evidence']['inputs'] if i['field'] == 'Taxon ID'][0]
    assert 'species 562' in taxon['detail']


def test_spelling_variants_reach_the_same_model_input():
    """Every model reads names through the shared alias table (amr_constants),
    as the web app does: 'Rifampin' is rifampicin everywhere."""
    fasta = '>x\n' + 'ACGTTGCAAT' * 400
    assert (amrpredict.predict_fasta(fasta, 'Rifampin')['probability']
            == amrpredict.predict_fasta(fasta, 'rifampicin')['probability'])
    t = amrpredict.simulate_timeline(fasta, 'Rifampin')
    assert t['antibiotic'] == 'rifampicin'
    assert t == amrpredict.simulate_timeline(fasta, 'rifampicin')
    assert amrpredict.forecast('Rifampin')['antibiotic'] == 'rifampicin'
