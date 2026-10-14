/* The parts of /forecast that only show text (converted from
   frontend/templates/resistance_forecast.html). */
import { Link } from 'react-router';
import { useMetrics } from '../../lib/health';

/** The page header. */
export function ForecastHeader() {
  return (
    <>
    <div className="page-header">
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">AMR Forecasting</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon lgbm-icon"><i className="bi bi-graph-up-arrow"></i></div>
          <div>
            <h1 className="page-title">AMR Resistance Forecasting</h1>
            <p className="page-subtitle">LightGBM gradient boosting to predict resistance from genomic metadata &amp; MIC values</p>
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
      <div className="d-flex gap-3 flex-wrap mb-4">
        <div className="flex-fill min-w-160">
          <div className="stat-mini">
            <div className="stat-mini-value text-indigo2">{m.lgbm.auc}</div>
            <div className="stat-mini-label">AUC-ROC (unseen genomes)</div>
          </div>
        </div>
        <div className="flex-fill min-w-160">
          <div className="stat-mini">
            <div className="stat-mini-value">{m.lgbm.train_rows_short}</div>
            <div className="stat-mini-label">Labeled AMR records</div>
          </div>
        </div>
        <div className="flex-fill min-w-160">
          <div className="stat-mini">
            <div className="stat-mini-value text-emerald2">14</div>
            <div className="stat-mini-label">Genomic features</div>
          </div>
        </div>
        <div className="flex-fill min-w-160">
          <div className="stat-mini">
            <div className="stat-mini-value text-rose2">1.27M</div>
            <div className="stat-mini-label">Annual AMR deaths (WHO)</div>
          </div>
        </div>
        <div className="flex-fill min-w-160">
          <div className="stat-mini">
            <div className="stat-mini-value text-amber2">{m.lgbm.antibiotics}</div>
            <div className="stat-mini-label">Antibiotics modeled</div>
          </div>
        </div>
      </div>
    </>
  );
}

/** The MIC reference card under the form. */
export function MicGuide() {
  return (
    <>
          {/* MIC Reference Guide */}
          <div className="info-card mt-4">
            <h6 className="card-section-title"><i className="bi bi-rulers text-accent me-2"></i>MIC Reference Guide</h6>
            <div className="method-steps">
              <div className="method-step"><span className="step-num step-success">S</span><div><strong className="text-emerald2">Susceptible:</strong> MIC is at or below the breakpoint; standard dosing is effective</div></div>
              <div className="method-step"><span className="step-num step-warning">I</span><div><strong className="text-amber2">Intermediate:</strong> MIC is near the breakpoint; higher dosing may be required</div></div>
              <div className="method-step"><span className="step-num step-danger">R</span><div><strong className="text-rose2">Resistant:</strong> MIC exceeds the breakpoint; the drug is likely ineffective</div></div>
            </div>
            <div className="mt-3 pt-2 border-top-subtle">
              <div className="text-muted fs-11">Common MIC breakpoints (EUCAST 2023)</div>
              <div className="d-flex flex-wrap gap-2 mt-2">{' '}
                <span className="feature-tag">Ciprofloxacin: ≤0.25 S</span>{' '}
                <span className="feature-tag">Ampicillin: ≤8 S</span>{' '}
                <span className="feature-tag">Meropenem: ≤2 S</span>
              </div>
            </div>
          </div>
    </>
  );
}

