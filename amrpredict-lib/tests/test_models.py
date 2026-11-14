"""The 0.3.0 models: the timeline ML forecast, the RL agent, species identification and the CLI."""
import json

import pytest

import amrpredict
from amrpredict import cli


# --- forecast_trend --------------------------------------------------------

def test_trend_shape_and_band():
    r = amrpredict.forecast_trend('salmonella', 'Ciprofloxacin', years_ahead=4)
    assert (r['organism'], r['antibiotic']) == ('Salmonella', 'ciprofloxacin')
    assert len(r['history']) >= 2 and len(r['forecast']) == 4
    assert r['forecast'][0]['year'] == r['history'][-1]['year'] + 1
    widths = [f['hi'] - f['lo'] for f in r['forecast']]
    for f in r['forecast']:
        assert 0 <= f['lo'] <= f['resistant_pct'] <= f['hi'] <= 100
    assert widths[-1] >= widths[0]          # the band widens (until it hits 0 or 100)
    assert {'model', 'last_value'} <= set(r['metrics'])


def test_trend_is_deterministic():
    assert amrpredict.forecast_trend('Salmonella', 'ciprofloxacin') == \
        amrpredict.forecast_trend('Salmonella', 'ciprofloxacin')


@pytest.mark.parametrize('genus,drug,years', [('Notagenus', 'ciprofloxacin', 5),
                                              ('Salmonella', 'notadrug', 5),
                                              ('Salmonella', 'ciprofloxacin', 0),
                                              ('Salmonella', 'ciprofloxacin', 11)])
def test_trend_bad_input_gives_an_error(genus, drug, years):
    assert 'error' in amrpredict.forecast_trend(genus, drug, years_ahead=years)


def test_trend_series_lists_what_can_be_forecast():
    series = amrpredict.trend_series()
    assert 'ciprofloxacin' in series['Salmonella']
    for genus, drugs in list(series.items())[:20]:
        for ab in drugs[:3]:
            assert 'error' not in amrpredict.forecast_trend(genus, ab, years_ahead=1)


# --- plan_treatment --------------------------------------------------------

def test_plan_shape():
    r = amrpredict.plan_treatment('Ciprofloxacin', n_weeks=12)
    assert r['drugs'][0] == 'ciprofloxacin'
    assert r['policies'][0]['name'] == 'rl'
    assert len(r['policies']) == 7
    for p in r['policies']:
        assert len(p['policy']) == 12
        assert set(p['policy']) <= set(r['drugs'])
    assert r['best'] in {p['name'] for p in r['policies']}


def test_plan_is_repeatable_with_a_seed():
    assert amrpredict.plan_treatment('gentamicin', n_weeks=20, seed=3) == \
        amrpredict.plan_treatment('gentamicin', n_weeks=20, seed=3)


@pytest.mark.parametrize('drug,weeks', [('ampicillin', 12), ('imipenem', 0), ('imipenem', 105)])
def test_plan_bad_input_gives_an_error(drug, weeks):
    assert 'error' in amrpredict.plan_treatment(drug, n_weeks=weeks)


# --- identify_species ------------------------------------------------------

def test_species_of_a_random_sequence_is_unknown():
    import random
    rng = random.Random(1)
    seq = ''.join(rng.choice('ACGT') for _ in range(150_000))
    r = amrpredict.identify_species('>x\n' + seq)
    assert r['species'] is None and r['genus'] is None


def test_species_needs_a_complete_genome():
    assert 'error' in amrpredict.identify_species('>x\nACGT\n')


# --- antibiotics and status ------------------------------------------------

def test_antibiotic_lists_per_model():
    assert 'ciprofloxacin' in amrpredict.antibiotics()
    assert len(amrpredict.antibiotics('forecast')) > 50
    assert 'ciprofloxacin' in amrpredict.antibiotics('trend')
    assert amrpredict.antibiotics('rl') == ['ciprofloxacin', 'gentamicin', 'imipenem']
    with pytest.raises(ValueError):
        amrpredict.antibiotics('nope')


def test_status_has_every_model():
    st = amrpredict.status()
    assert st['version'] == amrpredict.__version__ == '0.3.0'
    assert set(st) >= {'lgbm_forecasting', 'genome_resistance', 'trend_forecast', 'rl_agent',
                       'mutation_timeline'}
    assert 0.5 < st['genome_resistance']['metrics']['test']['auc_roc'] <= 1.0


# --- command line ----------------------------------------------------------

def run(capsys, *argv):
    code = cli.main(['--compact', *argv])
    return code, json.loads(capsys.readouterr().out)


def test_cli_trend_and_plan(capsys):
    code, out = run(capsys, 'trend', 'Salmonella', 'ciprofloxacin', '--years', '2')
    assert code == 0 and len(out['forecast']) == 2
    code, out = run(capsys, 'plan', 'imipenem', '--weeks', '8')
    assert code == 0 and out['drugs'][0] == 'imipenem'


def test_cli_unusable_input_is_an_error_payload(capsys):
    """As for a short FASTA: exit 0 with `error` in the JSON, like the Python API."""
    code, out = run(capsys, 'plan', 'ampicillin')
    assert code == 0 and 'error' in out


def test_cli_antibiotics_per_model(capsys):
    code, out = run(capsys, 'antibiotics', '--model', 'rl')
    assert out == ['ciprofloxacin', 'gentamicin', 'imipenem']
