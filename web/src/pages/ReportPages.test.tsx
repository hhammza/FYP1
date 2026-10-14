import { fireEvent, screen, within } from '@testing-library/react';
import Compare, { dataDesc } from './Compare';
import Genes, { linkedGenome } from './Genes';
import Models from './Models';
import Train, { reloadSummary } from './Train';
import { demoRows } from './models/GenomeDemo';
import { geneTitle, wrapLabel } from './genes/charts';
import { shownGenomeRuns, type GenomeRun, type ModelReport, type Run } from '../lib/report';
import { HEALTH, mockBackend, renderPage } from '../test-utils';

vi.mock('plotly.js-dist-min', () => ({ default: { react: vi.fn(), purge: vi.fn(), toImage: vi.fn(async () => '') } }));

afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); });

const run = (id: string, extra: Partial<Run> = {}): Run => ({
  id, rows: 1000, test_rows: 200, auc_roc: 0.785, auc_ci: [0.77, 0.80], auc_pr: 0.6, f1: 0.55,
  very_major_error: 0.1, major_error: 0.2325, threshold: 0.4, model: 'lightgbm', split: 'grouped', ...extra,
});
const result = (subset: string, auc: number) => ({ subset, rows: 5000, auc_roc: auc, auc_ci: [auc - 0.01, auc + 0.01] as [number, number],
                                                    very_major_error: 0.1, major_error: 0.3, roc: { fpr: [0, 1], tpr: [0, 1] } });
const profile = (rows: number) => ({ rows, genomes: rows / 10, genera: 4, taxa: 30, antibiotics: 20, prevalence: 0.3,
                                     lab_share: 0.2, mic_share: 0.5, shared_genomes: 0, genus_rows: { Klebsiella: rows / 4, Escherichia: rows / 2 } });

const REPORT: ModelReport = {
  generated_at: '2026-10-01T10:00:00', best_run: 'A2_oof_grouped', clean_version: 'v7',
  runs: [run('A2_oof_grouped', { group: 'baseline' }), run('A3_logistic', { auc_roc: 0.765, group: 'algorithm' }),
         run('A6b_lab_only_no_mic', { auc_roc: 0.701 })],
  split: { strategies: { grouped: { train_genomes: 800, test_genomes: 200, shared_genomes: 0, test_rows_from_seen_genomes: 0, train_prevalence: 0.31, test_prevalence: 0.3 },
                         random: { train_genomes: 990, test_genomes: 600, shared_genomes: 590, test_rows_from_seen_genomes: 0.98, train_prevalence: 0.3, test_prevalence: 0.3 } },
           total_rows: 1_000_000, total_genomes: 1000, rows_per_genome: 25, fit_rows: 640_000, validation_rows: 160_000, test_rows: 200_000,
           encoding_folds: 5, validation_folds: 4 },
  best: { id: 'A2_oof_grouped', model_info: { kind: 'LightGBM', n_trees: 500 }, features: Array(14).fill('f'),
          confusion: { tn: 100, fp: 20, fn: 10, tp: 70 },
          test: { threshold: 0.4, major_error: 0.17, very_major_error: 0.12, sensitivity: 0.88, specificity: 0.83 },
          per_antibiotic_best: [], per_antibiotic_worst: [], per_antibiotic_count: 40 },
  roc: {},
  shipped: {
    lightgbm: { name: 'Deployed LightGBM forecaster', page: '/forecast', trees: 300, known_antibiotics: 126, train_rows: 6_000_000,
                train_genomes: 20000, claimed_auc: 0.7737, split: 'grouped', results: [result('Seen', 0.94), result('Never seen', 0.762)],
                train_profile: profile(30_000), files_used: 10 },
    kmer: { name: 'Genome model', short_name: 'K-mer LightGBM', page: '/predict', run_id: 'G_kmer_deploy', trees: 400, known_antibiotics: 60,
            train_rows: 200_000, train_genomes: 15000, claimed_auc: 0.9345, split: 'grouped', within_antibiotic_auc: 0.81,
            results: [result('Seen', 0.97), result('Never seen', 0.934), result('Drug only', 0.66)],
            train_profile: profile(200_000), files_used: 15000, files_total: 24926, genomes_with_fasta: 24926, source: 'genomes_full/' },
  },
  genome_runs: [
    { id: 'B6L_genes_v6', clean_version: 'v6', label_version: 'v6', auc_roc_lab: 0.97, split: 'lineage' },
    { id: 'B6L_genes_v7', clean_version: 'v7', label_version: 'v6', auc_roc_lab: 0.977, split: 'lineage' },
    { id: 'G_kmer_deploy', clean_version: 'v6', label_version: 'v6', auc_roc_lab: 0.934, split: 'grouped', n_lab: 12000 },
    { id: 'old_run', clean_version: 'v5', label_version: 'v5', auc_roc_lab: 0.9 },
    { id: 'no_lab', clean_version: 'v6', label_version: 'v6', auc_roc_lab: null },
  ],
  insights: [{ icon: 'trophy', title: 'A finding', text: 'Text of the finding.', evidence: 'Section 3' }],
  training_profiles: { full_data: profile(1_000_000), A2_oof_grouped: profile(1_000_000), A3_logistic: profile(400_000) },
  shipped_versions: { lightgbm: 'v7', kmer: 'v6' },
};

