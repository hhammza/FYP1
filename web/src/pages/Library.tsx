import { Link } from 'react-router';
import CopyButton from '../components/CopyButton';
import { useTitle } from '../lib/pageEffects';
import BioIcon from '../components/BioIcon';
import HeaderScene from '../components/HeaderScene';

function Code({ label, code }: { label: string; code: string }) {
  return (
    <div className="code-block">
      <div className="code-header">{' '}
        <span className="code-header-label">{label}</span>{' '}
        <CopyButton />
      </div>
      <pre className="code-content"><code>{code}</code></pre>
    </div>
  );
}

export default function Library() {
  useTitle('Python Library');
  return (
    <>
    <div className="page-header">
      <HeaderScene kind="terminal" />
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">Python Library</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon">{' '}
            <BioIcon icon="bi-box-seam" live />
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
          <div className="stat-mini-value text-indigo2">5</div>
          <div className="stat-mini-label">Trained models, plus the simulation</div>
        </div></div>
        <div className="flex-fill min-w-160"><div className="stat-mini">
          <div className="stat-mini-value text-emerald2">6 MB</div>
          <div className="stat-mini-label">Download, models bundled</div>
        </div></div>
        <div className="flex-fill min-w-160"><div className="stat-mini">
          <div className="stat-mini-value">126</div>
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
            <Code label="Terminal" code="pip install amrpredict" />
            <p className="form-hint mt-2 mb-0">{' '}
              The trained artifacts ship inside the package, so there is nothing else to
              download and it works offline. For the gene model, also install NCBI
              AMRFinderPlus (<code className="code-pill">amrfinder</code> on the PATH);
              without it, genome predictions use the k-mer model.
            </p>
          </div>

          {/* Forecast */}
          <div className="info-card mb-4">
            <h5 className="card-section-title">{' '}
              <BioIcon icon="bi-graph-up-arrow" className="text-accent me-2" />Resistance from metadata{' '}
              <span className="badge bg-success ms-1 badge-xs">LightGBM</span>
            </h5>
            <p className="text-muted">{' '}
              Use when you have the organism and, ideally, an MIC measurement. The model
              behind <Link to="/forecast">/forecast</Link>.
            </p>
            <Code label="Python" code={"import amrpredict\n\nr = amrpredict.forecast(\n    'ciprofloxacin',\n    taxon_id=562,        # NCBI taxonomy ID (562 is E. coli)\n    mic_value=4,         # mg/L\n    genus='Escherichia',\n    species='coli',\n)\n\nprint(r['prediction'])   # 'Resistant'\nprint(r['probability'])  # calibrated"} />
          </div>

          {/* Predict */}
          <div className="info-card mb-4">
            <h5 className="card-section-title">{' '}
              <BioIcon icon="bi-dna" className="text-emerald2 me-2" />Resistance from a complete genome{' '}
              <span className="badge bg-primary ms-1 badge-xs">Genes or k-mers</span>
            </h5>
            <p className="text-muted">{' '}
              The models behind <Link to="/predict">/predict</Link>: the gene model when
              AMRFinderPlus is installed, the k-mer model otherwise. Upload a complete
              assembly (100,000 bp or more); every contig is read.
            </p>
            <Code label="Python" code={"with open('genome.fna') as fh:\n    fasta = fh.read()\n\nr = amrpredict.predict_fasta(fasta, 'ciprofloxacin')\nif 'error' in r:\n    print('bad input:', r['error'])\nelse:\n    print(r['prediction'], r['model_used'])\n\namrpredict.identify_species(fasta)   # species from the genome"} />
            <p className="form-hint mt-2 mb-0">{' '}
              Short or empty input returns an <code className="code-pill">error</code> key
              instead of a prediction. It never raises, so check for it first.
            </p>
          </div>

          {/* Trend */}
          <div className="info-card mb-4">
            <h5 className="card-section-title">{' '}
              <i className="bi bi-graph-up text-accent me-2"></i>Yearly resistance trend{' '}
              <span className="badge bg-success ms-1 badge-xs">Timeline ML</span>
            </h5>
            <p className="text-muted">{' '}
              The observed yearly % resistant of a genus and antibiotic, and the trained
              model's forecast with an 80% band: the "ML trend forecast" on{' '}
              <Link to="/timeline">/timeline</Link>.
            </p>
            <Code label="Python" code={"r = amrpredict.forecast_trend('Salmonella', 'ciprofloxacin', years_ahead=5)\n\nfor f in r['forecast']:\n    print(f['year'], f['resistant_pct'], f['lo'], f['hi'])\n\namrpredict.trend_series()   # every genus and drug it can forecast"} />
          </div>

          {/* RL */}
          <div className="info-card mb-4">
            <h5 className="card-section-title">{' '}
              <i className="bi bi-signpost-split text-accent me-2"></i>Drug per week{' '}
              <span className="badge bg-info text-dark ms-1 badge-xs">RL agent</span>
            </h5>
            <p className="text-muted">{' '}
              A PPO agent trained on the simulation picks ciprofloxacin, gentamicin or
              imipenem each week, compared with fixed schedules. It learned from simulated
              episodes, not patients.
            </p>
            <Code label="Python" code={"r = amrpredict.plan_treatment('ciprofloxacin', n_weeks=52)\n\nprint(r['best'])\nprint(r['policies'][0]['policy'][:8])   # the agent's first 8 weeks"} />
          </div>

          {/* Timeline */}
          <div className="info-card mb-4">
            <h5 className="card-section-title">{' '}
              <BioIcon icon="bi-activity" className="text-rose2 me-2" />Simulate resistance evolution{' '}
              <span className="badge bg-warning text-dark ms-1 badge-xs">Simulation</span>
            </h5>
            <div className="alert alert-warning-custom mb-3">{' '}
              <i className="bi bi-exclamation-triangle me-1"></i>{' '}
              This is a deterministic biological simulation, <strong>not a trained
              model</strong>. It carries no AUC or accuracy score, so treat its output as
              illustrative.
            </div>
            <Code label="Python" code={"r = amrpredict.simulate_timeline(fasta, 'ciprofloxacin', n_weeks=8)\n\nfor w in r['timeline']:\n    print(w['week'], w['resistant_fraction'], w['mic_fold_change'])\n\nprint(r['failure_week'])      # when treatment stops working"} />
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
            <Code label="Terminal" code={"amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4\namrpredict predict genome.fna ciprofloxacin\namrpredict species genome.fna\namrpredict trend Salmonella ciprofloxacin --years 5\namrpredict plan ciprofloxacin --weeks 52\namrpredict timeline genome.fna ciprofloxacin --weeks 12\namrpredict status\n\n# composes with jq\namrpredict --compact forecast meropenem --taxon-id 287 | jq -r .prediction"} />
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
                  {([
                    ['forecast()', 'Metadata + MIC', 'yes'],
                    ['predict_fasta()', 'Complete genome', 'yes'],
                    ['identify_species()', 'Complete genome', 'yes'],
                    ['forecast_trend()', 'Genus + antibiotic', 'yes'],
                    ['plan_treatment()', 'Antibiotic', 'yes'],
                    ['simulate_timeline()', 'Genome FASTA', 'sim'],
                    ['antibiotics(), status()', 'n/a', 'n/a'],
                  ] as const).map(([fn, input, trained]) => (
                    <tr key={fn}>
                      <td><code className="code-pill">{fn}</code></td>
                      <td className="text-muted">{input}</td>
                      <td className="text-end">
                        {trained === 'yes' ? <span className="badge bg-success badge-xs">Yes</span>
                          : trained === 'sim' ? <span className="badge bg-warning text-dark badge-xs">Sim</span>
                          : <span className="text-muted">n/a</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Choosing a threshold */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-sliders text-accent me-2"></i>Choosing a threshold</h5>
            <p className="text-muted mb-3">{' '}
              <code className="code-pill">threshold</code> is the probability at or above
              which a sample is called Resistant. Each model's default was chosen on
              validation genomes to keep missed resistance near 10%; it changes the label,
              never the underlying probability.
            </p>
            <div className="how-step">{' '}
              <span className="how-num">0.15</span>{' '}
              <div><div className="how-title">Forecast default</div>
                <div className="how-desc">The metadata model, <code className="code-pill">forecast()</code>.</div></div>
            </div>
            <div className="how-step">{' '}
              <span className="how-num">0.43</span>{' '}
              <div><div className="how-title">K-mer default</div>
                <div className="how-desc">The genome model without AMRFinderPlus.</div></div>
            </div>
            <div className="how-step">{' '}
              <span className="how-num">0.58</span>{' '}
              <div><div className="how-title">Gene model default</div>
                <div className="how-desc">The genome model with AMRFinderPlus.</div></div>
            </div>
            <div className="how-step">{' '}
              <span className="how-num">&uarr;</span>{' '}
              <div><div className="how-title">Higher threshold</div>
                <div className="how-desc">Fewer false alarms, more missed resistance.</div></div>
            </div>
          </div>

          {/* Custom models */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-folder2-open text-accent me-2"></i>Your own models</h5>
            <p className="text-muted">Every entry point accepts <code className="code-pill">model_dir</code>:</p>
            <Code label="Python" code={"amrpredict.forecast(\n    'ciprofloxacin', taxon_id=562,\n    model_dir='/path/to/models',\n)"} />
            <p className="form-hint mt-2 mb-0">{' '}
              A folder laid out like <code className="code-pill">amrpredict.default_model_dir()</code>,
              produced by the project's <code className="code-pill">experiments/promote.py</code>.
            </p>
          </div>

          {/* Compatibility note */}
          <div className="info-card">
            <h5 className="card-section-title"><i className="bi bi-shield-check text-accent me-2"></i>Compatibility</h5>
            <p className="text-muted mb-2" style={{fontSize: '12.5px'}}>{' '}
              Every bundled model is a LightGBM text file or NumPy arrays, so the package
              needs only LightGBM, pandas, NumPy and joblib, and no scikit-learn.
            </p>
            <p className="text-muted mb-0" style={{fontSize: '12.5px'}}>{' '}
              The gene model was trained with AMRFinderPlus 4.2.7 and database
              <strong> 2026-08-07.1</strong>; a newer database can rename genes it never saw.
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
              The package ships the same trained artifacts this site runs on, and gives
              the same answers. Full reference and known issues are on GitHub.
            </div>
          </div>
          <div className="d-flex gap-2 flex-wrap">{' '}
            <a className="btn btn-outline-secondary btn-sm" href="https://pypi.org/project/amrpredict/" target="_blank" rel="noopener">{' '}
              <i className="bi bi-box-seam me-1"></i>PyPI
            </a>{' '}
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
