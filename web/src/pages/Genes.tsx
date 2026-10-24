/* /genes: the resistance genes and mutations AMRFinderPlus found in every
   complete genome, and how well they match the lab results
   (frontend/templates/genes.html; the data is /api/genes/). */
import { useCallback, useEffect, useRef, useState, type FormEvent, type MouseEvent } from 'react';
import { Link, useLocation } from 'react-router';
import Plot, { type Figure, type PlotTheme } from '../components/Plot';
import { apiGet, apiUrl, errorText } from '../lib/api';
import { pyFixed, thousands } from '../lib/metrics';
import { usePageEffects, useTitle } from '../lib/pageEffects';
import { classFigure, geneTitle, heatFigure, perGenomeFigure, topFigure } from './genes/charts';
import type { GeneReport, GenomeGenes, LabView } from './genes/types';

const FIRST_ROWS = 12;
const KIND_LABEL: Record<string, string> = { gene: 'Gene', point_mutation: 'Mutation' };

const p1 = (x: number) => `${pyFixed(100 * x, 1)}%`;
/** Python's '%g' for the medians (9.0 -> '9', 2.5 -> '2.5'). */
const pyG = (x: number) => String(Number(x.toPrecision(6)));

/** The genome a /genes#genome=<id> link asks for. */
export const linkedGenome = (hash: string) => decodeURIComponent((hash.match(/^#genome=(.+)$/) || [])[1] || '');

function Chart({ id, report, build, height }: { id: string; report: GeneReport; build: (r: GeneReport, t: PlotTheme) => Figure; height: number }) {
  const figure = useCallback((t: PlotTheme) => build(report, t), [report, build]);
  return <Plot id={id} className="report-chart" style={{ height }} figure={figure} />;
}

function Meter({ share, cls }: { share: number | null | undefined; cls: string }) {
  if (share === null || share === undefined) return <span className="text-muted">n/a</span>;
  return (
    <div className="lab-meter">
      <span className="lab-meter-track"><span className={`lab-meter-fill ${cls}`} style={{ width: `${Math.max(2, Math.round(100 * share))}%` }}></span></span>
      <span className="lab-meter-val">{(100 * share).toFixed(1)}%</span>
    </div>
  );
}

/** Section 4's table: gene and antibiotic pairs, lab labels or every label. */
function GeneVsLab({ views }: { views: { lab: LabView; all: LabView } }) {
  const [labels, setLabels] = useState<'lab' | 'all'>('lab');
  const [showAll, setShowAll] = useState(false);
  const v = views[labels];
  const rows = showAll ? v.pairs : v.pairs.slice(0, FIRST_ROWS);
  const shown = showAll ? v.pairs.length : Math.min(FIRST_ROWS, v.pairs.length);
  const toggle = (which: 'lab' | 'all', text: string) => (
    <button type="button" className={'btn btn-sm btn-model' + (labels === which ? ' active' : '')} data-labels={which}
            aria-pressed={labels === which} onClick={() => setLabels(which)}>{text}</button>
  );
  return (
    <>
      <div className="d-flex flex-wrap gap-2 mb-3 label-toggle" role="group" aria-label="Which labels to compare with">
        {toggle('lab', `Lab results only (${views.lab.genomes_labelled} genomes)`)}
        {toggle('all', `Include BV-BRC predictions (${thousands(views.all.genomes_labelled)} genomes)`)}
      </div>
      <div className={'alert-warning-custom mb-3' + (labels === 'lab' ? ' d-none' : '')} id="compNote">
        <i className="bi bi-exclamation-triangle me-2"></i>
        Most of these labels were <strong>predicted</strong> by BV-BRC's own models from the genome, not measured
        in a lab. Comparing genes with them is partly circular, so treat this view as a rough check only.
      </div>
      <div className="glass-card">
        <div className="table-responsive">
          <table className="table table-custom table-sm mb-0" id="labTable">
            <thead><tr>
              <th>Gene</th><th>Antibiotic</th>
              <th className="text-end">With gene</th><th style={{ minWidth: '180px' }}>Resistant with gene</th>
              <th className="text-end">Without</th><th style={{ minWidth: '180px' }}>Resistant without</th>
            </tr></thead>
            <tbody>
              {!v.pairs.length
                ? <tr><td colSpan={6} className="text-muted">Not enough labelled genomes yet.</td></tr>
                : rows.map(r => (
                  <tr key={`${r.gene}|${r.antibiotic}`}>
                    <td><code>{r.gene}</code><div className="caption-text">{geneTitle(r.gene_subclass)}</div></td>
                    <td>{r.antibiotic}</td>
                    <td className="text-end">{r.carriers.toLocaleString()}</td>
                    <td><Meter share={r.carriers_resistant} cls="with" /></td>
                    <td className="text-end">{r.others.toLocaleString()}</td>
                    <td><Meter share={r.others_resistant} cls="without" /></td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <div className="d-flex flex-wrap align-items-center gap-3 mt-2">
          <button type="button" className={'btn btn-sm btn-model' + (v.pairs.length <= FIRST_ROWS ? ' d-none' : '')} id="labMore"
                  style={{ width: 'auto' }} onClick={() => setShowAll(x => !x)}>
            {showAll ? 'Show fewer' : `Show all ${v.pairs.length}`}
          </button>
          <p className="caption-text mb-0" id="labCaption">
            {`${shown} of ${v.pairs_total} gene and antibiotic pairs with at least ${v.min_carriers} genomes carrying the gene, `
              + `most genomes first. Over ${v.genomes_labelled.toLocaleString()} genomes with `
              + (labels === 'lab' ? 'a laboratory result.' : 'any label.')}
          </p>
        </div>
      </div>
    </>
  );
}

type Lookup = { state: 'idle' } | { state: 'busy' } | { state: 'error'; message: string } | { state: 'done'; id: string; data: GenomeGenes };

function LookupResult({ result }: { result: Lookup }) {
  if (result.state === 'idle') return null;
  if (result.state === 'busy') return <p className="text-muted small mb-0">Looking up…</p>;
  if (result.state === 'error') return <p className="text-danger small mb-0">{result.message}</p>;
  const d = result.data;
  if (!d.searched) {
    return <p className="small mb-0"><strong>{result.id}</strong> was not searched: it is not one of our genomes,
      its complete assembly could not be downloaded, or the run has not reached it yet.</p>;
  }
  const head = (
    <p className="small mb-2"><strong>{d.genome_id}</strong> · <em>{d.species}</em> ·{' '}
      {d.genes.length ? `${d.genes.length} resistance gene${d.genes.length > 1 ? 's' : ''} and mutations`
                      : 'searched, no core resistance gene or mutation found'}</p>
  );
  if (!d.genes.length) return head;
  return (
    <>
      {head}
      <div className="table-responsive"><table className="table table-custom table-sm mb-0">
        <thead><tr><th>Gene or mutation</th><th>Type</th><th>Drug class</th>
          <th className="text-end">Identity</th><th className="text-end">Coverage</th><th>Method</th></tr></thead>
        <tbody>
          {d.genes.map(g => (
            <tr key={g.gene}>
              <td><code>{g.gene}</code><div className="caption-text">{g.name}</div></td>
              <td>{KIND_LABEL[g.type] || g.type}</td>
              <td>{geneTitle(g.class)}<div className="caption-text">{geneTitle(g.subclass)}</div></td>
              <td className="text-end">{g.identity.toFixed(1)}%</td>
              <td className="text-end">{g.coverage.toFixed(1)}%</td>
              <td className="small">{g.method}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
    </>
  );
}

function Report({ report }: { report: GeneReport }) {
  const run = report.run, s = report.summary, mx = report.matrix;
  const { hash } = useLocation();
  const [genomeId, setGenomeId] = useState('');
  const [result, setResult] = useState<Lookup>({ state: 'idle' });
  const request = useRef(0);
  const section = useRef<HTMLDivElement>(null);

  const lookup = useCallback(async (raw: string) => {
    const id = raw.trim();
    if (!id) return;
    const mine = ++request.current;
    setResult({ state: 'busy' });
    try {
      const data = await apiGet<GenomeGenes>(`genes/${encodeURIComponent(id)}/`);
      if (mine === request.current) setResult({ state: 'done', id, data });
    } catch (e) {
      if (mine === request.current) setResult({ state: 'error', message: errorText(e) });
    }
  }, []);

  /* /genes#genome=1000561.3 opens with that genome looked up, for sharing */
  useEffect(() => {
    const linked = linkedGenome(hash);
    if (!linked) return;
    setGenomeId(linked);
    lookup(linked);
    section.current?.scrollIntoView();
  }, [hash, lookup]);

  function show(id: string) {
    history.replaceState(null, '', '#genome=' + encodeURIComponent(id));
    lookup(id);
  }
  function submit(e: FormEvent) {
    e.preventDefault();
    show(genomeId.trim());
  }
  function example(e: MouseEvent, id: string) {
    e.preventDefault();
    setGenomeId(id);
    show(id);
    section.current?.scrollIntoView({ behavior: 'smooth' });
  }

  return (
    <>
      {!run.complete && (
        <div className="alert-warning-custom mb-4">
          <i className="bi bi-hourglass-split me-2"></i>
          Partial results: {thousands(run.genomes_searched)} of {thousands(run.genomes_downloaded)}{' '}
          genomes searched so far. The numbers below cover those genomes only.
        </div>
      )}

      {/* ── Headline numbers ─────────────────────────────────────── */}
      <div className="d-flex gap-3 flex-wrap mb-4">
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static text-indigo2">{thousands(run.genomes_searched)}</div>
          <div className="stat-mini-label">Complete genomes searched{!run.complete && ` (of ${thousands(run.genomes_downloaded)})`}</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">{p1(s.with_gene / s.genomes)}</div>
          <div className="stat-mini-label">Carry at least one resistance gene</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">{thousands(s.genes)}</div>
          <div className="stat-mini-label">Different resistance genes</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">{thousands(s.point_mutations)}</div>
          <div className="stat-mini-label">Different point mutations</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">{pyG(s.median_genes)}</div>
          <div className="stat-mini-label">Median per genome (max {s.max_genes})</div>
        </div></div>
      </div>

      <div className="glass-card mb-5">
        <h5 className="fw-700 mb-2"><i className="bi bi-search me-2 text-indigo2"></i>What this page shows</h5>
        <p className="body-text mb-0">
          Our K-mer model counts DNA letter patterns; it does not know which gene causes resistance.
          AMRFinderPlus {run.amrfinder_version || ''} (database {run.database_version || 'unknown'}), NCBI's
          own tool, searched each complete assembly for known resistance genes and resistance mutations
          (only <em>core</em> AMR elements: {run.filter}). These results become gene features for the next
          models, and they can explain a prediction: <em>resistant because <code>blaCTX-M-15</code> is present</em>.
        </p>
      </div>

      {/* ── Section 1: what was found ───────────────────────────── */}
      <div className="mb-5" id="found">
        <div className="sec-eyebrow">Section 1</div>
        <h2 className="sec-title">What was found</h2>
        <p className="sec-sub mb-4">The most common genes and mutations, how many each genome carries, and which drug classes they affect.</p>
        <div className="glass-card mb-4">
          <h6 className="card-section-title mb-1"><i className="bi bi-bar-chart text-accent me-2"></i>Top {report.top_genes.length} genes and mutations</h6>
          <p className="small text-muted mb-2">Share of searched genomes that carry each one.</p>
          <Chart id="topChart" report={report} build={topFigure} height={90 + 24 * report.top_genes.length} />
        </div>
        <div className="row g-4 mb-4">
          <div className="col-lg-5">
            <div className="glass-card h-100">
              <h6 className="card-section-title mb-1"><i className="bi bi-bar-chart-line text-accent me-2"></i>Resistance genes per genome</h6>
              <p className="small text-muted mb-2">{thousands(s.genomes - s.with_gene)} genomes had none: searched, and nothing was found.</p>
              <Chart id="perGenomeChart" report={report} build={perGenomeFigure} height={300} />
            </div>
          </div>
          <div className="col-lg-7">
            <div className="glass-card h-100">
              <h6 className="card-section-title mb-1"><i className="bi bi-capsule text-accent me-2"></i>Genomes with a gene for each drug class</h6>
              <p className="small text-muted mb-2">A genome counts once per class, however many genes of that class it carries.</p>
              <Chart id="classChart" report={report} build={classFigure} height={90 + 22 * Math.min(report.classes.length, 14)} />
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 2: the gene matrix ──────────────────────────── */}
      <div className="mb-5" id="matrix">
        <div className="sec-eyebrow">Section 2</div>
        <h2 className="sec-title">The gene matrix</h2>
        <p className="sec-sub mb-4">
          The same results as one big yes/no table, the form the next models learn from:
          one row per genome, one column per gene or mutation, <strong>1</strong> if AMRFinderPlus found it.
        </p>
        <div className="d-flex gap-3 flex-wrap align-items-stretch mb-4">
          <div className="flex-fill min-w-130"><div className="stat-mini h-100">
            <div className="stat-mini-value stat-mini-static">{thousands(mx.genomes)} × {mx.symbols}</div>
            <div className="stat-mini-label">Genomes × genes and mutations</div>
          </div></div>
          <div className="flex-fill min-w-130"><div className="stat-mini h-100">
            <div className="stat-mini-value stat-mini-static">{pyFixed(100 * mx.ones / mx.cells, 2)}%</div>
            <div className="stat-mini-label">Cells that are 1 ({thousands(mx.ones)} of {thousands(mx.cells)}): a genome carries a handful of genes, if any</div>
          </div></div>
          <div className="d-flex flex-column justify-content-center gap-2">
            <a className="btn btn-model" href={apiUrl('genes/matrix.csv')} download><i className="bi bi-download me-2"></i>Gene matrix (CSV, opens in Excel)</a>
            <a className="btn btn-model" href={apiUrl('genes/info.csv')} download><i className="bi bi-download me-2"></i>What each column means (CSV)</a>
          </div>
        </div>
        <div className="glass-card">
          <h6 className="card-section-title mb-1"><i className="bi bi-grid-3x3-gap text-accent me-2"></i>A corner of the matrix</h6>
          <p className="small text-muted mb-3">{mx.preview.rows.length} real genomes and the {mx.preview.genes.length} most common genes.{' '}
            <span className="matrix-dot on" aria-hidden="true"></span> = found (1), <span className="matrix-dot" aria-hidden="true"></span> = not found (0).</p>
          <div className="table-responsive">
            <table className="table table-custom table-sm mb-0 matrix-preview">
              <thead><tr>
                <th>Genome</th>
                {mx.preview.genes.map(g => <th key={g} className="text-center matrix-gene">{g}</th>)}
                <th className="text-end">All genes</th>
              </tr></thead>
              <tbody>
                {mx.preview.rows.map(r => (
                  <tr key={r.genome}>
                    <td><a href={`#genome=${r.genome}`} className="lookup-example" data-id={r.genome} onClick={e => example(e, r.genome)}><code>{r.genome}</code></a>
                      <div className="caption-text"><em>{r.species}</em></div></td>
                    {r.values.map((v, i) => (
                      <td key={i} className="text-center"><span className={'matrix-dot' + (v ? ' on' : '')} role="img" aria-label={v ? 'found' : 'not found'}></span></td>
                    ))}
                    <td className="text-end">{r.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="caption-text mt-2 mb-0">"All genes" counts every gene and mutation in the genome, including the {mx.symbols - mx.preview.genes.length} columns not shown. Click a genome to see them all.</p>
        </div>
      </div>

      {/* ── Section 3: by species ───────────────────────────────── */}
      <div className="mb-5" id="species">
        <div className="sec-eyebrow">Section 3</div>
        <h2 className="sec-title">Genes by species</h2>
        <p className="sec-sub mb-4">Each species has its own resistance genes. Darker means more of that genus's genomes carry the gene.</p>
        <div className="glass-card mb-4">
          <h6 className="card-section-title mb-1"><i className="bi bi-grid-3x3 text-accent me-2"></i>Share of genomes carrying each gene, by genus</h6>
          <p className="small text-muted mb-2">Genera with at least {report.heatmap.min_genomes} searched genomes; the {report.heatmap.genes.length} most common genes overall.</p>
          {report.heatmap.genera.length > 0
            ? <Chart id="heatChart" report={report} build={heatFigure} height={150 + 34 * report.heatmap.genera.length} />
            : <div id="heatChart" className="report-chart" style={{ height: 150 }}></div>}
        </div>
        <div className="glass-card">
          <h6 className="card-section-title"><i className="bi bi-table text-accent me-2"></i>Every genus</h6>
          <div className="table-responsive">
            <table className="table table-custom table-sm mb-0">
              <thead><tr><th>Genus</th><th className="text-end">Genomes</th><th className="text-end">With a gene</th><th className="text-end">Median genes</th><th>Most common</th></tr></thead>
              <tbody>
                {report.genera.map(g => (
                  <tr key={g.genus}>
                    <td><em>{g.genus}</em></td>
                    <td className="text-end">{thousands(g.genomes)}</td>
                    <td className="text-end">{p1(g.with_gene)}</td>
                    <td className="text-end">{pyG(g.median_genes)}</td>
                    <td className="small">{g.top.length
                      ? g.top.map((t, i) => <span key={t.gene}><code>{t.gene}</code> {pyFixed(100 * t.share, 0)}%{i < g.top.length - 1 && ' · '}</span>)
                      : <span className="text-muted">none found</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── Section 4: gene vs lab result ───────────────────────── */}
      <div className="mb-5" id="lab">
        <div className="sec-eyebrow">Section 4</div>
        <h2 className="sec-title">Do the genes match the lab results?</h2>
        <p className="sec-sub mb-3">
          For a gene and an antibiotic AMRFinderPlus says it acts on: how often were genomes <strong>with</strong>{' '}
          the gene resistant, compared with genomes <strong>without</strong> it?
        </p>
        <GeneVsLab views={report.gene_vs_lab} />
      </div>

      {/* ── Section 5: look up a genome ─────────────────────────── */}
      <div className="mb-5" id="lookup" ref={section}>
        <div className="sec-eyebrow">Section 5</div>
        <h2 className="sec-title">Look up a genome</h2>
        <p className="sec-sub mb-3">Every core resistance gene and mutation AMRFinderPlus found in one genome.</p>
        <div className="glass-card">
          <form className="d-flex flex-wrap gap-2 mb-3" id="lookupForm" onSubmit={submit}>
            <label htmlFor="genomeId" className="visually-hidden">Genome ID</label>
            <input id="genomeId" className="form-control form-control-custom" style={{ maxWidth: '260px' }}
                   placeholder="Genome ID, e.g. 1000561.3" autoComplete="off" required
                   value={genomeId} onChange={e => setGenomeId(e.target.value)} />
            <button className="btn btn-model" type="submit"><i className="bi bi-search me-2"></i>Look up</button>
            <span className="small text-muted align-self-center">Try{' '}
              <a href="#lookup" className="lookup-example" data-id="1000561.3" onClick={e => example(e, '1000561.3')}>1000561.3</a>{' '}
              (<em>P. aeruginosa</em>)</span>
          </form>
          <div id="lookupResult" aria-live="polite"><LookupResult result={result} /></div>
        </div>
      </div>

      <div className="glass-card">
        <h6 className="card-section-title"><i className="bi bi-arrow-repeat text-accent me-2"></i>Where these numbers come from</h6>
        <p className="small text-muted">This page reads <code>backend/trained_models/gene_report.json</code> and <code>gene_hits.json</code>, generated {run.generated_at.slice(0, 10)}{run.git_commit && <> at <code>{run.git_commit}</code></>}. After AMRFinderPlus finishes, rebuild them:</p>
        <div className="code-block"><pre className="code-content"><code>{`python experiments/genome/features/run_amrfinder.py --jobs 4 --threads 2
python experiments/genome/features/export_gene_report.py`}</code></pre></div>
      </div>
    </>
  );
}

export default function Genes() {
  useTitle('Resistance Genes');
  const [state, setState] = useState<{ report?: GeneReport; error?: string }>({});
  const [root, setRoot] = useState<HTMLDivElement | null>(null);
  usePageEffects(root, [state]);
  useEffect(() => {
    let alive = true;
    apiGet<GeneReport>('genes/')
      .then(report => { if (alive) setState({ report }); })
      .catch(e => { if (alive) setState({ error: errorText(e) }); });
    return () => { alive = false; };
  }, []);

  return (
    <>
      <div className="page-header">
        <div className="container-xl">
          <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
            <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
            <li className="breadcrumb-item active">Resistance Genes</li>
          </ol></nav>
          <div className="d-flex align-items-center gap-3">
            <div className="page-header-icon kmer-icon"><i className="bi bi-bacteria"></i></div>
            <div>
              <h1 className="page-title">Resistance Genes</h1>
              <p className="page-subtitle">Resistance genes and mutations NCBI AMRFinderPlus found in the complete genome of every isolate, and how well they match the lab results</p>
            </div>
          </div>
        </div>
      </div>
      <div className="container-xl py-4" ref={setRoot}>
        {state.report ? <Report report={state.report} />
          : state.error ? (
            <div className="empty-state">
              <div className="empty-state-icon"><i className="bi bi-bacteria"></i></div>
              <h5 className="fw-700">Gene report not available</h5>
              <p className="text-muted mb-0">{state.error}</p>
            </div>
          ) : (
            <div className="empty-state">
              <div className="spinner-border text-accent mb-3" role="status"></div>
              <p className="text-muted mb-0">Loading the gene report…</p>
            </div>
          )}
      </div>
    </>
  );
}