describe('report helpers', () => {
  it('shows the newest genome runs with a lab score, a re-run once', () => {
    const { runs, version, hasV7 } = shownGenomeRuns(REPORT.genome_runs as GenomeRun[]);
    expect(version).toBe('v6');
    expect(runs.map(r => r.id)).toEqual(['B6L_genes_v7', 'G_kmer_deploy']);
    expect(hasV7).toBe(true);
    expect(shownGenomeRuns(null).runs).toEqual([]);
  });

  it('draws the same genome split illustration as models.js', () => {
    const grouped = demoRows('grouped');
    expect(grouped.map(r => r.every(Boolean))).toEqual([false, true, false, false, true, false]);
    const random = demoRows('random');
    expect(random.some(r => r.some(Boolean) && !r.every(Boolean))).toBe(true);    // genomes on both sides
    expect(demoRows('random')).toEqual(random);                                     // seeded, the same every time
  });

  it('names what each run trained on', () => {
    expect(dataDesc(run('A12', { split: 'species_holdout' }))).toBe('All files except Klebsiella');
    expect(dataDesc({ ...run('A6'), label_sources: ['lab'] })).toBe('Lab-confirmed labels only');
    expect(dataDesc({ ...run('LC'), sample_rows: 50_000 })).toBe('Random 50k-row sample');
    expect(dataDesc(run('A2'))).toBe('All 3,655 files');
  });

  it('titles AMRFinderPlus classes and wraps long ones', () => {
    expect(geneTitle('BETA-LACTAM')).toBe('Beta-Lactam');
    expect(geneTitle('AMINOGLYCOSIDE/QUINOLONE')).toBe('Aminoglycoside/Quinolone');
    expect(wrapLabel('Aminoglycoside/Quinolone/Phenicol')).toBe('Aminoglycoside/<br>Quinolone/Phenicol');
    expect(wrapLabel('Beta-Lactam')).toBe('Beta-Lactam');
  });

  it('reads a /genes#genome= link', () => {
    expect(linkedGenome('#genome=1000561.3')).toBe('1000561.3');
    expect(linkedGenome('#lookup')).toBe('');
  });

  it('summarises a reload as train.js did', () => {
    expect(reloadSummary({ lgbm: { trained: true }, timeline: { trained: false } }))
      .toBe('lgbm: ✅ Trained  |  timeline: ⚠️ Heuristic');
  });
});

