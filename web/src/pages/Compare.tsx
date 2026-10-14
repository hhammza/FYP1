/* /compare: the deployed models next to the experiments, what each learned
   from and how it scores on new genomes (frontend/templates/compare.html). */
import { useCallback, useState } from 'react';
import { Link } from 'react-router';
import Plot, { type Figure, type PlotTheme } from '../components/Plot';
import { pyFixed, thousands } from '../lib/metrics';
import { usePageEffects, useTitle } from '../lib/pageEffects';
import type { ModelReport, Run } from '../lib/report';
import { useModelReport } from '../lib/useReport';
import { ReportHeader, ReportUnavailable } from './Models';
import { claimFigure, genusFigure, labelFigure, sizeFigure, type Profile, type Profiles } from './compare/charts';

// the template's macros: n(x) and p(x)
const n = (x: number | undefined) => (typeof x === 'number' ? thousands(x) : '');
const p = (x: number) => `${pyFixed(100 * x, 1)}%`;
const f3 = (x: number) => pyFixed(x, 3);

/** What a run trained on (the template's data_desc macro). */
export function dataDesc(run: Run & { label_sources?: unknown; sample_rows?: number }): string {
  if (run.split === 'species_holdout') return 'All files except Klebsiella';
  if (run.label_sources) return 'Lab-confirmed labels only';
  if (run.sample_rows) return `Random ${Math.trunc(run.sample_rows / 1000)}k-row sample`;
  return 'All 3,655 files';
}

function Chart({ id, report, build, height }: { id: string; report: ModelReport; build: (r: ModelReport, t: PlotTheme) => Figure; height: number }) {
  const figure = useCallback((t: PlotTheme) => build(report, t), [report, build]);
  return <Plot id={id} className="report-chart" style={{ height }} figure={figure} />;
}

const kleb = (prof: Profile) => prof.genus_rows.Klebsiella ?? 0;

