import { Link } from 'react-router';
import CopyButton from '../components/CopyButton';
import { useTitle } from '../lib/pageEffects';

export default function Library() {
  useTitle('Python Library');
  return (
    <>
    <div className="page-header">
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">Python Library</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon">{' '}
            <i className="bi bi-box-seam"></i>
          </div>
          <div>
            <h1 className="page-title">amrpredict <span className="code-pill ms-1">v{__LIB_VERSION__}</span></h1>
            <p className="page-subtitle">The same models behind this site, as an installable Python package</p>
          </div>
        </div>
      </div>
    </div>


    <div className="container-xl py-4">

      {/* ── Quick stats ────────────────────────────────────────────── */}
      <div className="d-flex gap-3 flex-wrap mb-4">
        <div className="flex-fill min-w-160"><div className="stat-mini">
          <div className="stat-mini-value text-indigo2">3</div>
          <div className="stat-mini-label">Models in one API</div>
        </div></div>
        <div className="flex-fill min-w-160"><div className="stat-mini">
          <div className="stat-mini-value text-emerald2">7 MB</div>
          <div className="stat-mini-label">Models bundled, no download</div>
        </div></div>
        <div className="flex-fill min-w-160"><div className="stat-mini">
          <div className="stat-mini-value">62</div>
          <div className="stat-mini-label">Antibiotics covered</div>
        </div></div>
        <div className="flex-fill min-w-160"><div className="stat-mini">
          <div className="stat-mini-value text-amber2">3.9+</div>
          <div className="stat-mini-label">Python required</div>
        </div></div>
        <div className="flex-fill min-w-160"><div className="stat-mini">
          <div className="stat-mini-value">MIT</div>
          <div className="stat-mini-label">Licence</div>
        </div></div>
      </div>

      <div className="row g-4">

        {/* ── Left column ──────────────────────────────────────────── */}
        <div className="col-lg-7">

          {/* Install */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-download text-accent me-2"></i>Install</h5>
            <div className="code-block">
              <div className="code-header">{' '}
                <span className="code-header-label">Terminal</span>{' '}
                <CopyButton />
              </div>
              <pre className="code-content"><code>{"pip install amrpredict"}</code></pre>
            </div>
            <p className="form-hint mt-2 mb-0">{' '}
              The trained artifacts ship inside the package, so there is nothing else to
              download and it works offline.
            </p>
          </div>

          {/* Forecast */}
          <div className="info-card mb-4">
            <h5 className="card-section-title">{' '}
              <i className="bi bi-graph-up-arrow text-accent me-2"></i>Forecast from metadata{' '}
              <span className="badge bg-success ms-1 badge-xs">LightGBM</span>
            </h5>
            <p className="text-muted">{' '}
              Use when you have organism metadata and, ideally, an MIC measurement.
              This is the strongest of the three models.
            </p>
            <div className="code-block">
              <div className="code-header">{' '}
                <span className="code-header-label">Python</span>{' '}
                <CopyButton />
              </div>
              <pre className="code-content"><code>{"import amrpredict\n\nr = amrpredict.forecast(\n    'ciprofloxacin',\n    taxon_id=562,        # NCBI taxonomy ID (562 is E. coli)\n    mic_value=4,         # mg/L\n    genus='Escherichia',\n    species='coli',\n)\n\nprint(r['prediction'])   # 'Susceptible'\nprint(r['confidence'])   # 89.9"}</code></pre>
            </div>
          </div>

          {/* Predict */}
          <div className="info-card mb-4">
            <h5 className="card-section-title">{' '}
              <i className="bi bi-dna text-emerald2 me-2"></i>Predict from a genome{' '}
              <span className="badge bg-primary ms-1 badge-xs">K-mer RF</span>
            </h5>
            <p className="text-muted">{' '}
              Use when sequence is all you have. FASTA is cleaned to plain ACGT and
              capped at 500,000 bp.
            </p>
            <div className="code-block">
              <div className="code-header">{' '}
                <span className="code-header-label">Python</span>{' '}
                <CopyButton />
              </div>
              <pre className="code-content"><code>{"with open('genome.fasta') as fh:\n    r = amrpredict.predict_fasta(fh.read(), 'ciprofloxacin')\n\nif 'error' in r:\n    print('bad input:', r['error'])\nelse:\n    print(r['prediction'], r['gc_content'])"}</code></pre>
            </div>
            <p className="form-hint mt-2 mb-0">{' '}
              Short or empty input returns an <code className="code-pill">error</code> key
              instead of a prediction. It never raises, so check for it first.
            </p>
          </div>

          {/* Timeline */}
          <div className="info-card mb-4">
            <h5 className="card-section-title">{' '}
              <i className="bi bi-activity text-rose2 me-2"></i>Simulate resistance evolution{' '}
              <span className="badge bg-warning text-dark ms-1 badge-xs">Simulation</span>
            </h5>
            <div className="alert alert-warning-custom mb-3">{' '}
              <i className="bi bi-exclamation-triangle me-1"></i>{' '}
              This is a deterministic biological simulation, <strong>not a trained
              model</strong>. It carries no AUC or accuracy score, so treat its output as
              illustrative.
            </div>
            <div className="code-block">
              <div className="code-header">{' '}
                <span className="code-header-label">Python</span>{' '}
                <CopyButton />
              </div>
              <pre className="code-content"><code>{"r = amrpredict.simulate_timeline(fasta, 'ciprofloxacin', n_weeks=8)\n\nfor w in r['timeline']:\n    print(w['week'], w['resistant_fraction'], w['mic_fold_change'])\n\nprint(r['failure_week'])      # when treatment stops working\nprint(r['resistance_genes'])  # gyrA, gyrB, parC ..."}</code></pre>
            </div>
            <p className="form-hint mt-2 mb-0">{' '}
              <code className="code-pill">n_weeks=8</code> returns <strong>9</strong> entries. Week 0 is the untreated baseline.
            </p>
          </div>

          {/* CLI */}
          <div className="info-card">
            <h5 className="card-section-title"><i className="bi bi-terminal text-accent me-2"></i>Command line</h5>
            <p className="text-muted">{' '}
              Every command prints JSON to stdout; diagnostics go to stderr, so output
              pipes cleanly.
            </p>
            <div className="code-block">
              <div className="code-header">{' '}
                <span className="code-header-label">Terminal</span>{' '}
                <CopyButton />
              </div>
              <pre className="code-content"><code>{"amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4\namrpredict predict genome.fasta ciprofloxacin --threshold 0.6\namrpredict timeline genome.fasta ciprofloxacin --weeks 12\namrpredict antibiotics\namrpredict status\n\n# composes with jq\namrpredict --compact forecast meropenem --taxon-id 287 | jq -r .prediction\ncat genome.fasta | amrpredict predict - ciprofloxacin"}</code></pre>
            </div>
          </div>

        </div>

        {/* ── Right column ─────────────────────────────────────────── */}
        <div className="col-lg-5">

          {/* API summary */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-code-slash text-accent me-2"></i>The API</h5>
            <div className="table-responsive">
              <table className="table table-custom table-sm align-middle mb-0">
                <thead>
                  <tr>
                    <th>Function</th><th>Input</th><th className="text-end">Trained</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><code className="code-pill">forecast()</code></td>
                    <td className="text-muted">Metadata + MIC</td>
                    <td className="text-end"><span className="badge bg-success badge-xs">Yes</span></td>
                  </tr>
                  <tr>
                    <td><code className="code-pill">predict_fasta()</code></td>
                    <td className="text-muted">Genome FASTA</td>
                    <td className="text-end"><span className="badge bg-success badge-xs">Yes</span></td>
                  </tr>
                  <tr>
                    <td><code className="code-pill">simulate_timeline()</code></td>
                    <td className="text-muted">Genome FASTA</td>
                    <td className="text-end"><span className="badge bg-warning text-dark badge-xs">Sim</span></td>
                  </tr>
                  <tr>
                    <td><code className="code-pill">antibiotics()</code></td>
                    <td className="text-muted">n/a</td>
                    <td className="text-end text-muted">n/a</td>
                  </tr>
                  <tr>
                    <td><code className="code-pill">status()</code></td>
                    <td className="text-muted">n/a</td>
                    <td className="text-end text-muted">n/a</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Choosing a threshold */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-sliders text-accent me-2"></i>Choosing a threshold</h5>
            <p className="text-muted mb-3">{' '}
              <code className="code-pill">threshold</code> is the probability at or above
              which a sample is called Resistant. It changes the label, never the
              underlying probability.
            </p>
            <div className="how-step">{' '}
              <span className="how-num">0.3</span>{' '}
              <div><div className="how-title">Higher sensitivity</div>
                <div className="how-desc">More resistance calls. Use when missing resistance is costly.</div></div>
            </div>
            <div className="how-step">{' '}
              <span className="how-num">0.4</span>{' '}
              <div><div className="how-title">Forecast default</div>
                <div className="how-desc">Balanced for the LightGBM model.</div></div>
            </div>
            <div className="how-step">{' '}
              <span className="how-num">0.5</span>{' '}
              <div><div className="how-title">K-mer default</div>
                <div className="how-desc">Balanced for genome-based prediction.</div></div>
            </div>
            <div className="how-step">{' '}
              <span className="how-num">0.7</span>{' '}
              <div><div className="how-title">Higher specificity</div>
                <div className="how-desc">Fewer, more confident calls. Use when false alarms are costly.</div></div>
            </div>
          </div>

          {/* Custom models */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-folder2-open text-accent me-2"></i>Your own models</h5>
            <p className="text-muted">Every entry point accepts <code className="code-pill">model_dir</code>:</p>
            <div className="code-block">
              <div className="code-header">{' '}
                <span className="code-header-label">Python</span>{' '}
                <CopyButton />
              </div>
              <pre className="code-content"><code>{"amrpredict.forecast(\n    'ciprofloxacin', taxon_id=562,\n    model_dir='/path/to/models',\n)"}</code></pre>
            </div>
            <p className="form-hint mt-2 mb-0">{' '}
              Retrain artifacts with <code className="code-pill">train_models.py</code>.
            </p>
          </div>

          {/* Compatibility note */}
          <div className="info-card">
            <h5 className="card-section-title"><i className="bi bi-shield-check text-accent me-2"></i>Compatibility</h5>
            <p className="text-muted mb-2" style={{fontSize: '12.5px'}}>{' '}
              The k-mer model is a pickled scikit-learn estimator, so the dependency is
              pinned to <code className="code-pill">&gt;=1.3,&lt;2.0</code>. Unpickling across
              a major version is unsupported and would produce wrong numbers rather than
              failing loudly.
            </p>
            <p className="text-muted mb-0" style={{fontSize: '12.5px'}}>{' '}
              Artifacts were built with scikit-learn <strong>1.6.1</strong>. The LightGBM
              model is unaffected, because it uses LightGBM's own version-stable text
              format.
            </p>
          </div>

        </div>
      </div>

      {/* ── Footer note ──────────────────────────────────────────── */}
      <div className="info-card mt-4">
        <div className="d-flex flex-wrap align-items-center justify-content-between gap-3">
          <div>
            <div className="how-title mb-1">Source and documentation</div>
            <div className="how-desc">{' '}
              The package ships the same trained artifacts this site runs on.
              Full reference and known issues are on GitHub.
            </div>
          </div>
          <div className="d-flex gap-2 flex-wrap">{' '}
            <a className="btn btn-outline-secondary btn-sm" href="https://github.com/hhammza/FYP1/tree/main/amrpredict-lib" target="_blank" rel="noopener">{' '}
              <i className="bi bi-github me-1"></i>Source
            </a>{' '}
            <a className="btn btn-outline-secondary btn-sm" href="https://github.com/hhammza/FYP1/blob/main/amrpredict-lib/docs/api-reference.md" target="_blank" rel="noopener">{' '}
              <i className="bi bi-book me-1"></i>API reference
            </a>{' '}
            <a className="btn btn-outline-secondary btn-sm" href="https://github.com/hhammza/FYP1/blob/main/amrpredict-lib/docs/known-issues.md" target="_blank" rel="noopener">{' '}
              <i className="bi bi-exclamation-circle me-1"></i>Known issues
            </a>
          </div>
        </div>
      </div>

    </div>
    </>
  );
}
