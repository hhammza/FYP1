/* The parts of /timeline that only show text (converted from
   frontend/templates/mutation_timeline.html). */
import { Link } from 'react-router';
import { useHealth } from '../../lib/health';
import { pyFixed, thousands } from '../../lib/metrics';
import BioIcon from '../../components/BioIcon';
import HeaderScene from '../../components/HeaderScene';

/** The page header. */
export function TimelineHeader() {
  return (
    <>
    <div className="page-header">
      <HeaderScene kind="growth" />
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">Mutation Timeline</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon timeline-icon"><BioIcon icon="bi-activity" live /></div>
          <div>
            <h1 className="page-title">Bacterial Mutation Timeline</h1>
            <p className="page-subtitle">A trained model forecasts yearly resistance from BV-BRC lab results; a what-if simulation shows the weeks under treatment</p>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}

type MaeEntry = [number, [number, number]];
interface TimelineMetrics {
  data?: { series?: number; lab_results?: number; train_until?: number };
  test_mae_pp?: Record<string, MaeEntry>;
  interval_abs_error_pp?: { q80?: number };
}

/** The timeline ML model's held-out numbers (timeline_metrics.json, via
    /api/health/'s `timeline_ml`); undefined until the backend answers. */
export function useTimelineMetrics(): TimelineMetrics | undefined {
  const { health } = useHealth();
  return health?.models?.timeline_ml?.metrics as TimelineMetrics | undefined;
}

const pp = (v?: MaeEntry) => (v ? `${pyFixed(v[0], 1)} pp` : '—');

/** The numbers strip above the form. */
export function ContextStrip() {
  const m = useTimelineMetrics();
  const stat = (value: string, label: string, colour = '') => (
    <div className="flex-fill min-w-150">
      <div className="stat-mini">
        <div className={'stat-mini-value ' + colour}>{value}</div>
        <div className="stat-mini-label">{label}</div>
      </div>
    </div>
  );
  return (
    <div className="d-flex gap-3 flex-wrap mb-4">
      {stat('LightGBM', 'Trained model', 'text-rose2')}
      {stat(m?.data?.series ? String(m.data.series) : '—', 'Organism and drug series')}
      {stat(m?.data?.lab_results ? thousands(m.data.lab_results) : '—', 'BV-BRC lab results', 'text-amber2')}
      {stat(pp(m?.test_mae_pp?.model), 'Error on unseen years', 'text-indigo2')}
      {stat('1–10', 'Years ahead', 'text-emerald2')}
    </div>
  );
}

/** How the model works and how well, under the form. */
export function ModelGuides() {
  const m = useTimelineMetrics();
  const mae = m?.test_mae_pp;
  return (
    <>
      <div className="info-card mt-4" id="timelineModelCard">
        <h6 className="card-section-title"><BioIcon icon="bi-cpu" className="text-accent me-2" />The Model</h6>
        <div className="arch-box">
          <div className="arch-layer text-accent2">BV-BRC lab results with a collection year</div>
          <div className="arch-arrow">↓</div>
          <div className="arch-layer">Yearly resistant share per genus and antibiotic</div>
          <div className="arch-arrow">↓</div>
          <div className="arch-layer">Earlier years only: last values, recent slope, gap, drug class</div>
          <div className="arch-arrow">↓</div>
          <div className="arch-layer text-emerald2">LightGBM predicts the change from last year</div>
          <div className="arch-arrow">↓</div>
          <div className="arch-layer">Repeated year by year, with an 80% band</div>
        </div>
        <div className="mt-3 pt-2 border-top-subtle fs-11 text-3">
          <strong>Tested on years it never saw:</strong> trained on years up to {m?.data?.train_until ?? 2016} and
          tested on the years after, it is off by {pp(mae?.model)} on average, against {pp(mae?.['last value'])} for
          repeating last year's value, {pp(mae?.['linear trend'])} for a straight-line trend
          and {pp(mae?.['historical mean'])} for the average so far.
        </div>
        <div className="mt-2 fs-11 text-3">
          It extends one organism's trend for one drug. It cannot foresee a new resistance gene arriving or a change
          in prescribing, and a year with few lab results can swing the history.
        </div>
      </div>

      <div className="info-card mt-4">
        <h6 className="card-section-title"><i className="bi bi-alarm text-accent me-2"></i>Reading the Share</h6>
        <div className="method-steps">
          <div className="method-step">{' '}
            <span className="step-num step-success"><i className="bi bi-check-lg fs-10"></i></span>{' '}
            <div><strong className="text-emerald2">&lt; 20%</strong> resistant: the drug still works for most isolates</div>
          </div>
          <div className="method-step">{' '}
            <span className="step-num step-warning"><i className="bi bi-exclamation fs-10"></i></span>{' '}
            <div><strong className="text-amber2">20–50%</strong> resistant: test before prescribing</div>
          </div>
          <div className="method-step">{' '}
            <span className="step-num step-danger"><i className="bi bi-x-lg fs-10"></i></span>{' '}
            <div><strong className="text-rose2">&gt; 50%</strong> resistant: most isolates resist, a poor empirical choice</div>
          </div>
        </div>
      </div>
    </>
  );
}

/** Shown before the first forecast. */
export function TimelineEmpty() {
  return (
    <div className="empty-state" id="timelineEmpty">
      <div className="empty-state-icon timeline-icon"><BioIcon icon="bi-graph-up-arrow" /></div>
      <h4>Forecast a Resistance Trend</h4>
      <p>Choose an antibiotic and an organism, or upload a genome to identify the organism, to see the yearly share
        of resistant isolates in BV-BRC laboratory results and the trained model's forecast, with an 80% band.</p>
      <div className="row g-3 mt-3 text-start">
        <div className="col-md-6">
          <div className="example-box">
            <div className="example-title">What you'll see</div>
            <div className="example-content">
              <div><i className="bi bi-check text-success me-1"></i>Observed resistant share, year by year</div>
              <div><i className="bi bi-check text-success me-1"></i>The model's forecast and its 80% band</div>
              <div><i className="bi bi-check text-success me-1"></i>How many lab results each year rests on</div>
              <div><i className="bi bi-check text-success me-1"></i>The model's error against simple baselines</div>
            </div>
          </div>
        </div>
        <div className="col-md-6">
          <div className="example-box">
            <div className="example-title">Try</div>
            <div className="example-content">
              <div><span className="text-rose2">●</span> Ciprofloxacin + Salmonella</div>
              <div><span className="text-amber2">●</span> Ampicillin + Escherichia</div>
              <div><span className="text-emerald2">●</span> Meropenem + Klebsiella</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/** The simulation model and alert-level cards under the form. */
export function SimulationGuides() {
  return (
    <>
          {/* Model Architecture Info */}
          <div className="info-card mt-4">
            <h6 className="card-section-title"><BioIcon icon="bi-cpu" className="text-accent me-2" />Simulation Model</h6>
            <div className="alert-success-tok mb-3">{' '}
              <i className="bi bi-check-circle me-1"></i> <strong>Simulation, not a trained model.</strong> A logistic-growth model with hand-set, literature-based constants; it is not validated against patient data.
            </div>
            <div className="arch-box">
              <div className="arch-layer text-accent2">Genome K-mer Analysis</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-layer">GC Content + Hotspot Detection</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-layer">Antibiotic Class Profiling</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-layer text-emerald2">Logistic Growth Simulation</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-layer">Week-by-Week Timeline Output</div>
            </div>
            <div className="mt-3 pt-2 border-top-subtle fs-11 text-3">{' '}
              No trained model is used here. A CNN-LSTM was explored in the research notebook (<code>notebooks/archive/bacterial_mutation_timeline.ipynb</code>) but not deployed.
            </div>
            <div className="mt-2 fs-11 text-3">{' '}
              <strong>Checked against published data:</strong> the logistic shape fits 15 published resistance curves
              (median R&sup2; 0.91): lab evolution of <em>E. faecalis</em> under five drugs (Maltas et al. 2025, <em>PLOS Biology</em>)
              and carbapenem-resistant <em>K. pneumoniae</em> in 10 European countries (ECDC EARS-Net, 2005&ndash;2024).
              Lab resistance rises within days and hospital resistance over years, so the weeks shown here are illustrative
              and the constants are unchanged. Two limits found: the midpoint is set at 0.45 &times; the weeks you choose, so a
              longer chart moves the failure week later, and the plateau varies by country (7% to 66% for carbapenems).
            </div>
          </div>

    </>
  );
}

/** The what-if tab before its first simulation. */
export function SimulationEmpty() {
  return (
    <>
          {/* Empty State */}
          <div className="empty-state" id="simulationEmpty">
            <div className="empty-state-icon timeline-icon"><BioIcon icon="bi-activity" /></div>
            <h4>What-if: Resistance Under Treatment</h4>
            <p>Upload a bacterial FASTA genome and select an antibiotic to simulate week-by-week resistance evolution with a logistic-growth simulation. This is not a trained model: its constants are hand-set from the literature, and the weeks are illustrative.</p>
            <div className="row g-3 mt-3 text-start">
              <div className="col-md-6">
                <div className="example-box">
                  <div className="example-title">What you'll see</div>
                  <div className="example-content">
                    <div><i className="bi bi-check text-success me-1"></i>Week-by-week resistance evolution chart</div>
                    <div><i className="bi bi-check text-success me-1"></i>Treatment failure prediction week</div>
                    <div><i className="bi bi-check text-success me-1"></i>Mutation hotspot positions in genome</div>
                    <div><i className="bi bi-check text-success me-1"></i>Resistance gene activation timeline</div>
                    <div><i className="bi bi-check text-success me-1"></i>MIC fold-change progression</div>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="example-box">
                  <div className="example-title">Fast-resistance antibiotics</div>
                  <div className="example-content">
                    <div><span className="text-rose2">●</span> Ciprofloxacin: resistance in ~3–4 wks</div>
                    <div><span className="text-rose2">●</span> Ampicillin: resistance in ~4–6 wks</div>
                    <div><span className="text-amber2">●</span> Meropenem: resistance in ~6–10 wks</div>
                    <div><span className="text-emerald2">●</span> Colistin: resistance in ~10–16 wks</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
    </>
  );
}

/** The scientific background below the tool. */
export function TimelineBackground() {
  return (
    <>
      {/* ── Scientific Background ───────────────────────────────────── */}
      <div className="mt-5">
        <div className="mb-4">
          <div className="sec-eyebrow">Evolutionary Biology</div>
          <div className="sec-title">Understanding Bacterial Resistance Evolution</div>
          <div className="sec-sub">Antibiotic resistance evolves through mutation, selection, and gene transfer. The forecast above does not model these steps: it learns how the resistant share has moved from year to year in laboratory surveillance data.</div>
        </div>

        <div className="row g-4 mb-4">
          <div className="col-md-3">
            <div className="crisis-card rose h-100">
              <div className="crisis-icon"><BioIcon icon="bi-activity" className="text-rose2" /></div>
              <div className="crisis-val">Selection</div>
              <div className="fw-600 mb-2 text-rose2">Drug Pressure</div>
              <div className="crisis-desc">Every course of an antibiotic kills susceptible cells and leaves resistant ones to grow. The more a drug is used, the faster the resistant share of a population rises, which is the trend the yearly lab results record.</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="crisis-card amber h-100">
              <div className="crisis-icon"><i className="bi bi-shuffle text-amber2"></i></div>
              <div className="crisis-val">HGT</div>
              <div className="fw-600 mb-2 text-amber2">Horizontal Gene Transfer</div>
              <div className="crisis-desc">Bacteria exchange resistance genes via conjugation (plasmids), transformation (naked DNA), and transduction (phage). A plasmid spreading through a population can make the resistant share jump within a year or two, a change no trend model can see coming.</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="crisis-card indigo h-100">
              <div className="crisis-icon"><i className="bi bi-clipboard-data text-indigo2"></i></div>
              <div className="crisis-val">Surveillance</div>
              <div className="fw-600 mb-2 text-indigo2">Yearly Lab Results</div>
              <div className="crisis-desc">The model learns from BV-BRC laboratory results that carry a collection year, grouped per genus and antibiotic. A year counts only with at least 20 results, and years with under 30 are drawn hollow on the chart, since a handful of isolates can swing the share.</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="crisis-card blue h-100">
              <div className="crisis-icon"><i className="bi bi-bezier2"></i></div>
              <div className="crisis-val">Genes</div>
              <div className="fw-600 mb-2 text-accent">Resistance Gene Activation</div>
              <div className="crisis-desc">Each antibiotic class selects for characteristic resistance genes. Beta-lactams select for blaTEM/blaKPC; fluoroquinolones select for gyrA mutations and qnr genes; aminoglycosides for AMEs. Whether an isolate counts as resistant follows the clinical breakpoints from{' '}
                <a href="https://www.eucast.org/clinical_breakpoints/" target="_blank" rel="noopener" className="src-link">EUCAST</a> /{' '}
                <a href="https://clsi.org/standards/products/microbiology/documents/m100/" target="_blank" rel="noopener" className="src-link">CLSI M100</a>.
              </div>
            </div>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-5">
            <div className="glass-card h-100">
              <h6 className="card-section-title"><i className="bi bi-clock-history text-accent me-2"></i>Resistance Mechanisms by Drug Class</h6>
              <p className="fs-11 text-3 mb-2">{' '}
                Background on the mechanisms: <a href="https://www.who.int/publications/i/item/9789240062702" target="_blank" rel="noopener" className="src-link">WHO GLASS 2022</a> ·{' '}
                <a href="https://www.eucast.org/" target="_blank" rel="noopener" className="src-link">EUCAST</a> ·{' '}
                <a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext" target="_blank" rel="noopener" className="src-link">Murray et al., Lancet 2022</a>
              </p>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0">
                  <thead><tr><th>Antibiotic Class</th><th>Primary Mechanism</th></tr></thead>
                  <tbody>
                    <tr><td className="fw-500">Fluoroquinolones</td><td className="small text-muted">QRDR mutations (gyrA, parC)</td></tr>
                    <tr><td className="fw-500">Beta-Lactams</td><td className="small text-muted">Beta-lactamase acquisition</td></tr>
                    <tr><td className="fw-500">Aminoglycosides</td><td className="small text-muted">Enzymatic modification (AMEs)</td></tr>
                    <tr><td className="fw-500">Carbapenems</td><td className="small text-muted">Carbapenemase (KPC, NDM)</td></tr>
                    <tr><td className="fw-500">Polymyxins</td><td className="small text-muted">LPS modification (mcr genes)</td></tr>
                    <tr><td className="fw-500">Glycopeptides</td><td className="small text-muted">Cell wall precursor alteration</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div className="col-lg-7">
            <div className="glass-card h-100">
              <h6 className="card-section-title"><i className="bi bi-shield-plus text-accent me-2"></i>Clinical Implications &amp; Antimicrobial Stewardship</h6>
              <div className="row g-3">
                <div className="col-md-6">
                  <div className="how-step how-step-compact mb-0">
                    <div className="how-num how-num-md step-danger"><i className="bi bi-stopwatch fs-14"></i></div>
                    <div>
                      <div className="how-title fs-13">De-escalation</div>
                      <div className="how-desc fs-12">Switch from broad-spectrum to narrow-spectrum antibiotics as soon as culture sensitivity data confirms susceptibility. This helps slow down resistance development.</div>
                    </div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="how-step how-step-compact mb-0">
                    <div className="how-num how-num-md step-success"><i className="bi bi-arrow-repeat fs-14"></i></div>
                    <div>
                      <div className="how-title fs-13">Antibiotic Cycling</div>
                      <div className="how-desc fs-12">Rotating between drug classes at the population level can slow accumulation of resistance genes in the bacterial gene pool.</div>
                    </div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="how-step how-step-compact mb-0">
                    <div className="how-num how-num-md step-sky"><i className="bi bi-people fs-14"></i></div>
                    <div>
                      <div className="how-title fs-13">Combination Therapy</div>
                      <div className="how-desc fs-12">Using two synergistic antibiotics reduces the probability that a single mutation confers resistance to both agents simultaneously.</div>
                    </div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="how-step how-step-compact mb-0">
                    <div className="how-num how-num-md step-warning"><i className="bi bi-clock fs-14"></i></div>
                    <div>
                      <div className="how-title fs-13">Optimal Duration</div>
                      <div className="how-desc fs-12">Shorter antibiotic courses reduce selective pressure, which slows the year-on-year rise the forecast tracks.</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