/** Shown before the first prediction. */
export function ForecastEmpty() {
  return (
    <>
          {/* Empty State */}
          <div className="empty-state">
            <div className="empty-state-icon lgbm-icon"><i className="bi bi-graph-up-arrow"></i></div>
            <h4>Ready to Forecast</h4>
            <p>Enter the antibiotic name and organism details, then click <strong>Predict Resistance</strong> to get the forecasting result.</p>
            <div className="row g-3 mt-3">
              <div className="col-md-6">
                <div className="example-box">
                  <div className="example-title">Example 1  High Resistance</div>
                  <div className="example-content">
                    <div>Antibiotic: <strong>ciprofloxacin</strong></div>
                    <div>Organism: <strong>Escherichia coli</strong></div>
                    <div>MIC: <strong>≥ 4 mg/L</strong></div>
                    <div className="mt-1 text-rose2">Expected: Resistant</div>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="example-box">
                  <div className="example-title">Example 2  Susceptible</div>
                  <div className="example-content">
                    <div>Antibiotic: <strong>meropenem</strong></div>
                    <div>Organism: <strong>Klebsiella pneumoniae</strong></div>
                    <div>MIC: <strong>≤ 0.5 mg/L</strong></div>
                    <div className="mt-1 text-emerald2">Expected: Susceptible</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
    </>
  );
}