describe('/models', () => {
  it('shows the report, rounding as Python did', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'models/': { body: REPORT } });
    renderPage(<Models />, '/models');
    expect(await screen.findByText('How we split train and test')).toBeInTheDocument();
    expect(screen.getAllByText('23.2%').length).toBeGreaterThan(0);     // ME 0.2325: Python's tie to even
    expect(screen.getByText('A finding')).toBeInTheDocument();
    expect(screen.getByText(/Without MIC \(A6b\) it drops to 0\.701/)).toBeInTheDocument();
    expect(screen.getByText(/These 2 runs read the genome itself/)).toBeInTheDocument();
    const served = screen.getByText('Served').closest('tr')!;
    expect(within(served).getByText(/G_kmer_deploy/)).toBeInTheDocument();
    for (const id of ['seenChart', 'aucChart', 'rocChart', 'learningChart', 'errorChart', 'drugChart', 'genomeChart']) {
      expect(document.getElementById(id)).not.toBeNull();
    }
  });

  it('says why when the report is missing', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'models/': { status: 404, body: { error: 'model_report.json not found: run experiments/export_report.py' } } });
    renderPage(<Models />, '/models');
    expect(await screen.findByText('Report not available')).toBeInTheDocument();
    expect(screen.getByText(/export_report\.py/)).toBeInTheDocument();
  });
});

describe('/compare', () => {
  it('compares the deployed models with the best experiment', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'models/': { body: REPORT } });
    renderPage(<Compare />, '/compare');
    expect(await screen.findByText('Side by side')).toBeInTheDocument();
    expect(screen.getByText('33×')).toBeInTheDocument();                  // 1,000,000 / 30,000, rounded
    expect(screen.getByText('0.762 vs 0.785')).toBeInTheDocument();
    const crumb = document.querySelector('.breadcrumb')!;
    expect(within(crumb as HTMLElement).getByRole('link', { name: 'Model Report' })).toHaveAttribute('href', '/models');
  });

  it('explains a report without training profiles', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'models/': { body: { ...REPORT, training_profiles: undefined } } });
    renderPage(<Compare />, '/compare');
    expect(await screen.findByText('Comparison not available')).toBeInTheDocument();
    expect(screen.getByText(/evaluate_shipped\.py/)).toBeInTheDocument();
  });
});

const GENES = {
  run: { generated_at: '2026-09-28T11:52:59', git_commit: '97897d9', amrfinder_version: '4.2.7', database_version: '2026-08-07.1',
         genomes_downloaded: 100, genomes_searched: 100, complete: true, filter: 'Scope = core, Type = AMR' },
  summary: { genomes: 100, with_gene: 92, symbols: 30, genes: 20, point_mutations: 10, median_genes: 9.0, max_genes: 37 },
  matrix: { genomes: 100, symbols: 30, cells: 3000, ones: 300,
            preview: { genes: ['fosA', 'sul1'], rows: [{ genome: '1037890.3', species: 'Klebsiella pneumoniae', values: [1, 0], total: 5 }] } },
  genes_per_genome: [{ genes: 0, genomes: 8, capped: false }],
  top_genes: [{ gene: 'fosA', type: 'gene', class: 'FOSFOMYCIN', subclass: 'FOSFOMYCIN', genomes: 30, share: 0.3 }],
  classes: [{ class: 'BETA-LACTAM', genomes: 80, share: 0.8, symbols: 15 }],
  genera: [{ genus: 'Klebsiella', genomes: 60, with_gene: 0.9977, median_genes: 16.0, top: [{ gene: 'fosA', share: 0.9284 }] }],
  heatmap: { genera: ['Klebsiella'], genes: ['fosA'], share: [[0.93]], min_genomes: 50 },
  gene_vs_lab: {
    lab: { min_carriers: 20, pairs_total: 14, genomes_labelled: 1500,
           pairs: Array.from({ length: 14 }, (_, i) => ({ gene: `g${i}`, gene_subclass: 'QUINOLONE', antibiotic: 'ciprofloxacin',
                                                         carriers: 100, carriers_resistant: 0.9, others: 400, others_resistant: null })) },
    all: { min_carriers: 20, pairs_total: 1, genomes_labelled: 20000,
           pairs: [{ gene: 'blaCTX-M-15', antibiotic: 'ceftriaxone', carriers: 5, carriers_resistant: 0.8, others: 9, others_resistant: 0.1 }] },
  },
};

