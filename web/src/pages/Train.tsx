/* /train: start a training run or reload the served models, both behind
   the admin password (sent as X-Admin-Token; frontend/templates/train.html).
   A run saves a candidate to trained_models/candidates/: the served model is
   only replaced by experiments/promote.py. */
import { useState } from 'react';
import { Link } from 'react-router';
import { useHealth } from '../lib/health';
import { apiPost, errorText } from '../lib/api';
import CopyButton from '../components/CopyButton';
import { useToast } from '../components/Toasts';
import { useTitle } from '../lib/pageEffects';
import type { ModelStatus } from '../lib/types';

/** "lgbm_forecasting: ✅ Trained | kmer_resistance: ⚠️ Heuristic", as train.js showed it. */
export function reloadSummary(models: Record<string, ModelStatus> | undefined): string {
  return Object.entries(models || {})
    .map(([k, v]) => `${k}: ${v.trained ? '✅ Trained' : '⚠️ Heuristic'}`)
    .join('  |  ');   // the &nbsp; spacing train.js used
}

export default function Train() {
  useTitle('Train Models');
  const { metrics: m, refresh } = useHealth();
  const toast = useToast();
  const [token, setToken] = useState('');
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);
  const [error, setError] = useState('');
  const [training, setTraining] = useState<'lgbm' | 'kmer' | null>(null);
  const [reloading, setReloading] = useState(false);
  const [reloaded, setReloaded] = useState<{ ok: boolean; text: string } | null>(null);

  function needToken(): boolean {
    if (token) return false;
    toast('Enter the admin password first.', 'error', 'Password needed');
    document.getElementById('adminToken')?.focus();
    return true;
  }

  async function train(model: 'lgbm' | 'kmer') {
    if (needToken()) return;
    setTraining(model);
    setResult(null);
    setError('');
    try {
      setResult(await apiPost<{ status: string; message: string }>('train/', { model }, { headers: { 'X-Admin-Token': token } }));
    } catch (e) {
      setError(errorText(e));
    } finally {
      setTraining(null);
      window.scrollTo({ top: 0, behavior: 'smooth' });   // the answer is at the top, as after the Flask page's reload
    }
  }

  async function reload() {
    setReloading(true);
    try {
      const data = await apiPost<{ models?: Record<string, ModelStatus> }>('reload/', {}, { headers: { 'X-Admin-Token': token } });
      // the lists and model numbers may have changed
      try { Object.keys(sessionStorage).filter(k => k.startsWith('amr_')).forEach(k => sessionStorage.removeItem(k)); } catch { /* storage blocked */ }
      refresh();
      setReloaded({ ok: true, text: reloadSummary(data.models) });
      toast('Models reloaded successfully', 'success', 'Reload Complete');
    } catch (e) {
      setReloaded({ ok: false, text: errorText(e) });
      toast(errorText(e), 'error', 'Reload Failed');
    } finally {
      setReloading(false);
    }
  }

  const trainButton = (model: 'lgbm' | 'kmer', cls: string, label: string) => (
    <button type="button" className={cls} disabled={training !== null} onClick={() => train(model)}>
      {training === model
        ? <><span className="spinner-border spinner-border-sm me-2" role="status"></span>Processing…</>
        : <><i className="bi bi-play-circle me-2"></i>{label}</>}
    </button>
  );
  return (
    <>
    <div className="page-header">
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">Train Models</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon">{' '}
            <i className="bi bi-cpu"></i>
          </div>
          <div>
            <h1 className="page-title">Model Training</h1>
            <p className="page-subtitle">Train ML models on your local dataset using LightGBM &amp; K-mer RandomForest</p>
          </div>
        </div>
      </div>
    </div>


    <div className="container-xl py-4">

      {result && (
        <div className="alert alert-success-custom mb-4">
          <i className="bi bi-check-circle me-2"></i>{' '}
          <strong>{result.status}</strong>: {result.message}
        </div>
      )}
      {error && (
        <div className="alert alert-danger-custom mb-4">
          <i className="bi bi-exclamation-circle me-2"></i>{error}
        </div>
      )}

      {/* Admin password: sent to the backend as X-Admin-Token */}
      <div className="form-card mb-4">{' '}
        <label htmlFor="adminToken" className="form-label-custom">Admin password <span className="required">*</span></label>{' '}
        <input type="password" id="adminToken" className="form-control form-control-custom" autoComplete="current-password" placeholder="Needed to train or reload models"
               value={token} onChange={e => setToken(e.target.value)} />{' '}
        <small className="text-muted">The <code>ADMIN_TOKEN</code> set on the backend. Without it, training and reloading are refused.</small>
      </div>

      <div className="row g-4">

        {/* LightGBM Training */}
        <div className="col-lg-6">
          <div className="form-card h-100">
            <div className="d-flex align-items-center gap-3 mb-3">
              <div className="model-icon lgbm-icon"><i className="bi bi-graph-up-arrow"></i></div>
              <div>
                <h5 className="mb-0">LightGBM AMR Forecasting</h5>{' '}
                <small className="text-muted">Gradient Boosting on genomic metadata</small>
              </div>
            </div>

            <div className="alert alert-info-custom mb-3">{' '}
              <i className="bi bi-database me-2"></i>{' '}
              <strong>Dataset:</strong> <code>amr_output/</code> (3,655 CSV files with AMR phenotype data)
            </div>

            <div className="mb-3">
              <h6 className="text-muted mb-2">Training Pipeline:</h6>
              <div className="method-steps">
                <div className="method-step"><span className="step-num">1</span>Load &amp; combine every amr_output CSV</div>
                <div className="method-step"><span className="step-num">2</span>Clean: parse MIC values, extract genus/species</div>
                <div className="method-step"><span className="step-num">3</span>Target encoding: per-antibiotic resistance rates</div>
                <div className="method-step"><span className="step-num">4</span>Train LightGBM with early stopping</div>
                <div className="method-step"><span className="step-num">5</span>Save a candidate to trained_models/candidates/ (the served model is not replaced)</div>
              </div>
            </div>

            <div className="row g-2 mb-3 text-center">
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value">{m.lgbm.train_rows_short}</div><div className="stat-mini-label">Training rows</div></div></div>
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value">14</div><div className="stat-mini-label">Features</div></div></div>
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value">~4 min</div><div className="stat-mini-label">Train time</div></div></div>
            </div>

            {trainButton('lgbm', 'btn btn-primary-custom w-100', 'Train LightGBM Model')}
          </div>
        </div>

        {/* K-mer Training */}
        <div className="col-lg-6">
          <div className="form-card h-100">
            <div className="d-flex align-items-center gap-3 mb-3">
              <div className="model-icon kmer-icon"><i className="bi bi-dna"></i></div>
              <div>
                <h5 className="mb-0">K-mer Resistance Predictor</h5>{' '}
                <small className="text-muted">RandomForest on 4-mer frequency spectra</small>
              </div>
            </div>

            <div className="alert alert-info-custom mb-3">{' '}
              <i className="bi bi-database me-2"></i>{' '}
              <strong>Dataset:</strong> <code>mapped_output/</code> + <code>fasta_output/</code> ({m.kmer.genomes_total} genomes with a FASTA)
            </div>

            <div className="mb-3">
              <h6 className="text-muted mb-2">Training Pipeline:</h6>
              <div className="method-steps">
                <div className="method-step"><span className="step-num">1</span>Load mapped CSVs with fasta_path column</div>
                <div className="method-step"><span className="step-num">2</span>Read FASTA files, extract 4-mer frequencies (256 features)</div>
                <div className="method-step"><span className="step-num">3</span>Combine with antibiotic one-hot encoding</div>
                <div className="method-step"><span className="step-num">4</span>Train RandomForest (100 trees, balanced weights)</div>
                <div className="method-step"><span className="step-num">5</span>Save a candidate to trained_models/candidates/ (the served model is not replaced)</div>
              </div>
            </div>

            <div className="row g-2 mb-3 text-center">
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value">{m.kmer.genomes_total}</div><div className="stat-mini-label">Genomes</div></div></div>
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value">256+N</div><div className="stat-mini-label">Features</div></div></div>
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value">~1 h</div><div className="stat-mini-label">Train time</div></div></div>
            </div>

            {trainButton('kmer', 'btn btn-primary-custom w-100 btn-success-custom', 'Train K-mer Model')}
          </div>
        </div>

        {/* Mutation Timeline Model */}
        <div className="col-lg-6">
          <div className="form-card h-100">
            <div className="d-flex align-items-center gap-3 mb-3">
              <div className="model-icon timeline-icon"><i className="bi bi-activity"></i></div>
              <div>
                <h5 className="mb-0">Mutation Timeline</h5>{' '}
                <small className="text-muted">Simulation, nothing to train</small>
              </div>
            </div>
            <div className="alert alert-warning-custom mb-3">{' '}
              <i className="bi bi-info-circle me-2"></i>{' '}
              The timeline is a logistic-growth simulation with hand-set constants, so there is no model to train here.
              A CNN-LSTM was explored in the research notebook (<code>notebooks/archive/bacterial_mutation_timeline.ipynb</code>) but not deployed.
            </div>
            <div className="method-steps">
              <div className="method-step"><span className="step-num">1</span>Read the genome's GC content to set the starting resistant share</div>
              <div className="method-step"><span className="step-num">2</span>Look up the antibiotic's growth profile (peak and speed, from the literature)</div>
              <div className="method-step"><span className="step-num">3</span>Simulate susceptible, intermediate and resistant shares week by week</div>
            </div>
            <div className="alert alert-success-custom mt-3">{' '}
              <i className="bi bi-check-circle me-2"></i>{' '}
              <strong>Currently running:</strong> the logistic-growth simulation.
              Label its output "Simulation, not a trained model" wherever it is shown.
            </div>
          </div>
        </div>

        {/* Formulation Forecasting (unavailable) */}
        <div className="col-lg-6">
          <div className="form-card model-card-disabled h-100">
            <div className="d-flex align-items-center gap-3 mb-3">
              <div className="model-icon formulation-icon"><i className="bi bi-capsule"></i></div>
              <div>
                <h5 className="mb-0">Formulation Forecasting</h5>{' '}
                <small className="text-danger">Dataset Not Available</small>
              </div>
            </div>
            <div className="alert alert-warning-custom mb-3">{' '}
              <i className="bi bi-database-x me-2"></i>{' '}
              This model requires a pharmaceutical formulation dataset which is not currently available in the project directory.
            </div>
            {/* train.html had a <ul> inside a <p>, which a browser cannot nest: it ends
                the paragraph before the list and turns the stray </p> into an empty one.
                This is the page as browsers drew it. */}
            <p className="text-muted">The formulation forecasting model would predict:</p>
            <ul className="text-muted small">
              <li>Optimal antibiotic formulation types</li>
              <li>Dosing strategies to counter resistance</li>
              <li>Drug combination effectiveness</li>
            </ul>{' '}
            Training can be enabled once the relevant dataset is provided.
            <p></p>{' '}
            <button className="btn btn-secondary w-100" disabled>{' '}
              <i className="bi bi-database-x me-2"></i>Dataset Not Available
            </button>
          </div>
        </div>
      </div>

      {/* Reload Models */}
      <div className="info-card mt-4">
        <h5 className="card-section-title"><i className="bi bi-arrow-clockwise text-accent me-2"></i>Reload Trained Models</h5>
        <p className="text-muted">After training from the command line, click below to reload models without restarting the server.</p>{' '}
        <button className="btn btn-outline-custom" type="button" disabled={reloading} onClick={reload}>
          {reloading
            ? <><span className="spinner-border spinner-border-sm me-2"></span>Reloading…</>
            : <><i className="bi bi-arrow-clockwise me-2"></i>Reload All Models</>}
        </button>
        <div id="reloadResult" className="mt-3">
          {reloaded && (
            <div className={reloaded.ok ? 'alert alert-success-custom' : 'alert alert-danger-custom'}>
              <i className={reloaded.ok ? 'bi bi-check-circle me-2' : 'bi bi-exclamation-circle me-2'}></i>{reloaded.text}
            </div>
          )}
        </div>
      </div>

      {/* Command Line Training */}
      <div className="info-card mt-4">
        <h5 className="card-section-title"><i className="bi bi-terminal text-accent me-2"></i>Command Line Training (Recommended)</h5>
        <p className="text-muted">For best performance, run training from the command line in the backend directory:</p>
        <div className="code-block">
          <div className="code-header">{' '}
            <span className="text-muted">Terminal</span>{' '}
            <CopyButton />
          </div>
          <pre className="code-content"><code>{"# Navigate to backend directory\ncd path/to/FYP/backend\n\n# Train all models (LightGBM + K-mer)\npython train_models.py --model all\n\n# Or train individually:\npython train_models.py --model lgbm   # LightGBM only\npython train_models.py --model kmer   # K-mer model only\n"}</code></pre>
        </div>
      </div>

    </div>
    </>
  );
}
