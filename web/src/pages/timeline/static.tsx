/* The parts of /timeline that only show text (converted from
   frontend/templates/mutation_timeline.html). */
import { Link } from 'react-router';
import { useMetrics } from '../../lib/health';

/** The page header. */
export function TimelineHeader() {
  return (
    <>
    <div className="page-header">
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">Mutation Timeline</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon timeline-icon"><i className="bi bi-activity"></i></div>
          <div>
            <h1 className="page-title">Bacterial Mutation Timeline</h1>
            <p className="page-subtitle">Week-by-week resistance evolution using a biologically-informed logistic growth simulation</p>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}

/** The numbers strip above the form. */
export function ContextStrip() {
  const m = useMetrics();
  return (
    <>
      {/* ── Model Info Strip ──────────────────────────────────────── */}
      <div className="d-flex gap-3 flex-wrap mb-4">
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value text-rose2">Bio-Sim</div>
            <div className="stat-mini-label">Active model mode</div>
          </div>
        </div>
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value">2–24</div>
            <div className="stat-mini-label">Simulation weeks</div>
          </div>
        </div>
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value text-amber2">10+</div>
            <div className="stat-mini-label">Resistance genes tracked</div>
          </div>
        </div>
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value text-indigo2">{m.kmer.genomes_total}</div>
            <div className="stat-mini-label">Training genomes</div>
          </div>
        </div>
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value text-emerald2">50%</div>
            <div className="stat-mini-label">Treatment failure threshold</div>
          </div>
        </div>
      </div>
    </>
  );
}

/** The simulation model and alert-level cards under the form. */
export function SimulationGuides() {
  return (
    <>
          {/* Model Architecture Info */}
          <div className="info-card mt-4">
            <h6 className="card-section-title"><i className="bi bi-cpu text-accent me-2"></i>Simulation Model</h6>
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

          {/* Clinical Alert Thresholds */}
          <div className="info-card mt-4">
            <h6 className="card-section-title"><i className="bi bi-alarm text-accent me-2"></i>Clinical Alert Levels</h6>
            <div className="method-steps">
              <div className="method-step">{' '}
                <span className="step-num step-success"><i className="bi bi-check-lg fs-10"></i></span>{' '}
                <div><strong className="text-emerald2">&lt; 20%</strong> Resistant: treatment is effective, continue therapy</div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num step-warning"><i className="bi bi-exclamation fs-10"></i></span>{' '}
                <div><strong className="text-amber2">20–50%</strong> Resistant: escalate monitoring and consider rotation</div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num step-danger"><i className="bi bi-x-lg fs-10"></i></span>{' '}
                <div><strong className="text-rose2">&gt; 50%</strong> Resistant  <strong>treatment failure</strong>, switch antibiotic class</div>
              </div>
            </div>
          </div>
    </>
  );
}

/** Shown before the first simulation. */
export function TimelineEmpty() {
  return (
    <>
          {/* Empty State */}
          <div className="empty-state">
            <div className="empty-state-icon timeline-icon"><i className="bi bi-activity"></i></div>
            <h4>Generate Resistance Timeline</h4>
            <p>Upload a bacterial FASTA genome and select an antibiotic to simulate week-by-week resistance evolution with a logistic-growth simulation.</p>
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
          <div className="sec-sub">Antibiotic resistance evolves through mutation, selection, and gene transfer. Our simulation models these population dynamics with logistic growth, using hand-set constants per antibiotic class whose curve shape has been checked against published data.</div>
        </div>

        <div className="row g-4 mb-4">
          <div className="col-md-3">
            <div className="crisis-card rose h-100">
              <div className="crisis-icon"><i className="bi bi-activity text-rose2"></i></div>
              <div className="crisis-val">Logistic</div>
              <div className="fw-600 mb-2 text-rose2">Population Growth Model</div>
              <div className="crisis-desc">Resistance fraction follows a logistic S-curve: slow initial spread, exponential acceleration, then plateau. Each antibiotic has its own mutation speed, peak resistance and growth rate. These are hand-set from the literature, not fitted to data; only the curve's shape has been checked against published resistance curves.</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="crisis-card amber h-100">
              <div className="crisis-icon"><i className="bi bi-shuffle text-amber2"></i></div>
              <div className="crisis-val">HGT</div>
              <div className="fw-600 mb-2 text-amber2">Horizontal Gene Transfer</div>
              <div className="crisis-desc">Bacteria exchange resistance genes via conjugation (plasmids), transformation (naked DNA), and transduction (phage). Our model accounts for HGT acceleration by increasing the logistic growth rate when high-GC genomic regions (insertion sites) are detected.</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="crisis-card indigo h-100">
              <div className="crisis-icon"><i className="bi bi-geo-alt text-indigo2"></i></div>
              <div className="crisis-val">Hotspots</div>
              <div className="fw-600 mb-2 text-indigo2">Mutation Hotspot Detection</div>
              <div className="crisis-desc">Genomic windows with elevated GC content and tandem repeat density are scored as mutation hotspots. These are regions where transposons and integrons insert resistance cassettes. The model identifies the top 10 highest-risk positions in your submitted genome.</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="crisis-card blue h-100">
              <div className="crisis-icon"><i className="bi bi-bezier2"></i></div>
              <div className="crisis-val">Genes</div>
              <div className="fw-600 mb-2 text-accent">Resistance Gene Activation</div>
              <div className="crisis-desc">Each antibiotic class activates characteristic resistance genes over time. Beta-lactams select for blaTEM/blaKPC; fluoroquinolones select for gyrA mutations and qnr genes; aminoglycosides for AMEs. Activation timing reflects clinical breakpoint data from{' '}
                <a href="https://www.eucast.org/clinical_breakpoints/" target="_blank" rel="noopener" className="src-link">EUCAST</a> /{' '}
                <a href="https://clsi.org/standards/products/microbiology/documents/m100/" target="_blank" rel="noopener" className="src-link">CLSI M100</a>.
              </div>
            </div>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-5">
            <div className="glass-card h-100">
              <h6 className="card-section-title"><i className="bi bi-clock-history text-accent me-2"></i>Resistance Development Timeline by Drug Class</h6>
              <p className="fs-11 text-3 mb-2">{' '}
                Illustrative speeds used by this simulation, not measured timescales: in published data resistance
                rises within days in lab evolution and over years in hospital surveillance (Dataset 5).
                Background on the mechanisms: <a href="https://www.who.int/publications/i/item/9789240062702" target="_blank" rel="noopener" className="src-link">WHO GLASS 2022</a> ·{' '}
                <a href="https://www.eucast.org/" target="_blank" rel="noopener" className="src-link">EUCAST</a> ·{' '}
                <a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext" target="_blank" rel="noopener" className="src-link">Murray et al., Lancet 2022</a>
              </p>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0">
                  <thead><tr><th>Antibiotic Class</th><th>Typical Speed</th><th>Primary Mechanism</th></tr></thead>
                  <tbody>
                    <tr>
                      <td className="fw-500">Fluoroquinolones</td>
                      <td><span className="status-badge offline">3–5 weeks</span></td>
                      <td className="small text-muted">QRDR mutations (gyrA, parC)</td>
                    </tr>
                    <tr>
                      <td className="fw-500">Beta-Lactams</td>
                      <td><span className="status-badge offline">4–8 weeks</span></td>
                      <td className="small text-muted">Beta-lactamase acquisition</td>
                    </tr>
                    <tr>
                      <td className="fw-500">Aminoglycosides</td>
                      <td><span className="status-badge untrained">6–10 weeks</span></td>
                      <td className="small text-muted">Enzymatic modification (AMEs)</td>
                    </tr>
                    <tr>
                      <td className="fw-500">Carbapenems</td>
                      <td><span className="status-badge untrained">8–14 weeks</span></td>
                      <td className="small text-muted">Carbapenemase (KPC, NDM)</td>
                    </tr>
                    <tr>
                      <td className="fw-500">Polymyxins</td>
                      <td><span className="status-badge trained">10–18 weeks</span></td>
                      <td className="small text-muted">LPS modification (mcr genes)</td>
                    </tr>
                    <tr>
                      <td className="fw-500">Glycopeptides</td>
                      <td><span className="status-badge trained">12–20 weeks</span></td>
                      <td className="small text-muted">Cell wall precursor alteration</td>
                    </tr>
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
                      <div className="how-desc fs-12">Shorter antibiotic courses reduce selective pressure. The timeline model helps identify the minimum effective treatment window before resistance emerges.</div>
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