describe('/genes', () => {
  it('shows the gene report and switches the labels compared', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'genes/': { body: GENES } });
    renderPage(<Genes />, '/genes');
    expect(await screen.findByText('What was found')).toBeInTheDocument();
    expect(screen.getByText('92.0%')).toBeInTheDocument();
    expect(screen.getByText('9')).toBeInTheDocument();                    // '%g' of 9.0
    expect(screen.getByText(/Gene matrix \(CSV/).closest('a')).toHaveAttribute('href', '/api/genes/matrix.csv');
    const table = document.getElementById('labTable')!;
    expect(within(table).getAllByRole('row')).toHaveLength(1 + 12);       // the first 12 pairs
    fireEvent.click(screen.getByRole('button', { name: 'Show all 14' }));
    expect(within(table).getAllByRole('row')).toHaveLength(1 + 14);
    fireEvent.click(screen.getByRole('button', { name: /Include BV-BRC predictions \(20,000 genomes\)/ }));
    expect(document.getElementById('compNote')).not.toHaveClass('d-none');
    expect(within(table).getByText('blaCTX-M-15')).toBeInTheDocument();
  });

  it('looks up a genome from a #genome= link', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'genes/': { body: GENES }, 'genes/1000561.3/': { body: {
      genome_id: '1000561.3', searched: true, species: 'Pseudomonas aeruginosa',
      genes: [{ gene: 'gyrA_T83I', name: 'quinolone resistant GyrA', type: 'point_mutation', class: 'QUINOLONE', subclass: 'QUINOLONE', identity: 99.89, coverage: 100, method: 'POINTX' }] } } });
    Element.prototype.scrollIntoView = vi.fn();
    renderPage(<Genes />, '/genes#genome=1000561.3');
    expect(await screen.findByText('gyrA_T83I')).toBeInTheDocument();
    expect(screen.getByLabelText('Genome ID')).toHaveValue('1000561.3');
    expect(screen.getByText('Mutation')).toBeInTheDocument();
    expect(screen.getByText('99.9%')).toBeInTheDocument();
  });
});

describe('/train', () => {
  it('asks for the password, then sends it as X-Admin-Token', async () => {
    const calls = mockBackend({ 'health/': { body: HEALTH }, 'train/': { body: { status: 'Training started', message: 'Saved to candidates/.' } } });
    renderPage(<Train />, '/train');
    fireEvent.click(screen.getByRole('button', { name: /Train LightGBM Model/ }));
    expect(await screen.findByText('Enter the admin password first.')).toBeInTheDocument();
    expect(calls.some(c => c.url.endsWith('/train/'))).toBe(false);
    fireEvent.change(screen.getByLabelText(/Admin password/), { target: { value: 'secret' } });
    fireEvent.click(screen.getByRole('button', { name: /Train K-mer Model/ }));
    expect(await screen.findByText('Training started')).toBeInTheDocument();
    const call = calls.find(c => c.url.endsWith('/train/'))!;
    expect(JSON.parse(String(call.init?.body))).toEqual({ model: 'kmer' });
    expect((call.init?.headers as Record<string, string>)['X-Admin-Token']).toBe('secret');
  });

  it('shows a refused reload', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'reload/': { status: 401, body: { error: 'Admin token missing or wrong.' } } });
    renderPage(<Train />, '/train');
    fireEvent.click(screen.getByRole('button', { name: /Reload All Models/ }));
    expect((await screen.findAllByText('Admin token missing or wrong.')).length).toBeGreaterThan(0);
  });
});