/** The scientific background below the tool. */
export function ForecastBackground() {
  const m = useMetrics();
  return (
    <>
      {/* ── Scientific Background Section ──────────────────────────── */}
      <div className="mt-5">
        <div className="mb-4">
          <div className="sec-eyebrow">Scientific Background</div>
          <div className="sec-title">Understanding LightGBM-Based AMR Forecasting</div>
          <div className="sec-sub">The model uses gradient boosting on {m.lgbm.train_rows} labelled records to classify antibiotic resistance.</div>
        </div>

        <div className="row g-4 mb-4">
          <div className="col-md-4">
            <div className="crisis-card blue h-100">
              <div className="crisis-icon"><i className="bi bi-cpu text-accent"></i></div>
              <div className="crisis-val">LightGBM</div>
              <div className="fw-600 mb-2 text-accent2">Gradient Boosting Algorithm</div>
              <div className="crisis-desc">LightGBM builds an ensemble of decision trees sequentially, each correcting the errors of the previous. It uses histogram-based splitting and leaf-wise tree growth for superior speed and accuracy on tabular genomic metadata. On genomes it never saw in training it scores AUC-ROC {m.lgbm.auc_ci}.</div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="crisis-card indigo h-100">
              <div className="crisis-icon"><i className="bi bi-bar-chart-steps text-indigo2"></i></div>
              <div className="crisis-val">MIC Values</div>
              <div className="fw-600 mb-2 text-indigo2">Minimum Inhibitory Concentration</div>
              <div className="crisis-desc">MIC is the lowest antibiotic concentration that prevents visible bacterial growth. It is the gold-standard phenotypic measure of resistance. Our model log-transforms MIC values and encodes the sign (≤, =, ≥) as a separate categorical feature, capturing both measurement and directionality.</div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="crisis-card amber h-100">
              <div className="crisis-icon"><i className="bi bi-diagram-3 text-amber2"></i></div>
              <div className="crisis-val">14 Features</div>
              <div className="fw-600 mb-2 text-amber2">Genomic Feature Engineering</div>
              <div className="crisis-desc">The model uses 14 engineered features: antibiotic name, drug class, MIC value + sign, genus, species, taxon ID, and target-encoded resistance rates per antibiotic, per taxon-antibiotic pair, and per genus-antibiotic pair, capturing population-level resistance patterns.</div>
            </div>
          </div>
        </div>

        <div className="row g-4 mb-4">
          <div className="col-lg-7">
            <div className="glass-card h-100">
              <h6 className="card-section-title"><i className="bi bi-bacteria text-accent me-2"></i>WHO Priority Pathogens: Resistance Rates</h6>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0">
                  <thead><tr>
                    <th>Pathogen</th><th>Drug</th><th>Resistance Rate</th><th>Priority</th>
                  </tr></thead>
                  <tbody>
                    <tr>
                      <td className="fw-500"><em>E. coli</em></td>
                      <td>Fluoroquinolones</td>
                      <td><span className="fw-700 text-rose2">~80%</span></td>
                      <td><span className="status-badge trained">Critical</span></td>
                    </tr>
                    <tr>
                      <td className="fw-500"><em>K. pneumoniae</em></td>
                      <td>3rd-gen Cephalosporins</td>
                      <td><span className="fw-700 text-rose2">~60%</span></td>
                      <td><span className="status-badge trained">Critical</span></td>
                    </tr>
                    <tr>
                      <td className="fw-500"><em>Acinetobacter</em></td>
                      <td>Carbapenems</td>
                      <td><span className="fw-700 text-amber2">~45%</span></td>
                      <td><span className="status-badge trained">Critical</span></td>
                    </tr>
                    <tr>
                      <td className="fw-500"><em>S. aureus</em></td>
                      <td>Methicillin (MRSA)</td>
                      <td><span className="fw-700 text-amber2">~30%</span></td>
                      <td><span className="status-badge untrained">High</span></td>
                    </tr>
                    <tr>
                      <td className="fw-500"><em>P. aeruginosa</em></td>
                      <td>Carbapenems</td>
                      <td><span className="fw-700 text-amber2">~20%</span></td>
                      <td><span className="status-badge untrained">High</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="mt-2 fs-11 text-3">Source: WHO Global Antimicrobial Resistance and Use Surveillance System (GLASS) 2022</div>
            </div>
          </div>
          <div className="col-lg-5">
            <div className="glass-card h-100">
              <h6 className="card-section-title"><i className="bi bi-gear text-accent me-2"></i>Model Training Pipeline</h6>
              <div className="method-steps">
                <div className="method-step"><span className="step-num">1</span>Load every AMR CSV file from the BVBRC/PATRIC export ({m.lgbm.train_rows} training rows)</div>
                <div className="method-step"><span className="step-num">2</span>Parse MIC values, extract genus/species, merge Intermediate→Resistant</div>
                <div className="method-step"><span className="step-num">3</span>Target-encode resistance rates per antibiotic, taxon, genus (5-fold CV)</div>
                <div className="method-step"><span className="step-num">4</span>Train LightGBM with <code>is_unbalance=True</code> and early stopping (50 rounds)</div>
                <div className="method-step"><span className="step-num">5</span>Evaluate on genomes held out of training with AUC-ROC: <strong className="text-accent2">{m.lgbm.auc_ci}</strong></div>
              </div>
              <div className="mt-3 pt-2 border-top-subtle">
                <div className="d-flex gap-2 flex-wrap">{' '}
                  <span className="feature-tag">BVBRC Dataset</span>{' '}
                  <span className="feature-tag">PATRIC AMR</span>{' '}
                  <span className="feature-tag">EUCAST Breakpoints</span>{' '}
                  <span className="feature-tag">LightGBM 4.x</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Drug Class Reference */}
        <div className="glass-card">
          <h6 className="card-section-title"><i className="bi bi-capsule text-accent me-2"></i>Antibiotic Drug Classes: Mechanism of Action</h6>
          <div className="row g-3">
            <div className="col-md-3">
              <div className="example-box">
                <div className="example-title text-indigo2">Beta-Lactams</div>
                <div className="example-content">Inhibit cell wall synthesis by binding penicillin-binding proteins (PBPs). Include penicillins, cephalosporins, carbapenems. Resistance via beta-lactamase enzymes (ESBL, KPC).</div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="example-box">
                <div className="example-title text-rose2">Fluoroquinolones</div>
                <div className="example-content">Inhibit DNA gyrase and topoisomerase IV, blocking DNA replication. Include ciprofloxacin, levofloxacin. Resistance via target mutations and efflux pumps (QRDR mutations).</div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="example-box">
                <div className="example-title text-emerald2">Aminoglycosides</div>
                <div className="example-content">Bind 30S ribosomal subunit, inhibiting protein synthesis. Include gentamicin, tobramycin, amikacin. Resistance via aminoglycoside-modifying enzymes (AMEs) and 16S rRNA methylases.</div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="example-box">
                <div className="example-title text-amber2">Tetracyclines</div>
                <div className="example-content">Inhibit 30S ribosomal subunit, blocking aminoacyl-tRNA binding. Include tetracycline, doxycycline, tigecycline. Resistance via efflux pumps (tet genes) and ribosomal protection proteins.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
