"""Edge cases for FASTA input.

This is user-supplied data, so it is where malformed input actually arrives.
Each test states the behaviour the library guarantees, so a regression here
fails loudly rather than silently changing what callers get.
"""
import random

import numpy as np
import pytest

import amrpredict
from amrpredict.genome import contigs, genome_counts


def make_sequence(n=3000, seed=7):
    rng = random.Random(seed)
    return ''.join(rng.choice('ACGT') for _ in range(n))


def as_fasta(seq, header='>test_contig', width=70):
    body = '\n'.join(seq[i:i + width] for i in range(0, len(seq), width))
    return f'{header}\n{body}\n'


GENOME = as_fasta(make_sequence(150_000))      # the genome models need >= 100,000 bp


# --- parsing ---------------------------------------------------------------

def test_headers_are_stripped():
    seq = make_sequence(200)
    assert list(contigs(as_fasta(seq))) == [seq.encode()]


def test_each_record_is_its_own_contig():
    """k-mers are counted inside each contig, as in training, never across two."""
    a, b = make_sequence(150, seed=1), make_sequence(150, seed=2)
    assert list(contigs(as_fasta(a) + as_fasta(b, '>second'))) == [a.encode(), b.encode()]
    assert genome_counts(as_fasta(a) + as_fasta(b, '>second'))[2] == 300


def test_lowercase_counts_the_same():
    seq = make_sequence(500)
    up, low = genome_counts(as_fasta(seq)), genome_counts(as_fasta(seq.lower()))
    assert np.array_equal(up[0], low[0]) and up[1:] == low[1:]


def test_non_acgt_characters_are_not_counted():
    """Ambiguity codes count toward nothing and break the k-mers that span them."""
    counts, _, length = genome_counts('>x\nACGTNNNRYKM\nACGT\n')
    assert length == 8
    assert counts.sum() == 0       # no clean 6-mer in ACGTNNNRYKMACGT


def test_sequence_without_a_header_is_accepted():
    assert genome_counts(make_sequence(200))[2] == 200


def test_empty_input_yields_an_empty_genome():
    assert genome_counts('')[2] == 0
    assert genome_counts('>header only\n')[2] == 0


# --- predict_fasta ---------------------------------------------------------

def test_predict_on_a_complete_genome():
    r = amrpredict.predict_fasta(GENOME, 'ciprofloxacin', use_genes=False)
    assert r['prediction'] in ('Resistant', 'Susceptible')
    assert 0.0 <= r['probability'] <= 1.0
    assert r['sequence_length'] == 150_000
    assert 0.0 <= r['gc_content'] <= 100.0
    assert len(r['top_kmers']) == 10
    assert all(len(k['kmer']) == 4 for k in r['top_kmers'])


@pytest.mark.parametrize('bad', ['', '>header only\n', '>x\nACGT\n', 'NNNN' * 50,
                                 as_fasta(make_sequence(50_000))],
                         ids=['empty', 'header-only', '4-bp', 'only-N', '50-kb'])
def test_short_input_reports_an_error_instead_of_raising(bad):
    """Short or empty input returns an error dict; it must never raise."""
    r = amrpredict.predict_fasta(bad, 'ciprofloxacin', use_genes=False)
    assert 'error' in r
    assert 'prediction' not in r


def test_predict_is_deterministic():
    a = amrpredict.predict_fasta(GENOME, 'ciprofloxacin', use_genes=False)['probability']
    b = amrpredict.predict_fasta(GENOME, 'ciprofloxacin', use_genes=False)['probability']
    assert a == b


def test_unknown_antibiotic_is_tolerated():
    r = amrpredict.predict_fasta(GENOME, 'notarealdrug', use_genes=False)
    assert r['prediction'] in ('Resistant', 'Susceptible')
    assert r['antibiotic_known'] is False


def test_the_kmer_model_is_the_lightgbm_one():
    """0.3.0: the k-mer model is the web app's LightGBM (lab AUC 0.935), not
    the July RandomForest (0.695 on new genomes)."""
    r = amrpredict.predict_fasta(GENOME, 'ciprofloxacin', use_genes=False)
    assert r['model_used'].startswith('LightGBM on 4-mers')


def test_gene_model_without_amrfinder_says_so():
    from amrpredict.genome import find_amrfinder
    if find_amrfinder():
        pytest.skip('AMRFinderPlus is installed here')
    r = amrpredict.predict_fasta(GENOME, 'ciprofloxacin', use_genes=True)
    assert 'AMRFinderPlus' in r['error']
    assert 'prediction' in amrpredict.predict_fasta(GENOME, 'ciprofloxacin')


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


def test_timeline_compartments_partition_the_population_throughout():
    """After the susceptible pool is exhausted too (fixed 2026-09-29; the
    library copy once reached 106% by week 8)."""
    r = amrpredict.simulate_timeline(as_fasta(make_sequence()), 'ciprofloxacin', n_weeks=8)
    for w in r['timeline']:
        total = (w['resistant_fraction'] + w['susceptible_fraction']
                 + w['intermediate_fraction'])
        assert total == pytest.approx(100.0, abs=0.5)


def test_timeline_is_repeatable_with_a_seed():
    """Same FASTA, drug and seed: the same response (mutations and types included)."""
    fasta = as_fasta(make_sequence())
    a = amrpredict.simulate_timeline(fasta, 'ciprofloxacin', n_weeks=8, seed=7)
    b = amrpredict.simulate_timeline(fasta, 'ciprofloxacin', n_weeks=8, seed=7)
    assert a == b
    assert a['model_used'] == 'Biological Simulation' and a['simulation'] is True
