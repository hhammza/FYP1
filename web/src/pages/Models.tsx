/* /models: every model we trained, how the data was split for testing, and
   how each one scores on genomes it never saw (frontend/templates/models.html;
   the data is /api/models/, built by experiments/export_report.py). */
import { useCallback, useState, type ReactNode } from 'react';
import { Link } from 'react-router';
import Plot, { type Figure, type PlotTheme } from '../components/Plot';
import { pyFixed, thousands } from '../lib/metrics';
import { usePageEffects, useTitle } from '../lib/pageEffects';
import { shownGenomeRuns, type ModelReport, type ShippedModel } from '../lib/report';
import { useModelReport } from '../lib/useReport';
import GenomeDemo from './models/GenomeDemo';
import { aucFigure, drugFigure, errorFigure, genomeFigure, learningFigure, rocFigure, seenFigure } from './models/charts';

// the template's '%.3f' etc., rounded as Python rounds
const f3 = (x: number) => pyFixed(x, 3);
const f2 = (x: number) => pyFixed(x, 2);
const p0 = (x: number) => pyFixed(100 * x, 0);
const p1 = (x: number) => pyFixed(100 * x, 1);

/** A report chart: drawn from the report, redrawn with the theme. */
function Chart({ id, report, build, height }: {
  id: string; report: ModelReport; build: (r: ModelReport, t: PlotTheme) => Figure; height: number;
}) {
  const figure = useCallback((t: PlotTheme) => build(report, t), [report, build]);
  return <Plot id={id} className="report-chart" style={{ height }} figure={figure} />;
}