function Comparison({ report }: { report: ModelReport }) {
  const tp = report.training_profiles as Profiles;
  const full = tp.full_data!;
  const lg = report.shipped!.lightgbm;
  const km = report.shipped!.kmer;
  const lgp = lg.train_profile as Profile;
  const kmp = km.train_profile as Profile;
  const sv = (report.shipped_versions || {}) as Record<string, string | undefined>;
  const best = report.runs.find(r => r.id === report.best_run)!;
  const bp = tp[report.best_run]!;
  const kmName = km.short_name || 'K-mer RF';
  const lgSource = sv.lightgbm ? `BV-BRC export, cleaning ${sv.lightgbm}` : `amr_output/, files 1 to ${lg.files_used}`;
  const kmSource = km.run_id ? String(km.source) : `mapped_output/, files 1 to ${km.files_used}`;
  const genomesWithFasta = Number(km.genomes_with_fasta);

  return (
    <>
      {/* ── Headline contrast ────────────────────────────────────── */}
      <div className="row g-3 mb-4">
        <div className="col-6 col-lg-3"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static text-indigo2">{pyFixed(bp.rows / lgp.rows, 0)}×</div>
          <div className="stat-mini-label">More training rows in {best.id} than the deployed LightGBM</div>
        </div></div>
        <div className="col-6 col-lg-3"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">{lgp.genera} vs {bp.genera}</div>
          <div className="stat-mini-label">Bacterial genera seen: deployed vs best experiment</div>
        </div></div>
        <div className="col-6 col-lg-3"><div className="stat-mini">
          <div className="stat-mini-value">{p(kleb(lgp) / lgp.rows)}</div>
          <div className="stat-mini-label">Klebsiella in deployed training data ({p((full.genus_rows.Klebsiella ?? 0) / full.rows)} of all data)</div>
        </div></div>
        <div className="col-6 col-lg-3"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">{f3(lg.results[1].auc_roc)} vs {f3(best.auc_roc)}</div>
          <div className="stat-mini-label">AUC on new genomes: deployed vs best experiment</div>
        </div></div>
      </div>

      {/* ── Section 1: where the data comes from ───────────────── */}
      <div className="mb-5">
        <div className="sec-eyebrow">Section 1</div>
        <h2 className="sec-title">Where each model's training data comes from</h2>
        <p className="sec-sub mb-4">
          All data comes from BV-BRC / PATRIC: the resistance table for the forecaster, and complete genome
          assemblies for the genome model.
        </p>
        <div className="glass-card">
          <div className="flow-lane">
            <div className="flow-source">
              <div className="flow-source-name"><i className="bi bi-folder2-open me-2"></i>BV-BRC AMR export</div>
              <div className="flow-source-meta">complete, cleaning {report.clean_version || 'v7'}</div>
              <div className="flow-source-meta">{n(full.rows)} rows after cleaning</div>
              <div className="flow-source-meta">{n(full.genomes)} genomes, {full.genera} genera</div>
            </div>
            <div className="flow-arrow"><i className="bi bi-arrow-right"></i></div>
            <div className="flow-targets">
              <div className="flow-target deployed">
                <div className="flow-target-head"><span className="flow-dot deployed"></span>Deployed LightGBM <span className="caption-text ms-1">/forecast</span></div>
                <div className="flow-target-meta">{n(lgp.rows)} training rows{sv.lightgbm && ` (cleaning ${sv.lightgbm})`}</div>
                <div className="flow-meter"><div className="flow-meter-fill deployed" style={{ width: `${Math.max(100 * lgp.rows / full.rows, 0.6)}%` }}></div></div>
                <div className="caption-text">{p(lgp.rows / full.rows)} of the available rows</div>
              </div>
              <div className="flow-target experiment">
                <div className="flow-target-head"><span className="flow-dot experiment"></span>Experiments <span className="caption-text ms-1">A0 to A12, learning curves</span></div>
                <div className="flow-target-meta">The whole export → up to {n(full.rows)} rows, 80% for training</div>
                <div className="flow-meter"><div className="flow-meter-fill experiment" style={{ width: '100%' }}></div></div>
                <div className="caption-text">100% of the available rows (some runs sample or filter, see the table below)</div>
              </div>
            </div>
          </div>

          <div className="flow-lane mt-4">
            <div className="flow-source">
              <div className="flow-source-name"><i className="bi bi-folder2-open me-2"></i>{km.run_id ? 'Complete genome assemblies' : 'mapped_output/ + fasta_output/'}</div>
              <div className="flow-source-meta">{n(Number(km.files_total))} {km.run_id ? 'complete genome assemblies' : 'CSVs joined to genome files'}</div>
              <div className="flow-source-meta">{n(genomesWithFasta)} genomes with a FASTA assembly</div>
              {!km.run_id && <div className="flow-source-meta">About 4 GB of sequence</div>}
            </div>
            <div className="flow-arrow"><i className="bi bi-arrow-right"></i></div>
            <div className="flow-targets">
              <div className="flow-target deployed">
                <div className="flow-target-head"><span className="flow-dot deployed"></span>Deployed {kmName} <span className="caption-text ms-1">/predict</span></div>
                <div className="flow-target-meta">{km.run_id ? `${n(Number(km.files_used))} training genomes` : `Files 1 to ${km.files_used}`} → {n(kmp.rows)} rows from {n(kmp.genomes)} genomes</div>
                <div className="flow-meter"><div className="flow-meter-fill deployed" style={{ width: `${100 * kmp.genomes / genomesWithFasta}%` }}></div></div>
                <div className="caption-text">{p(kmp.genomes / genomesWithFasta)} of the genomes with a FASTA</div>
              </div>
              {report.genome_runs?.length ? (
                <div className="flow-target experiment">
                  <div className="flow-target-head"><span className="flow-dot experiment"></span>Experiments <span className="caption-text ms-1">genes, k-mers, lineage splits</span></div>
                  <div className="flow-target-meta">{report.genome_runs.length} genome runs, scored on lab results: <Link to="/models#genome">Model Report, Section 5</Link></div>
                </div>
              ) : (
                <div className="flow-target empty">
                  <div className="flow-target-head"><span className="flow-dot"></span>Experiments</div>
                  <div className="flow-target-meta">No genome-sequence experiment yet. All experiments use the tabular AMR data.</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 2: side by side ─────────────────────────────── */}
      <div className="mb-5">
        <div className="sec-eyebrow">Section 2</div>
        <h2 className="sec-title">Side by side</h2>
        <p className="sec-sub mb-4">The two models the app serves today, next to the best experimental model.</p>
        <div className="glass-card">
          <div className="table-responsive">
            <table className="table table-custom mb-0 compare-table">
              <thead>
                <tr>
                  <th></th>
                  <th><span className="flow-dot deployed"></span>Deployed LightGBM</th>
                  <th><span className="flow-dot deployed"></span>Deployed {kmName}</th>
                  <th><span className="flow-dot experiment"></span>Best experiment ({best.id})</th>
                </tr>
              </thead>
              <tbody>
                <tr className="compare-section"><td colSpan={4}>Model</td></tr>
                <tr><td>Status</td>
                  <td>Serves <Link to="/forecast">/forecast</Link></td>
                  <td>Loaded for <Link to="/predict">/predict</Link>, but never runs (heuristic fallback)</td>
                  <td>Experiment, not deployed yet</td></tr>
                <tr><td>Algorithm</td>
                  <td>LightGBM, {lg.trees} trees</td>
                  <td>{(km.algorithm as string) || `Random forest, ${km.trees} trees`}</td>
                  <td>LightGBM, {report.best.model_info.n_trees} trees</td></tr>
                <tr><td>What it reads</td>
                  <td>Antibiotic, organism, MIC, resistance-rate lookups</td>
                  <td>4-letter DNA word frequencies of the genome, plus antibiotic and GC content</td>
                  <td>Same inputs as the deployed LightGBM ({report.best.features.length} features)</td></tr>

                <tr className="compare-section"><td colSpan={4}>Training data</td></tr>
                <tr><td>Source</td>
                  <td className="font-mono small">{lgSource}</td>
                  <td className="font-mono small">{kmSource}</td>
                  <td className="font-mono small">amr_full/, the complete export (cleaning {report.clean_version || 'v7'})</td></tr>
                <tr><td>Training rows</td>
                  <td className="font-mono">{n(lgp.rows)}</td><td className="font-mono">{n(kmp.rows)}</td>
                  <td className="font-mono">{n(bp.rows)} <span className="caption-text">incl. validation</span></td></tr>
                <tr><td>Genomes</td>
                  <td className="font-mono">{n(lgp.genomes)}</td><td className="font-mono">{n(kmp.genomes)}</td><td className="font-mono">{n(bp.genomes)}</td></tr>
                <tr><td>Genera / taxa</td>
                  <td className="font-mono">{lgp.genera} / {n(lgp.taxa)}</td><td className="font-mono">{kmp.genera} / {n(kmp.taxa)}</td><td className="font-mono">{bp.genera} / {n(bp.taxa)}</td></tr>
                <tr><td>Antibiotics</td>
                  <td className="font-mono">{lgp.antibiotics}</td><td className="font-mono">{kmp.antibiotics}</td><td className="font-mono">{bp.antibiotics}</td></tr>
                <tr><td>Klebsiella rows</td>
                  <td className="font-mono">{n(kleb(lgp))}</td><td className="font-mono">{n(kleb(kmp))}</td><td className="font-mono">{n(kleb(bp))}</td></tr>
                <tr><td>Resistant share</td>
                  <td className="font-mono">{p(lgp.prevalence)}</td><td className="font-mono">{p(kmp.prevalence)}</td><td className="font-mono">{p(bp.prevalence)}</td></tr>
                <tr><td>Lab-confirmed labels</td>
                  <td className="font-mono">{p(lgp.lab_share)}</td><td className="font-mono">{p(kmp.lab_share)}</td><td className="font-mono">{p(bp.lab_share)}</td></tr>

                <tr className="compare-section"><td colSpan={4}>How it was tested</td></tr>
                <tr><td>Split</td>
                  <td>Random rows, 80/20</td><td>Random rows, 80/20</td><td>By genome, 80/20</td></tr>
                <tr><td>Resistance-rate features</td>
                  <td>Fitted on all rows, test rows included</td><td>Not used</td><td>Fitted out of fold, training rows only</td></tr>
                <tr><td>Test genomes also in training</td>
                  <td>Most (same genome, other antibiotics)</td><td>Most (identical k-mer vector)</td><td className="font-mono">{bp.shared_genomes}</td></tr>

                <tr className="compare-section"><td colSpan={4}>Results</td></tr>
                <tr><td>AUC as originally reported</td>
                  <td className="font-mono">{lg.claimed_auc}</td><td className="font-mono">{km.claimed_auc}</td><td className="font-mono">{f3(best.auc_roc)}</td></tr>
                <tr><td>AUC on genomes never seen</td>
                  <td className="font-mono fw-700">{f3(lg.results[1].auc_roc)}</td>
                  <td className="font-mono fw-700">{f3(km.results[1].auc_roc)}</td>
                  <td className="font-mono fw-700 text-indigo2">{f3(best.auc_roc)}</td></tr>
                <tr><td>Resistant isolates missed (VME)</td>
                  <td className="font-mono">{pyFixed(100 * lg.results[1].very_major_error, 0)}%</td>
                  <td className="font-mono">{pyFixed(100 * km.results[1].very_major_error, 0)}%</td>
                  <td className="font-mono">{pyFixed(100 * best.very_major_error, 0)}%</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── Section 3: the training data, compared ──────────────── */}
      <div className="mb-5">
        <div className="sec-eyebrow">Section 3</div>
        <h2 className="sec-title">The training data, compared</h2>
        <p className="sec-sub mb-4">Size, organism mix and label mix of every training set, and what each model scores as a result.</p>
        <div className="row g-4 mb-4">
          <div className="col-lg-6">
            <div className="glass-card h-100">
              <h6 className="card-section-title mb-1"><i className="bi bi-database text-accent me-2"></i>Training set size</h6>
              <p className="small text-muted mb-2">Rows each model learned from. Log scale: every gridline is 10 times more data.</p>
              <Chart id="sizeChart" report={report} build={sizeFigure} height={420} />
            </div>
          </div>
          <div className="col-lg-6">
            <div className="glass-card h-100">
              <h6 className="card-section-title mb-1"><i className="bi bi-arrow-down-right text-accent me-2"></i>Reported AUC vs AUC on new genomes</h6>
              <p className="small text-muted mb-2">Experiments are already tested on unseen genomes, so their two dots sit on top of each other.</p>
              <Chart id="claimChart" report={report} build={claimFigure} height={420} />
            </div>
          </div>
        </div>
        <div className="glass-card mb-4">
          <h6 className="card-section-title mb-1"><i className="bi bi-grid-3x3 text-accent me-2"></i>Which bacteria each model learned from</h6>
          <p className="small text-muted mb-2">
            Share of training rows per genus. The deployed models learned almost only from <em>Escherichia</em> and{' '}
            <em>Salmonella</em> and never saw <em>Klebsiella</em>, the largest genus in the data.
          </p>
          <Chart id="genusChart" report={report} build={genusFigure} height={520} />
        </div>
        <div className="glass-card">
          <h6 className="card-section-title mb-1"><i className="bi bi-tags text-accent me-2"></i>Label mix</h6>
          <p className="small text-muted mb-2">
            The deployed LightGBM learned from data that is {p(lgp.prevalence)} resistant, against {p(full.prevalence)} overall,
            so it expects resistance to be rarer than it is. The K-mer model has no lab-confirmed labels at all.
          </p>
          <Chart id="labelChart" report={report} build={labelFigure} height={380} />
        </div>
      </div>

      {/* ── Section 4: every model and its data ─────────────────── */}
      <div className="mb-5">
        <div className="sec-eyebrow">Section 4</div>
        <h2 className="sec-title">Every model and its data</h2>
        <p className="sec-sub mb-4">All deployed and experimental models. Training rows include the validation slice.</p>
        <div className="glass-card">
          <div className="table-responsive">
            <table className="table table-custom table-sm mb-0">
              <thead><tr><th>Model</th><th>Type</th><th>Algorithm</th><th>Trained on</th><th>Train rows</th><th>Genomes</th><th>Genera</th><th>Resistant</th><th>Lab labels</th><th>Split</th><th>AUC, new genomes</th></tr></thead>
              <tbody>
                {([[lg, lgp, 'lightgbm', sv.lightgbm ? `BV-BRC export, cleaning ${sv.lightgbm}` : `amr_output files 1 to ${lg.files_used}`],
                   [km, kmp, km.run_id ? 'lightgbm' : 'random_forest', km.run_id ? String(km.source) : `mapped_output files 1 to ${km.files_used}`]] as const)
                  .map(([m, prof, algo, src]) => (
                  <tr key={m.name}>
                    <td><span className="text-white fw-600">{m.name}</span><div className="caption-text">{m.page}</div></td>
                    <td className="text-nowrap"><span className="flow-dot deployed"></span>Deployed</td>
                    <td className="small">{algo}</td>
                    <td className="small">{src}</td>
                    <td className="font-mono small">{n(prof.rows)}</td>
                    <td className="font-mono small">{n(prof.genomes)}</td>
                    <td className="font-mono small">{prof.genera}</td>
                    <td className="font-mono small">{p(prof.prevalence)}</td>
                    <td className="font-mono small">{p(prof.lab_share)}</td>
                    <td className="small">random</td>
                    <td className="font-mono small">{f3(m.results[1].auc_roc)}</td>
                  </tr>
                ))}
                {report.runs.map(run => {
                  const prof = tp[run.id];
                  return (
                    <tr key={run.id} className={run.id === report.best_run ? 'report-best-row' : undefined}>
                      <td><span className="font-mono small text-white">{run.id}</span><div className="caption-text">{run.description}</div></td>
                      <td className="text-nowrap"><span className="flow-dot experiment"></span>Experiment</td>
                      <td className="small">{run.model}</td>
                      <td className="small">{dataDesc(run)}</td>
                      <td className="font-mono small">{n(prof?.rows)}</td>
                      <td className="font-mono small">{n(prof?.genomes)}</td>
                      <td className="font-mono small">{prof?.genera}</td>
                      <td className="font-mono small">{prof ? p(prof.prevalence) : ''}</td>
                      <td className="font-mono small">{prof ? p(prof.lab_share) : ''}</td>
                      <td className="small">{run.split}</td>
                      <td className="font-mono small">{f3(run.auc_roc)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="caption-text mt-2 mb-0">
            A0 and A1 use a random split, so some of their test genomes were also in training. Every other experiment keeps test genomes out of training.
            The deployed models' AUC comes from <code>experiments/evaluate_shipped.py</code>, on genomes outside the files they read.
          </p>
        </div>
      </div>

      <div className="alert-info-custom">
        <i className="bi bi-lightbulb me-2"></i>
        <strong>Bottom line.</strong> The deployed models are weaker mainly because of their data, not their algorithm:
        they learned from {p(lgp.rows / full.rows)} and {p(kmp.genomes / genomesWithFasta)} of what was available, from a narrow set of bacteria,
        and were scored on genomes they had already seen. Trained on all the data and tested fairly, the same LightGBM algorithm reaches{' '}
        {f3(best.auc_roc)}. See the <Link to="/models">Model Report</Link> for how the split works.
      </div>
    </>
  );
}

export default function Compare() {
  useTitle('Model Comparison');
  const report = useModelReport();
  const [root, setRoot] = useState<HTMLDivElement | null>(null);
  usePageEffects(root, [report.state]);
  const ready = report.state === 'ready' && report.report.shipped && report.report.training_profiles;
  return (
    <>
      <ReportHeader title="Deployed vs Experimental Models" icon="layout-split" crumb="Comparison"
                    parent={{ to: '/models', label: 'Model Report' }}
                    subtitle="What each model learned from, how it was tested, and how it scores on genomes it has never seen" />
      <div className="container-xl py-4" ref={setRoot}>
        {ready ? <Comparison report={report.report} />
          : report.state === 'loading' ? <ReportUnavailable />
          : (
            <div className="empty-state">
              <div className="empty-state-icon"><i className="bi bi-clipboard-x"></i></div>
              <h5 className="fw-700">Comparison not available</h5>
              <p className="text-muted mb-0">{report.state === 'failed' ? report.error
                : 'The report has no training-data profiles yet. Run: python experiments/evaluate_shipped.py, then python experiments/export_report.py'}</p>
            </div>
          )}
      </div>
    </>
  );
}
