"""Edge cases for FASTA input.

This is user-supplied data, so it is where malformed input actually arrives.
Each test states the behaviour the library guarantees, so a regression here
fails loudly rather than silently changing what callers get.
"""
import random

import pytest

import amrpredict
from amrpredict.kmer import read_fasta_sequence


def make_sequence(n=3000, seed=7):
    rng = random.Random(seed)
    return ''.join(rng.choice('ACGT') for _ in range(n))


def as_fasta(seq, header='>test_contig', width=70):
    body = '\n'.join(seq[i:i + width] for i in range(0, len(seq), width))
    return f'{header}\n{body}\n'


# --- parsing ---------------------------------------------------------------

def test_headers_are_stripped():
    seq = make_sequence(200)
    assert read_fasta_sequence(as_fasta(seq)) == seq


def test_multiple_records_are_concatenated():
    a, b = make_sequence(150, seed=1), make_sequence(150, seed=2)
    assert read_fasta_sequence(as_fasta(a) + as_fasta(b, '>second')) == a + b


def test_lowercase_is_normalised():
    seq = make_sequence(200)
    assert read_fasta_sequence(as_fasta(seq.lower())) == seq


def test_non_acgt_characters_are_discarded():
    """Ambiguity codes and whitespace are dropped rather than rejected."""
    assert read_fasta_sequence('>x\nACGTNNNRYKM\nACGT\n') == 'ACGTACGT'


def test_sequence_without_a_header_is_accepted():
    seq = make_sequence(200)
    assert read_fasta_sequence(seq) == seq


def test_empty_input_yields_empty_sequence():
    assert read_fasta_sequence('') == ''
    assert read_fasta_sequence('>header only\n') == ''


def test_long_sequences_are_truncated():
    capped = read_fasta_sequence(as_fasta(make_sequence(12_000)), max_bp=5_000)
    assert len(capped) == 5_000


# --- predict_fasta ---------------------------------------------------------

def test_predict_on_a_normal_genome():
    r = amrpredict.predict_fasta(as_fasta(make_sequence()), 'ciprofloxacin')
    assert r['prediction'] in ('Resistant', 'Susceptible')
    assert 0.0 <= r['probability'] <= 1.0
    assert r['sequence_length'] == 3000
    assert 0.0 <= r['gc_content'] <= 100.0
    assert len(r['top_kmers']) == 10
    assert all(len(k['kmer']) == 4 for k in r['top_kmers'])


@pytest.mark.parametrize('bad', ['', '>header only\n', '>x\nACGT\n', 'NNNN' * 50])
def test_too_short_input_reports_an_error_instead_of_raising(bad):
    """Short or empty input returns an error dict; it must never raise."""
    r = amrpredict.predict_fasta(bad, 'ciprofloxacin')
    assert 'error' in r
    assert 'prediction' not in r


def test_predict_is_deterministic():
    fasta = as_fasta(make_sequence())
    a = amrpredict.predict_fasta(fasta, 'ciprofloxacin')['probability']
    b = amrpredict.predict_fasta(fasta, 'ciprofloxacin')['probability']
    assert a == b


def test_unknown_antibiotic_is_tolerated():
    r = amrpredict.predict_fasta(as_fasta(make_sequence()), 'notarealdrug')
    assert r['prediction'] in ('Resistant', 'Susceptible')


# --- simulate_timeline -----------------------------------------------------

def test_timeline_returns_the_requested_span():
    r = amrpredict.simulate_timeline(as_fasta(make_sequence()), 'ciprofloxacin', n_weeks=6)
    weeks = r['timeline']
    # Week 0 is the baseline, so n_weeks=6 spans 7 points.
    assert len(weeks) == 7
    assert [w['week'] for w in weeks] == list(range(7))


def test_timeline_resistance_is_monotonic_under_pressure():
    """Sustained antibiotic pressure should never reduce resistance."""
    r = amrpredict.simulate_timeline(as_fasta(make_sequence()), 'ciprofloxacin', n_weeks=8)
    # Despite the name, these fields are percentages (0-100), not fractions.
    frac = [w['resistant_fraction'] for w in r['timeline']]
    assert frac == sorted(frac)
    assert all(0.0 <= f <= 100.0 for f in frac)


def test_timeline_compartments_partition_the_population_early():
    """Before the susceptible pool is exhausted, the three shares total 100%."""
    r = amrpredict.simulate_timeline(as_fasta(make_sequence()), 'ciprofloxacin', n_weeks=4)
    for w in r['timeline']:
        total = (w['resistant_fraction'] + w['susceptible_fraction']
                 + w['intermediate_fraction'])
        assert total == pytest.approx(100.0, abs=0.5)


@pytest.mark.xfail(strict=True, reason=(
    'Known bug: once susceptible_fraction clamps at 0 the compartments are '
    'not rebalanced, so the three shares sum above 100% (~106% by week 8). '
    'The intermediate share is pinned at a constant 25%. Remove this xfail '
    'when the simulation renormalises.'))
def test_timeline_compartments_partition_the_population_throughout():
    r = amrpredict.simulate_timeline(as_fasta(make_sequence()), 'ciprofloxacin', n_weeks=8)
    for w in r['timeline']:
        total = (w['resistant_fraction'] + w['susceptible_fraction']
                 + w['intermediate_fraction'])
        assert total == pytest.approx(100.0, abs=0.5)


def test_kmer_model_actually_runs():
    """Guards the scaler fix: a silent fallback to the heuristic must not return."""
    r = amrpredict.predict_fasta(as_fasta(make_sequence()), 'ciprofloxacin')
    assert r['model_used'] == 'RandomForest K-mer (trained)'