export function ReportHeader({ title, subtitle, icon, crumb, parent }: {
  title: string; subtitle: string; icon: string;
  /** the breadcrumb's last item, when not the title */
  crumb?: string;
  /** a page between the Dashboard and this one */
  parent?: { to: string; label: string };
}) {
  return (
    <div className="page-header">
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          {parent && <li className="breadcrumb-item"><Link to={parent.to}>{parent.label}</Link></li>}
          <li className="breadcrumb-item active">{crumb ?? title}</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon"><i className={`bi bi-${icon}`}></i></div>
          <div>
            <h1 className="page-title">{title}</h1>
            <p className="page-subtitle">{subtitle}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

/** The report's place while it loads, or why it is missing. */
export function ReportUnavailable({ error }: { error?: string }) {
  if (!error) {
    return (
      <div className="empty-state">
        <div className="spinner-border text-accent mb-3" role="status"></div>
        <p className="text-muted mb-0">Loading the report…</p>
      </div>
    );
  }
  return (
    <div className="empty-state">
      <div className="empty-state-icon"><i className="bi bi-clipboard-x"></i></div>
      <h5 className="fw-700">Report not available</h5>
      <p className="text-muted mb-0">{error}</p>
    </div>
  );
}

function Stat({ value, label, cls = '' }: { value: ReactNode; label: string; cls?: string }) {
  return (
    <div className="flex-fill min-w-130"><div className="stat-mini">
      <div className={'stat-mini-value' + (cls ? ' ' + cls : '')}>{value}</div>
      <div className="stat-mini-label">{label}</div>
    </div></div>
  );
}

function DeployedCard({ m, which, icon, report }: { m: ShippedModel; which: 'lightgbm' | 'kmer'; icon: string; report: ModelReport }) {
  return (
    <div className="col-lg-6">
      <div className="info-card h-100">
        <h6 className="card-section-title"><i className={`bi bi-${icon} text-accent me-2`}></i>{m.name}{' '}
          <Link to={m.page} className="small ms-1">{m.page}</Link></h6>
        <div className="table-responsive">
          <table className="table table-custom table-sm mb-2">
            <thead><tr><th>Tested on</th><th>Rows</th><th>AUC [95% CI]</th><th>VME</th><th>ME</th></tr></thead>
            <tbody>
              {m.results.map(row => (
                <tr key={row.subset}><td className="small">{row.subset}</td><td className="font-mono small">{thousands(row.rows)}</td>
                  <td className="font-mono small text-nowrap">{f3(row.auc_roc)}<div className="caption-text">{f3(row.auc_ci[0])} to {f3(row.auc_ci[1])}</div></td>
                  <td className="font-mono small">{p0(row.very_major_error)}%</td>
                  <td className="font-mono small">{p0(row.major_error)}%</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <ul className="small text-muted mb-0 ps-3">
          <li>Trained on {thousands(m.train_rows)} rows from {thousands(m.train_genomes)} genomes, {m.trees} trees, {m.known_antibiotics} antibiotics.</li>
          <li>Quoted AUC {m.claimed_auc}; split: {m.split}.</li>
          {which === 'lightgbm' && m.head_to_head_a2 && (
            <>
              <li>Same {thousands(m.head_to_head_a2.rows)} test rows: deployed {f3(m.head_to_head_a2.shipped_auc)} vs {report.best_run} <strong>{f3(m.head_to_head_a2.a2_auc)}</strong>.</li>
              <li>Only knows {m.known_genera?.length ?? 0} genera: {(m.known_genera || []).join(', ')}.</li>
            </>
          )}
          {which === 'kmer' && (
            <>
              {m.within_antibiotic_auc !== undefined && (m.run_id
                ? <li>Within a single antibiotic the lab AUC averages {f2(m.within_antibiotic_auc)}, so the genome itself carries the signal, not just knowing the drug (drug-only baseline {m.results.length > 2 ? f2(m.results[2].auc_roc) : 'n/a'}).</li>
                : <li>Within a single antibiotic the AUC averages {f2(m.within_antibiotic_auc)}, so the genome adds little beyond knowing the drug.</li>)}
              {m.served_fallback_rate
                ? <li className="text-rose2"><i className="bi bi-bug me-1"></i>{p0(m.served_fallback_rate)}% of <code>/predict</code> calls fall back to a heuristic instead of running this model.</li>
                : <li>{m.run_id
                    ? <>Runs on every <code>/predict</code> call; a file under 100,000 bp is refused rather than guessed.</>
                    : <>Runs on every <code>/predict</code> call: 0% fall back to the heuristic (the scaler bug that used to force it was fixed in Week 1).</>}</li>}
            </>
          )}
        </ul>
      </div>
    </div>
  );
}

function Report({ report }: { report: ModelReport }) {
  const s = report.split;
  const g = s.strategies.grouped;
  const r = s.strategies.random;
  const best = report.runs.find(x => x.id === report.best_run)!;
  const sh = report.shipped;
  const b = report.best;
  const c = b.confusion;
  const a2r = report.runs.find(x => x.id === 'A2_oof_grouped');
  const a9r = report.runs.find(x => x.id === 'A9_threshold_f1');
  const a6b = report.runs.find(x => x.id === 'A6b_lab_only_no_mic');
  const gr = shownGenomeRuns(report.genome_runs);
  const servedId = sh?.kmer?.run_id ?? null;
  const served = gr.runs.filter(x => x.id === servedId);
  const total = s.total_rows;

  return (
    <>
      {/* ── Headline numbers ─────────────────────────────────────── */}
      <div className="d-flex gap-3 flex-wrap mb-4">
        <Stat value={f3(best.auc_roc)} label={`Best model AUC (LightGBM, ${best.id})`} cls="text-indigo2" />
        {sh && <Stat value={f3(sh.lightgbm.results[1].auc_roc)} label="Deployed LightGBM, new genomes" />}
        {sh && <Stat value={f3(sh.kmer.results[1].auc_roc)} label={`Deployed ${sh.kmer.short_name || 'K-mer RF'}, new genomes`} />}
        <Stat value={report.runs.length} label="Experiment runs" />
        <Stat value={thousands(s.total_rows)} label="Labelled rows" />
        <Stat value={thousands(s.total_genomes)} label="Genomes" />
      </div>

      <div className="glass-card mb-5">
        <h5 className="fw-700 mb-2"><i className="bi bi-trophy me-2 text-indigo2"></i>Which model is best</h5>
        <p className="body-text mb-2">
          <strong>LightGBM trained on all {thousands(s.total_rows)} rows with a genome-grouped split
          ({best.id}) scores AUC {f3(best.auc_roc)} [{f3(best.auc_ci[0])} to {f3(best.auc_ci[1])}]</strong>{' '}
          on genomes it never saw. XGBoost and CatBoost tie with it (their confidence intervals overlap),
          and all three clearly beat logistic regression.{' '}
          <Link to="/compare">Compare the deployed and experimental models, and the data each trained on <i className="bi bi-arrow-right"></i></Link>
        </p>
        {sh && (
          <div className="alert-warning-custom">
            <i className="bi bi-exclamation-triangle me-2"></i>
            Earlier versions of this app quoted AUC 0.93 for both models. That figure was measured on genomes they
            had already seen in training. On new genomes the deployed LightGBM scores{' '}
            {f3(sh.lightgbm.results[1].auc_roc)} and the K-mer model{' '}
            {f3(sh.kmer.results[1].auc_roc)}. See <a href="#deployed">Deployed models</a>.
          </div>
        )}
      </div>

      {/* ── Key findings (built from the results by experiments/export_report.py) ── */}
      {report.insights?.length ? (
        <div className="mb-5" id="insights">
          <div className="sec-eyebrow">Key findings</div>
          <h2 className="sec-title">What the results tell us</h2>
          <p className="sec-sub mb-4">Each finding is written from the numbers when the report is rebuilt, and names the runs behind it.</p>
          <div className="row g-3">
            {report.insights.map(f => (
              <div className="col-md-6 col-xl-3" key={f.title}>
                <div className="glass-card h-100 insight-card">
                  <div className="insight-icon mb-2"><i className={`bi bi-${f.icon}`}></i></div>
                  <h6 className="fw-700 mb-2">{f.title}</h6>
                  <p className="small body-text mb-2">{f.text}</p>
                  <div className="caption-text"><i className="bi bi-link-45deg me-1"></i>{f.evidence}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* ── Section 1: how we split ─────────────────────────────── */}
      <div className="mb-5" id="split">
        <div className="sec-eyebrow">Section 1</div>
        <h2 className="sec-title">How we split train and test</h2>
        <p className="sec-sub mb-4">
          Each genome is tested against about {s.rows_per_genome} antibiotics, so it appears in about{' '}
          {s.rows_per_genome} rows. The split is made by <strong>genome</strong>, not by row, so no genome
          is ever in both training and test.
        </p>
        <div className="row g-4 mb-4">
          <div className="col-lg-7">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-layout-three-columns text-accent me-2"></i>Where every row goes</h6>
              <div className="split-bar" role="img" aria-label={`Fit ${s.fit_rows} rows, validation ${s.validation_rows} rows, test ${s.test_rows} rows`}>
                <div className="split-seg split-fit" style={{ flex: s.fit_rows }}>
                  <span className="split-seg-name">Fit</span><span className="split-seg-pct">{p0(s.fit_rows / total)}%</span>
                </div>
                <div className="split-seg split-val" style={{ flex: s.validation_rows }}>
                  <span className="split-seg-name">Val</span><span className="split-seg-pct">{p0(s.validation_rows / total)}%</span>
                </div>
                <div className="split-seg split-test" style={{ flex: s.test_rows }}>
                  <span className="split-seg-name">Test</span><span className="split-seg-pct">{p0(s.test_rows / total)}%</span>
                </div>
              </div>
              <div className="table-responsive mt-3">
                <table className="table table-custom table-sm mb-0">
                  <thead><tr><th>Part</th><th>Rows</th><th>Genomes</th><th>Used for</th></tr></thead>
                  <tbody>
                    <tr><td><span className="split-key split-fit"></span>Fit</td><td className="font-mono">{thousands(s.fit_rows)}</td>
                        <td className="font-mono" rowSpan={2}>{thousands(g.train_genomes)}</td><td className="small text-muted">Learning the trees</td></tr>
                    <tr><td><span className="split-key split-val"></span>Validation</td><td className="font-mono">{thousands(s.validation_rows)}</td>
                        <td className="small text-muted">Early stopping and choosing the threshold</td></tr>
                    <tr><td><span className="split-key split-test"></span>Test</td><td className="font-mono">{thousands(s.test_rows)}</td>
                        <td className="font-mono">{thousands(g.test_genomes)}</td><td className="small text-muted">Final metrics only, used once</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div className="col-lg-5">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-list-ol text-accent me-2"></i>The procedure</h6>
              <div className="method-steps">
                <div className="split-step"><span className="step-num step-indigo">1</span>
                  <div><strong>Test set.</strong> <code>StratifiedGroupKFold</code> with 5 folds, grouped by Genome ID. One fold (20% of genomes) becomes the test set.</div></div>
                <div className="split-step"><span className="step-num step-indigo">2</span>
                  <div><strong>Validation set.</strong> The training genomes are split again into {s.validation_folds} grouped folds. One is held out for early stopping and the threshold.</div></div>
                <div className="split-step"><span className="step-num step-indigo">3</span>
                  <div><strong>Rate features.</strong> Resistance rates per drug, taxon and genus are computed out of fold ({s.encoding_folds} grouped folds), so a row never sees its own label.</div></div>
                <div className="split-step"><span className="step-num step-indigo">4</span>
                  <div><strong>Stratified.</strong> Train and test keep the same resistant share:{' '}
                    {p1(g.train_prevalence)}% and {p1(g.test_prevalence)}%.</div></div>
              </div>
            </div>
          </div>
        </div>

        <div className="row g-4 mb-4">
          {([['random', 'Random row split', 'simulated', 'Old pipeline', 'Rows are shuffled one by one. Rows from the same genome land on both sides.', r],
             ['grouped', 'Genome-grouped split', 'trained', 'Used now', "Each genome goes entirely to one side, like a new patient's isolate in real use.", g]] as const)
            .map(([mode, title, badge, badgeText, text, st]) => (
            <div className="col-md-6" key={mode}>
              <div className="info-card h-100">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <h6 className="card-section-title mb-0">{title}</h6>
                  <span className={`status-badge ${badge}`}>{badgeText}</span>
                </div>
                <p className="small text-muted">{text}</p>
                <GenomeDemo mode={mode} />
                <div className="d-flex gap-3 mt-3">
                  <div className="flex-fill"><div className="stat-mini">
                    <div className="stat-mini-value">{thousands(st.shared_genomes)}</div>
                    <div className="stat-mini-label">Genomes on both sides</div>
                  </div></div>
                  <div className="flex-fill"><div className="stat-mini">
                    <div className="stat-mini-value">{p1(st.test_rows_from_seen_genomes)}%</div>
                    <div className="stat-mini-label">Test rows from a seen genome</div>
                  </div></div>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="genome-demo-legend small text-muted mb-4">
          <span><span className="split-key split-fit"></span>Training row</span>{' '}
          <span><span className="split-key split-test"></span>Test row</span>{' '}
          <span>Each line is one genome, each square one antibiotic test</span>
        </div>

        <div className="glass-card">
          <h6 className="card-section-title"><i className="bi bi-diagram-2 text-accent me-2"></i>Split strategies in the project</h6>
          <div className="table-responsive">
            <table className="table table-custom table-sm mb-0">
              <thead><tr><th>Strategy</th><th>What it does</th><th>Used by</th><th>Why</th></tr></thead>
              <tbody>
                <tr><td className="fw-600 text-white">grouped</td><td className="small">80/20 by genome, stratified</td>
                    <td className="small font-mono">A2, A3 to A10, learning curves</td><td className="small text-muted">Honest estimate for new isolates. The default.</td></tr>
                <tr><td className="fw-600 text-white">random</td><td className="small">80/20 by row, stratified</td>
                    <td className="small font-mono">A0, A1, the deployed models</td><td className="small text-muted">Kept only to measure how much it inflates scores</td></tr>
                <tr><td className="fw-600 text-white">species_holdout</td><td className="small">Train without one genus, test only on it</td>
                    <td className="small font-mono">A12 (Klebsiella)</td><td className="small text-muted">Can the model handle an organism it has never seen?</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── Section 2: deployed models ──────────────────────────── */}
      {sh && (
        <div className="mb-5" id="deployed">
          <div className="sec-eyebrow">Section 2</div>
          <h2 className="sec-title">Deployed models, re-tested</h2>
          <p className="sec-sub mb-4">
            The models behind <Link to="/forecast">/forecast</Link> and <Link to="/predict">/predict</Link> were trained with a
            random row split. We reconstructed exactly which genomes they trained on and scored them on every genome they never saw.
          </p>
          <div className="glass-card mb-4">
            <h6 className="card-section-title mb-1"><i className="bi bi-bar-chart text-accent me-2"></i>AUC on genomes seen in training vs never seen</h6>
            <p className="small text-muted mb-2">Near-perfect on familiar genomes, much weaker on new ones. That gap is what a random split hides.</p>
            <Chart id="seenChart" report={report} build={seenFigure} height={320} />
          </div>
          <div className="row g-4 mb-4">
            <DeployedCard m={sh.lightgbm} which="lightgbm" icon="graph-up-arrow" report={report} />
            <DeployedCard m={sh.kmer} which="kmer" icon="upc-scan" report={report} />
          </div>
        </div>
      )}

      {/* ── Section 3: every experiment ─────────────────────────── */}
      <div className="mb-5" id="experiments">
        <div className="sec-eyebrow">Section 3</div>
        <h2 className="sec-title">All experiment runs</h2>
        <p className="sec-sub mb-4">Every run from <code>experiments/</code> on the complete BV-BRC data (cleaning {report.clean_version || 'v7'}), scored on the test genomes it held out. The bars show the 95% confidence interval, resampled by genome.</p>
        <div className="glass-card mb-4">
          <h6 className="card-section-title mb-1"><i className="bi bi-bar-chart-steps text-accent me-2"></i>AUC-ROC by run</h6>
          <Chart id="aucChart" report={report} build={aucFigure} height={140 + 24 * report.runs.length} />
        </div>
        <div className="row g-4 mb-4">
          <div className="col-lg-6">
            <div className="glass-card h-100">
              <h6 className="card-section-title mb-1"><i className="bi bi-bezier2 text-accent me-2"></i>ROC curves</h6>
              <p className="small text-muted mb-2">Higher and further left is better. The dotted line is guessing.</p>
              <Chart id="rocChart" report={report} build={rocFigure} height={440} />
            </div>
          </div>
          <div className="col-lg-6">
            <div className="glass-card h-100">
              <h6 className="card-section-title mb-1"><i className="bi bi-graph-up text-accent me-2"></i>Learning curve</h6>
              <p className="small text-muted mb-2">LightGBM AUC as training data grows. It flattens early, so more rows alone will not fix it.</p>
              <Chart id="learningChart" report={report} build={learningFigure} height={440} />
            </div>
          </div>
        </div>
        <div className="glass-card mb-4">
          <h6 className="card-section-title mb-1"><i className="bi bi-sliders text-accent me-2"></i>The error trade-off</h6>
          <p className="small text-muted mb-2">
            <strong>VME</strong> (very major error) is a resistant isolate called susceptible, the dangerous mistake.{' '}
            <strong>ME</strong> (major error) is a false resistant call. Moving the threshold trades one for the other,{' '}
            {a2r && a9r && `which is why A2 (threshold ${f2(a2r.threshold)}) and A9 (${f2(a9r.threshold)}) share an AUC but sit far apart here.`}
          </p>
          <Chart id="errorChart" report={report} build={errorFigure} height={380} />
        </div>
        <div className="glass-card">
          <h6 className="card-section-title"><i className="bi bi-table text-accent me-2"></i>Results table</h6>
          <div className="table-responsive">
            <table className="table table-custom table-sm mb-0">
              <thead><tr><th>Run</th><th>Model</th><th>Split</th><th>Rows</th><th>AUC [95% CI]</th><th>AUPRC</th><th>F1</th><th>VME</th><th>ME</th><th>Thr</th></tr></thead>
              <tbody>
                {report.runs.map(run => (
                  <tr key={run.id} className={run.id === report.best_run ? 'report-best-row' : undefined}>
                    <td><span className="font-mono small text-white">{run.run_id || run.id}</span>
                        <div className="caption-text">{run.description}</div></td>
                    <td className="small">{run.model}</td>
                    <td className="small">{run.split}</td>
                    <td className="font-mono small">{thousands(run.rows)}</td>
                    <td className="font-mono small text-nowrap">{f3(run.auc_roc)}<div className="caption-text">{f3(run.auc_ci[0])} to {f3(run.auc_ci[1])}</div></td>
                    <td className="font-mono small">{f3(run.auc_pr)}</td>
                    <td className="font-mono small">{f3(run.f1)}</td>
                    <td className="font-mono small">{p1(run.very_major_error)}%</td>
                    <td className="font-mono small">{p1(run.major_error)}%</td>
                    <td className="font-mono small">{f2(run.threshold)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="caption-text mt-2 mb-0">
            A6 (lab labels only) scores highest because a wet-lab label is almost fixed by the MIC value.
            {a6b && ` Without MIC (A6b) it drops to ${f3(a6b.auc_roc)}, so it is an easier task, not a better model.`}
          </p>
        </div>
      </div>

      {/* ── Section 4: inside the best model ────────────────────── */}
      <div className="mb-5" id="best">
        <div className="sec-eyebrow">Section 4</div>
        <h2 className="sec-title">Inside the best model ({b.id})</h2>
        <p className="sec-sub mb-4">
          {b.model_info.kind}, {b.model_info.n_trees} trees, {b.features.length} features,
          tested on {thousands(s.test_rows)} rows at threshold {f2(b.test.threshold)}.
        </p>
        <div className="row g-4">
          <div className="col-lg-4">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-grid text-accent me-2"></i>Confusion matrix</h6>
              <div className="confusion">
                <div></div><div className="confusion-head">Called S</div><div className="confusion-head">Called R</div>
                <div className="confusion-side">Truly S</div>
                <div className="confusion-cell ok"><strong>{thousands(c.tn)}</strong><span>correct</span></div>
                <div className="confusion-cell warn"><strong>{thousands(c.fp)}</strong><span>ME {p0(b.test.major_error)}%</span></div>
                <div className="confusion-side">Truly R</div>
                <div className="confusion-cell bad"><strong>{thousands(c.fn)}</strong><span>VME {p0(b.test.very_major_error)}%</span></div>
                <div className="confusion-cell ok"><strong>{thousands(c.tp)}</strong><span>correct</span></div>
              </div>
              <div className="d-flex gap-2 mt-3">
                <div className="flex-fill"><div className="stat-mini"><div className="stat-mini-value fs-16">{p0(b.test.sensitivity)}%</div><div className="stat-mini-label">Sensitivity</div></div></div>
                <div className="flex-fill"><div className="stat-mini"><div className="stat-mini-value fs-16">{p0(b.test.specificity)}%</div><div className="stat-mini-label">Specificity</div></div></div>
              </div>
            </div>
          </div>
          <div className="col-lg-8">
            <div className="glass-card h-100">
              <h6 className="card-section-title mb-1"><i className="bi bi-capsule text-accent me-2"></i>Best and worst antibiotics</h6>
              <p className="small text-muted mb-2">AUC per antibiotic, among the {b.per_antibiotic_count} with at least 1,000 test rows.</p>
              <Chart id="drugChart" report={report} build={drugFigure} height={460} />
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 5: genome models (genome_runs, format §6) ───── */}
      {gr.runs.length > 0 && (
        <div className="mb-5" id="genome">
          <div className="sec-eyebrow">Section 5</div>
          <h2 className="sec-title">Genome models, scored on lab results</h2>
          <p className="sec-sub mb-4">
            These {gr.runs.length} run{gr.runs.length !== 1 ? 's' : ''} read the genome itself (resistance genes, k-mers, or both; baselines use none),
            on complete genomes, cleaning {gr.version}{gr.hasV7 && ' (runs marked v7 read the same rows and labels; v7 changed only MIC values, which genome runs do not use)'}. Every score here is on <strong>lab-tested results only</strong>, from
            genomes the model never saw. The data and labels differ from Sections 1 to 4, so compare these scores with each
            other, not with the forecaster.
          </p>
          <div className="row g-4 mb-4">
            <div className="col-lg-8">
              <div className="glass-card h-100">
                <h6 className="card-section-title mb-1"><i className="bi bi-dna text-accent me-2"></i>Lab AUC by run</h6>
                <p className="small text-muted mb-2">Each dot is one run; the colour is how its test genomes were held out.</p>
                <Chart id="genomeChart" report={report} build={genomeFigure} height={140 + 22 * gr.runs.length} />
              </div>
            </div>
            <div className="col-lg-4">
              <div className="info-card h-100">
                <h6 className="card-section-title"><i className="bi bi-info-circle text-accent me-2"></i>Reading these scores</h6>
                <ul className="small mb-0 ps-3">
                  <li className="mb-2"><strong>Lab AUC</strong> uses only rows with a real lab result. BV-BRC's computer-predicted
                    labels were made from the genome itself, so scoring on them would reward copying.</li>
                  <li className="mb-2"><strong>Split</strong>: <em>grouped</em> keeps each genome on one side; <em>lineage</em> also keeps
                    near-identical isolates together, so outbreak clones cannot leak; <em>species_holdout</em> tests on a whole
                    genus the model never saw.</li>
                  <li className="mb-2"><strong>Lab rows</strong> is how many results each score rests on.</li>
                  <li>{served.length
                    ? <>Served on <Link to="/predict">/predict</Link>: <code>{served[0].id}</code> (the star).</>
                    : <>None of these runs is the one <Link to="/predict">/predict</Link> serves; that model is in Section 2.</>}</li>
                </ul>
              </div>
            </div>
          </div>
          <div className="info-card">
            <h6 className="card-section-title"><i className="bi bi-table text-accent me-2"></i>All genome runs</h6>
            <div className="table-responsive">
              <table className="table table-custom table-sm mb-0 genome-runs-table">
                <thead><tr><th>Run</th><th>Reads</th><th>What it tests</th><th>Split</th><th>Lab AUC</th><th>Lab rows</th></tr></thead>
                <tbody>
                  {gr.runs.slice().sort((x, y) => (y.auc_roc_lab as number) - (x.auc_roc_lab as number)).map(run => {
                    const isServed = run.id === servedId;
                    return (
                      <tr key={run.id} className={isServed ? 'report-best-row' : undefined}>
                        <td className="font-mono small">{run.id}{isServed && <> <span className="status-badge trained ms-1">Served</span></>}</td>
                        <td className="small">{run.features || ''}</td>
                        <td className="small text-muted">{run.description}</td>
                        <td className="small">{run.split}</td>
                        <td className="font-mono">{f3(run.auc_roc_lab as number)}{run.auc_roc_lab_ci && (
                          <>{' '}<span className="text-muted small">[{f3(run.auc_roc_lab_ci[0])}–{f3(run.auc_roc_lab_ci[1])}]</span></>)}</td>
                        <td className="font-mono small">{typeof run.n_lab === 'number' ? thousands(run.n_lab) : 'n/a'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      <div className="glass-card">
        <h6 className="card-section-title"><i className="bi bi-arrow-repeat text-accent me-2"></i>Updating this page</h6>
        <p className="small text-muted">This page reads <code>backend/trained_models/model_report.json</code>, generated {report.generated_at.slice(0, 10)}. After new experiments or retraining, rebuild it:</p>
        <div className="code-block"><pre className="code-content"><code>{`python experiments/run.py experiments/configs/<config>.json
python experiments/evaluate_shipped.py   # after retraining the app's models
python experiments/export_report.py`}</code></pre></div>
      </div>
    </>
  );
}

export default function Models() {
  useTitle('Model Report');
  const report = useModelReport();
  const [root, setRoot] = useState<HTMLDivElement | null>(null);
  usePageEffects(root, [report.state]);
  return (
    <>
      <ReportHeader title="Model Report" icon="clipboard-data"
                    subtitle="Every model we trained, how the data was split for testing, and how each one scores on genomes it has never seen" />
      <div className="container-xl py-4" ref={setRoot}>
        {report.state === 'ready' ? <Report report={report.report} />
          : <ReportUnavailable error={report.state === 'failed' ? report.error : undefined} />}
      </div>
    </>
  );
}
