import { Link } from 'react-router';
import { useMetrics } from '../lib/health';
import { useTitle } from '../lib/pageEffects';

export default function About() {
  useTitle('About the AMR Prediction System');
  const m = useMetrics();
  return (
    <>
    <div className="page-header">
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">About</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon">{' '}
            <i className="bi bi-info-circle"></i>
          </div>
          <div>
            <h1 className="page-title">About This Project</h1>
            <p className="page-subtitle">Forecasting Antibiotic Resistance with Machine Learning | Final Year Project</p>
          </div>
        </div>
      </div>
    </div>


    <div className="container-xl py-4">

      {/* ── Quick Stats ────────────────────────────────────────────── */}
      <div className="d-flex gap-3 flex-wrap mb-4">
        <div className="about-stat-wrap"><div className="stat-mini">
          <div className="stat-mini-value text-indigo">2</div>
          <div className="stat-mini-label">ML models + 1 bio-sim</div>
        </div></div>
        <div className="about-stat-wrap"><div className="stat-mini">
          <div className="stat-mini-value text-emerald">{m.lgbm.auc}</div>
          <div className="stat-mini-label">Forecaster AUC (unseen genomes)</div>
        </div></div>
        <div className="about-stat-wrap"><div className="stat-mini">
          <div className="stat-mini-value">{m.lgbm.train_rows_short}</div>
          <div className="stat-mini-label">Training records</div>
        </div></div>
        <div className="about-stat-wrap"><div className="stat-mini">
          <div className="stat-mini-value text-amber">{m.lgbm.antibiotics}</div>
          <div className="stat-mini-label">Antibiotics modeled</div>
        </div></div>
        <div className="about-stat-wrap"><div className="stat-mini">
          <div className="stat-mini-value text-rose">2</div>
          <div className="stat-mini-label">Backend services</div>
        </div></div>
      </div>

      <div className="row g-4">

        {/* ══ LEFT COLUMN ══════════════════════════════════════════ */}
        <div className="col-lg-8">

          {/* Project Overview */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-mortarboard text-accent me-2"></i>Project Overview</h5>
            <p className="about-body-text">{' '}
              <strong>AMRPredict</strong> is a full-stack machine learning system developed as a Final Year Project (FYP) in BioInformatics &amp; Machine Learning. The project addresses the global health crisis of <strong className="text-rose">Antimicrobial Resistance (AMR)</strong>, which the <a href="https://www.who.int/news-room/spotlight/ten-threats-to-global-health-in-2019" target="_blank" rel="noopener" className="src-link">WHO lists as one of the top ten global public health threats facing humanity</a>.
            </p>
            <p className="about-body-text">{' '}
              The system predicts whether a bacterial sample is <strong className="text-rose">Resistant</strong> or <strong className="text-emerald">Susceptible</strong> to a specific antibiotic. It uses two machine learning models trained on real genomic data from the BVBRC/PATRIC database. A third component simulates how resistance can spread through a bacterial population week by week, using a biologically grounded logistic growth model.
            </p>
            <p className="about-body-text">{' '}
              The idea behind this project is to show that machine learning applied to genomic data can <strong>predict antibiotic resistance faster and more affordably</strong> than traditional lab culture tests, giving clinicians useful information within minutes rather than waiting days for results.
            </p>
            <div className="d-flex flex-wrap gap-2 mt-3">{' '}
              <span className="feature-tag">Antimicrobial Resistance</span>{' '}
              <span className="feature-tag">Gradient Boosting</span>{' '}
              <span className="feature-tag">K-mer Analysis</span>{' '}
              <span className="feature-tag">Logistic Growth Simulation</span>{' '}
              <span className="feature-tag">BVBRC Genomic Data</span>{' '}
              <span className="feature-tag">REST API</span>
            </div>
          </div>

          {/* Objectives */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-bullseye text-accent me-2"></i>Project Objectives</h5>
            <div className="row g-3">
              <div className="col-md-6">
                <div className="how-step about-obj-step">
                  <div className="how-num about-obj-num">01</div>
                  <div>
                    <div className="how-title">Binary Resistance Classification</div>
                    <div className="how-desc">Train a LightGBM model on {m.lgbm.train_rows} labelled AMR records to classify antibiotic resistance from genomic metadata. The target was AUC-ROC 0.90; on genomes it never saw it reaches {m.lgbm.auc}.</div>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="how-step about-obj-step">
                  <div className="how-num about-obj-num">02</div>
                  <div>
                    <div className="how-title">Alignment-Free Genomic Prediction</div>
                    <div className="how-desc">Build a k-mer frequency model (LightGBM on the complete genome) that predicts resistance directly from raw FASTA sequences without needing any reference genome alignment.</div>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="how-step about-obj-step">
                  <div className="how-num about-obj-num">03</div>
                  <div>
                    <div className="how-title">Temporal Resistance Forecasting</div>
                    <div className="how-desc">Simulate week-by-week resistance evolution using a logistic growth model with hand-set constants per antibiotic class.</div>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="how-step about-obj-step">
                  <div className="how-num about-obj-num">04</div>
                  <div>
                    <div className="how-title">Production-Ready Web System</div>
                    <div className="how-desc">Deploy all models as a full-stack REST API system (Django + Flask) with an interactive web interface for clinical and research use.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Methodology */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-diagram-3 text-accent me-2"></i>Methodology</h5>

            <h6 className="about-method-h6 mt-3 mb-2">Phase 1: Data Collection and Preprocessing</h6>
            <p className="about-method-text">{' '}
              AMR phenotype data including Resistant, Susceptible, and Intermediate labels, MIC values, and organism metadata was downloaded from the BVBRC database across {m.lgbm.genera} bacterial genera. Complete genome assemblies were downloaded for {m.kmer.genomes_total} of the isolates. The data was then cleaned to remove duplicates, parse MIC strings, extract genus and species from genome names, and merge Intermediate labels into Resistant for binary classification.
            </p>

            <h6 className="about-method-h6 mt-3 mb-2">Phase 2: Feature Engineering</h6>
            <p className="about-method-text">{' '}
              Two separate feature sets were built: (1) <strong>14 tabular features</strong> for LightGBM, including MIC value, log, and sign, drug class, genus and species, as well as target-encoded resistance rates per antibiotic, taxon-antibiotic pair, and genus-antibiotic pair; and (2) <strong>256 k-mer features</strong> for the genome model, the 4-mer frequency spectrum of the complete genome assembly counted within each contig, along with GC content, genome length and the antibiotic.
            </p>

            <h6 className="about-method-h6 mt-3 mb-2">Phase 3: Model Training and Evaluation</h6>
            <p className="about-method-text">{' '}
              Both models are LightGBM, trained with <code className="font-mono">is_unbalance=True</code> and early stopping (30 rounds). The data is split <strong>by genome</strong>, 80/20: every genome is either in training or in the test set, never both, so the scores are on isolates the model never saw. The decision threshold is chosen on validation genomes, as the highest that misses at most 10% of resistant isolates (very major error), and the forecaster's probabilities are calibrated (isotonic). Each model is reported with AUC-ROC and its 95% confidence interval, AUPRC, F1, recall, and the very major and major error rates; the genome model is scored on lab-confirmed results only, because BV-BRC's computer-predicted labels were made from the genome itself.
            </p>

            <h6 className="about-method-h6 mt-3 mb-2">Phase 4: Deployment</h6>
            <p className="about-method-text">{' '}
              The trained models are saved to disk as LightGBM .txt files with their metrics, and loaded when the Django backend starts up through a model registry; every number the site shows is read from those metrics files. The Flask frontend forwards all prediction requests to the Django REST API. If a model file is missing, the forecaster falls back to a heuristic and <code className="font-mono">/predict</code> to the original K-mer RandomForest, and the page says so; the genome model refuses a partial genome (under 100,000 bp) rather than guess.
            </p>
          </div>

          {/* Models Detail */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-cpu text-accent me-2"></i>ML Models: Technical Detail</h5>

            {/* LightGBM */}
            <div className="example-box mb-3">
              <div className="d-flex align-items-center gap-2 mb-2">
                <div className="model-icon lgbm-icon about-model-icon"><i className="bi bi-graph-up-arrow"></i></div>
                <div className="example-title mb-0">Model 1: LightGBM Resistance Forecasting</div>{' '}
                <span className="status-badge trained ms-auto">AUC {m.lgbm.auc}</span>
              </div>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0"><tbody>
                  <tr><td className="text-muted about-td-label">Algorithm</td><td>Gradient Boosted Decision Trees (LightGBM 4.x)</td></tr>
                  <tr><td className="text-muted">Training data</td><td>{m.lgbm.train_rows} labeled AMR records from {m.lgbm.train_genomes} genomes (BVBRC)</td></tr>
                  <tr><td className="text-muted">Features</td><td>14 engineered features (MIC, taxonomy, drug class, target-encoded rates)</td></tr>
                  <tr><td className="text-muted">Hyperparameters</td><td>500 estimators, lr=0.05, num_leaves=63, is_unbalance=True, early_stop=30</td></tr>
                  <tr><td className="text-muted">Saved as</td><td className="font-mono">trained_models/amr_lgbm_final_model.txt</td></tr>
                  <tr><td className="text-muted">Fallback</td><td>Heuristic rule-based on per-antibiotic resistance rates + MIC adjustment</td></tr>
                </tbody></table>
              </div>
            </div>

            {/* K-mer genome model */}
            <div className="example-box mb-3">
              <div className="d-flex align-items-center gap-2 mb-2">
                <div className="model-icon kmer-icon about-model-icon"><i className="bi bi-dna"></i></div>
                <div className="example-title mb-0">Model 2: K-mer Genome Predictor</div>{' '}
                <span className="status-badge trained about-kmer-badge ms-auto">AUC {m.kmer.auc}</span>
              </div>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0"><tbody>
                  <tr><td className="text-muted about-td-label">Algorithm</td><td>LightGBM gradient-boosted trees on the complete genome assembly (replaced a 100-tree RandomForest trained on partial genomes, AUC about 0.70)</td></tr>
                  <tr><td className="text-muted">Training data</td><td>{m.kmer.train_rows} genome–antibiotic pairs from {m.kmer.train_genomes} bacterial genomes</td></tr>
                  <tr><td className="text-muted">Features</td><td>256 4-mer frequencies counted within each contig + antibiotic + GC content + genome length</td></tr>
                  <tr><td className="text-muted">Threshold</td><td>{m.kmer.threshold}, chosen on validation so that at most 10% of resistant isolates are missed</td></tr>
                  <tr><td className="text-muted">Saved as</td><td className="font-mono">trained_models/genome/model.txt</td></tr>
                  <tr><td className="text-muted">Input check</td><td>Refuses files under 100,000 bp (partial or plasmid-only); AUC is measured on lab-confirmed results only</td></tr>
                </tbody></table>
              </div>
            </div>

            {/* Timeline */}
            <div className="example-box">
              <div className="d-flex align-items-center gap-2 mb-2">
                <div className="model-icon timeline-icon about-model-icon"><i className="bi bi-activity"></i></div>
                <div className="example-title mb-0">Model 3: Mutation Timeline (Biological Simulation)</div>{' '}
                <span className="status-badge simulated ms-auto">Bio-Sim</span>
              </div>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0"><tbody>
                  <tr><td className="text-muted about-td-label">Algorithm</td><td>Logistic growth model with hand-set constants (nothing is trained)</td></tr>
                  <tr><td className="text-muted">Input</td><td>Raw FASTA sequence + antibiotic name + number of weeks (2–24)</td></tr>
                  <tr><td className="text-muted">Growth model</td><td>Sigmoid logistic curve with speed and peak parameterised per antibiotic class</td></tr>
                  <tr><td className="text-muted">Hotspot detection</td><td>Sliding GC-content + repeat-density windows → top 12 putative mutation sites</td></tr>
                  <tr><td className="text-muted">Output</td><td>Week-by-week R/S/I fractions, MIC fold-change, gene activation, failure week</td></tr>
                  <tr><td className="text-muted">Antibiotics</td><td>14 drug-specific profiles hardcoded (ciprofloxacin, ampicillin, imipenem, …)</td></tr>
                </tbody></table>
              </div>
            </div>
          </div>

          {/* System Architecture */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-layers text-accent me-2"></i>System Architecture</h5>
            <p className="about-arch-intro">This is a two-tier web application. The Flask layer handles the user interface, while the Django REST API takes care of model inference and data processing.</p>

            <div className="pipeline-diagram about-pipeline mb-4">
              <div className="pipeline-step">
                <div className="pipeline-icon"><i className="bi bi-person-fill"></i></div>
                <div className="pipeline-label">User / Browser<br /><small>localhost:5001</small></div>
              </div>
              <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
              <div className="pipeline-step">
                <div className="pipeline-icon"><i className="bi bi-layout-text-window"></i></div>
                <div className="pipeline-label">Flask Frontend<br /><small>Jinja2 + Bootstrap</small></div>
              </div>
              <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
              <div className="pipeline-step">
                <div className="pipeline-icon"><i className="bi bi-server"></i></div>
                <div className="pipeline-label">Django REST API<br /><small>localhost:8000</small></div>
              </div>
              <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
              <div className="pipeline-step">
                <div className="pipeline-icon"><i className="bi bi-cpu"></i></div>
                <div className="pipeline-label">ML Models<br /><small>LightGBM · RF · Sim</small></div>
              </div>
              <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
              <div className="pipeline-step active-step">
                <div className="pipeline-icon"><i className="bi bi-clipboard2-pulse"></i></div>
                <div className="pipeline-label">JSON Response<br /><small>+ Plotly Charts</small></div>
              </div>
            </div>

            <div className="row g-3">
              <div className="col-md-6">
                <div className="example-box">
                  <div className="example-title about-flask-title">Flask Frontend (Port 5001)</div>
                  <div className="example-content small text-muted">
                    <div>• Jinja2 templates + Bootstrap 5 dark theme</div>
                    <div>• Proxies all API calls to Django via <code>requests</code></div>
                    <div>• Handles file uploads (multipart), JSON, form POST</div>
                    <div>• Plotly.js for interactive charts (no server-side rendering)</div>
                    <div>• Animated loading states, drag-and-drop file zones</div>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="example-box">
                  <div className="example-title about-django-title">Django REST API (Port 8000)</div>
                  <div className="example-content small text-muted">
                    <div>• Django REST Framework with CORS enabled (all origins)</div>
                    <div>• Models loaded once at startup via AppConfig.ready()</div>
                    <div>• 7 endpoints: health, forecast, predict, timeline, antibiotics, train, reload</div>
                    <div>• Background thread for async model training</div>
                    <div>• Heuristic fallback if trained model unavailable</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* API Reference */}
          <div className="info-card mb-4">
            <h5 className="card-section-title"><i className="bi bi-braces text-accent me-2"></i>REST API Reference</h5>
            <p className="about-api-base">Base URL: <code className="font-mono about-api-url">http://localhost:8000/api/</code></p>
            <div className="table-responsive">
              <table className="table table-custom table-sm mb-0">
                <thead><tr><th>Method</th><th>Endpoint</th><th>Description</th><th>Key Parameters</th></tr></thead>
                <tbody>
                  <tr>
                    <td><span className="feature-tag about-api-get">GET</span></td>
                    <td className="font-mono small">health/</td>
                    <td className="small text-muted">Model status check</td>
                    <td className="small text-muted">N/A</td>
                  </tr>
                  <tr>
                    <td><span className="feature-tag about-api-post">POST</span></td>
                    <td className="font-mono small">forecast/</td>
                    <td className="small text-muted">LightGBM AMR prediction</td>
                    <td className="small font-mono">antibiotic, taxon_id, mic_value, mic_sign, genus, species, threshold</td>
                  </tr>
                  <tr>
                    <td><span className="feature-tag about-api-post">POST</span></td>
                    <td className="font-mono small">predict/</td>
                    <td className="small text-muted">K-mer FASTA prediction</td>
                    <td className="small font-mono">fasta_file (upload) OR fasta_text, antibiotic, threshold</td>
                  </tr>
                  <tr>
                    <td><span className="feature-tag about-api-post">POST</span></td>
                    <td className="font-mono small">timeline/</td>
                    <td className="small text-muted">Mutation timeline simulation</td>
                    <td className="small font-mono">fasta_file OR fasta_text, antibiotic, n_weeks</td>
                  </tr>
                  <tr>
                    <td><span className="feature-tag about-api-get">GET</span></td>
                    <td className="font-mono small">antibiotics/</td>
                    <td className="small text-muted">List of 48 supported antibiotics</td>
                    <td className="small text-muted">N/A</td>
                  </tr>
                  <tr>
                    <td><span className="feature-tag about-api-post">POST</span></td>
                    <td className="font-mono small">train/</td>
                    <td className="small text-muted">Trigger background model training</td>
                    <td className="small font-mono">model: "lgbm" | "kmer" | "all"</td>
                  </tr>
                  <tr>
                    <td><span className="feature-tag about-api-post">POST</span></td>
                    <td className="font-mono small">reload/</td>
                    <td className="small text-muted">Reload models from disk</td>
                    <td className="small text-muted">N/A</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Limitations */}
          <div className="info-card">
            <h5 className="card-section-title"><i className="bi bi-exclamation-triangle text-accent me-2"></i>Known Limitations</h5>
            <div className="row g-3">
              <div className="col-md-6">
                <div className="example-box about-limit-box">
                  <div className="example-title about-limit-title">Formulation Model Missing</div>
                  <div className="example-content small text-muted">A fourth model (Formulation Forecasting) was planned to recommend optimal dosing strategies but was left out of scope. No publicly available pharmaceutical formulation dataset was found that matched the project's genomic data.</div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="example-box about-limit-box">
                  <div className="example-title about-limit-title">No Real-Time Training Progress</div>
                  <div className="example-content small text-muted">Model training runs in a background thread. There is no WebSocket-based live progress indicator. The interface shows a "Training started" message but does not stream training logs in real time. A production system would use Celery and Redis for async task queuing.</div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="example-box about-limit-box">
                  <div className="example-title about-limit-title">Timeline is Simulation, Not Trained</div>
                  <div className="example-content small text-muted">The Mutation Timeline uses a biologically-informed logistic growth model, not a trained CNN-LSTM. While results are scientifically plausible, they are simulated rather than learned from empirical time-series data.</div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="example-box about-limit-box">
                  <div className="example-title about-limit-title">No User Authentication</div>
                  <div className="example-content small text-muted">The system has no login/authentication layer. In a clinical deployment, HIPAA/GDPR compliance would require user accounts, audit logging, and encrypted data at rest. This is a research prototype.</div>
                </div>
              </div>
            </div>
          </div>

        </div>{/* /col-lg-8 */}

        {/* ══ RIGHT COLUMN ═════════════════════════════════════════ */}
        <div className="col-lg-4">

          {/* FYP Details */}
          <div className="info-card mb-4">
            <h6 className="card-section-title"><i className="bi bi-mortarboard text-accent me-2"></i>Project Details</h6>
            <table className="table table-custom table-sm"><tbody>
              <tr><td className="text-muted">Project title</td><td className="fw-500 text-white">Forecasting Antibiotic Resistance with Machine Learning</td></tr>
              <tr><td className="text-muted">Institution</td><td className="fw-500">COMSATS University Islamabad, Lahore Campus</td></tr>
              <tr><td className="text-muted">Type</td><td className="fw-500">Final Year Project (FYP)</td></tr>
              <tr><td className="text-muted">Domain</td><td className="fw-500">BioInformatics &amp; ML</td></tr>
              <tr><td className="text-muted">Year</td><td className="fw-500">2026 – 2027</td></tr>
            </tbody></table>
          </div>

          {/* Project Members */}
          <div className="info-card mb-4">
            <h6 className="card-section-title"><i className="bi bi-people text-accent me-2"></i>Project Members</h6>
            <div className="d-flex flex-column gap-3">

              {/* Hamza Afzal */}
              <div className="d-flex align-items-center gap-3">{' '}
                <img src="https://avatars.githubusercontent.com/hhammza" alt="Hamza Afzal" width="52" height="52" className="rounded-circle border border-secondary" onError={e => { const img = e.currentTarget; if (!img.dataset.fallback) { img.dataset.fallback = '1'; img.src = 'https://ui-avatars.com/api/?name=Hamza+Afzal&background=6366f1&color=fff&size=52'; } }} />
                <div className="flex-fill">
                  <div className="fw-600 text-white about-member-name">Hamza Afzal</div>
                  <div className="d-flex gap-2 mt-1">{' '}
                    <a href="https://www.linkedin.com/in/muhammad-hamza-afzal/" target="_blank" rel="noopener" className="btn btn-outline-custom btn-sm about-member-btn d-flex align-items-center gap-1">{' '}
                      <i className="bi bi-linkedin"></i> LinkedIn
                    </a>{' '}
                    <a href="https://github.com/hhammza" target="_blank" rel="noopener" className="btn btn-outline-custom btn-sm about-member-btn d-flex align-items-center gap-1">{' '}
                      <i className="bi bi-github"></i> GitHub
                    </a>
                  </div>
                </div>
              </div>

              {/* Muhammad Ali */}
              <div className="d-flex align-items-center gap-3">{' '}
                <img src="https://avatars.githubusercontent.com/aligmirza" alt="Muhammad Ali" width="52" height="52" className="rounded-circle border border-secondary" onError={e => { const img = e.currentTarget; if (!img.dataset.fallback) { img.dataset.fallback = '1'; img.src = 'https://ui-avatars.com/api/?name=Muhammad+Ali&background=10b981&color=fff&size=52'; } }} />
                <div className="flex-fill">
                  <div className="fw-600 text-white about-member-name">Muhammad Ali</div>
                  <div className="d-flex gap-2 mt-1">{' '}
                    <a href="https://www.linkedin.com/in/maliprogmeleon/" target="_blank" rel="noopener" className="btn btn-outline-custom btn-sm about-member-btn d-flex align-items-center gap-1">{' '}
                      <i className="bi bi-linkedin"></i> LinkedIn
                    </a>{' '}
                    <a href="https://github.com/aligmirza" target="_blank" rel="noopener" className="btn btn-outline-custom btn-sm about-member-btn d-flex align-items-center gap-1">{' '}
                      <i className="bi bi-github"></i> GitHub
                    </a>
                  </div>
                </div>
              </div>

              {/* Malik Muhammad Suleman Saleh */}
              <div className="d-flex align-items-center gap-3">{' '}
                <img src="https://avatars.githubusercontent.com/Suleman-Saleh" alt="Malik Muhammad Suleman Saleh" width="52" height="52" className="rounded-circle border border-secondary" onError={e => { const img = e.currentTarget; if (!img.dataset.fallback) { img.dataset.fallback = '1'; img.src = 'https://ui-avatars.com/api/?name=Suleman+Saleh&background=f59e0b&color=fff&size=52'; } }} />
                <div className="flex-fill">
                  <div className="fw-600 text-white about-member-name">Malik Muhammad Suleman Saleh</div>
                  <div className="d-flex gap-2 mt-1">{' '}
                    <a href="https://www.linkedin.com/in/muhammad-suleman-69149a226/" target="_blank" rel="noopener" className="btn btn-outline-custom btn-sm about-member-btn d-flex align-items-center gap-1">{' '}
                      <i className="bi bi-linkedin"></i> LinkedIn
                    </a>{' '}
                    <a href="https://github.com/Suleman-Saleh" target="_blank" rel="noopener" className="btn btn-outline-custom btn-sm about-member-btn d-flex align-items-center gap-1">{' '}
                      <i className="bi bi-github"></i> GitHub
                    </a>
                  </div>
                </div>
              </div>

            </div>
          </div>

          {/* Supervision */}
          <div className="info-card mb-4">
            <h6 className="card-section-title"><i className="bi bi-person-badge text-accent me-2"></i>Supervision</h6>
            <div className="d-flex flex-column gap-3">

              {/* Supervisor */}
              <div>
                <div className="text-muted about-sup-label mb-2">Supervisor</div>
                <div className="d-flex align-items-center gap-3">{' '}
                  <img src="https://lahore.comsats.edu.pk/Images/employees/77-43-8588891734814339558.jpg" alt="Mr. Imran Latif" width="52" height="52" className="rounded-circle border border-secondary object-fit-cover" onError={e => { const img = e.currentTarget; if (!img.dataset.fallback) { img.dataset.fallback = '1'; img.src = 'https://ui-avatars.com/api/?name=Imran+Latif&background=6366f1&color=fff&size=52'; } }} />
                  <div className="flex-fill">
                    <div className="fw-600 text-white about-member-name">Mr. Imran Latif</div>
                    <div className="text-muted about-sup-dept">Lecturer, Computer Science</div>
                    <div className="text-muted about-sup-areas">Data Mining &middot; Machine Learning &middot; Databases</div>{' '}
                    <a href="https://lahore.comsats.edu.pk/employees/77" target="_blank" rel="noopener" className="btn btn-outline-custom btn-sm about-member-btn d-inline-flex align-items-center gap-1 mt-1">{' '}
                      <i className="bi bi-person-circle"></i> Profile
                    </a>
                  </div>
                </div>
              </div>

              <hr className="border-secondary my-1" />

              {/* Co-Supervisor */}
              <div>
                <div className="text-muted about-sup-label mb-2">Co-Supervisor</div>
                <div className="d-flex align-items-center gap-3">{' '}
                  <img src="https://lahore.comsats.edu.pk/Images/employees/277-119-8585741571943583130.JPG" alt="Dr. Muhammad Shahid Bhatti" width="52" height="52" className="rounded-circle border border-secondary object-fit-cover" onError={e => { const img = e.currentTarget; if (!img.dataset.fallback) { img.dataset.fallback = '1'; img.src = 'https://ui-avatars.com/api/?name=Shahid+Bhatti&background=10b981&color=fff&size=52'; } }} />
                  <div className="flex-fill">
                    <div className="fw-600 text-white about-member-name">Muhammad Shahid Bhatti</div>
                    <div className="text-muted about-sup-dept">Assistant Professor, Computer Science</div>
                    <div className="text-muted about-sup-areas">NLP &middot; Computer Vision &middot; Medical Imaging</div>{' '}
                    <a href="https://lahore.comsats.edu.pk/employees/277" target="_blank" rel="noopener" className="btn btn-outline-custom btn-sm about-member-btn d-inline-flex align-items-center gap-1 mt-1">{' '}
                      <i className="bi bi-person-circle"></i> Profile
                    </a>
                  </div>
                </div>
              </div>

            </div>
          </div>

          {/* Performance Summary */}
          <div className="info-card mb-4">
            <h6 className="card-section-title"><i className="bi bi-graph-up text-accent me-2"></i>Model Performance</h6>
            <table className="table table-custom table-sm"><tbody>
              <tr>
                <td className="text-muted">LightGBM AUC-ROC</td>
                <td><span className="about-perf-val">{m.lgbm.auc_ci}</span></td>
              </tr>
              <tr>
                <td className="text-muted">K-mer genome model AUC-ROC</td>
                <td><span className="about-perf-val">{m.kmer.auc_ci}</span></td>
              </tr>
              <tr>
                <td className="text-muted">LightGBM threshold</td>
                <td className="fw-500">{m.lgbm.threshold || 'not measured'} (very major error {m.lgbm.very_major_error}, recall {m.lgbm.recall})</td>
              </tr>
              <tr>
                <td className="text-muted">K-mer threshold</td>
                <td className="fw-500">{m.kmer.threshold || 'not measured'} (training default)</td>
              </tr>
              <tr>
                <td className="text-muted">LightGBM train size</td>
                <td className="fw-500">{m.lgbm.train_rows} rows</td>
              </tr>
              <tr>
                <td className="text-muted">K-mer train size</td>
                <td className="fw-500">{m.kmer.train_rows} pairs</td>
              </tr>
            </tbody></table>
            <p className="small text-muted mb-0">{' '}
              An earlier version of this site reported AUC 0.93 (0.9255). That figure was inflated:
              it came from a model trained on 1.6% of the data and tested on genomes it had already seen,
              with resistance rates computed from the test rows. Tested on genomes it never saw,
              that model scored 0.644. The forecaster now served scores {m.lgbm.auc_ci}{' '}
              under a genome-grouped split. The current figures on this page are read from each model's metrics file.{' '}
              <Link to="/models">Full results</Link>.
            </p>
          </div>

          {/* Data Sources */}
          <div className="info-card mb-4">
            <h6 className="card-section-title"><i className="bi bi-database text-accent me-2"></i>Data Sources</h6>
            <div className="d-flex flex-column gap-2">{' '}

              <a href="https://www.bv-brc.org/" target="_blank" rel="noopener" className="datasrc-card">
                <div className="datasrc-icon datasrc-primary"><i className="bi bi-virus2"></i></div>
                <div className="datasrc-body">
                  <div className="datasrc-name">BVBRC / PATRIC</div>
                  <div className="datasrc-desc">Primary training data: {m.lgbm.train_rows} AMR phenotype records and {m.kmer.genomes_total} FASTA genomes</div>
                </div>{' '}
                <i className="bi bi-arrow-up-right-circle-fill datasrc-arrow"></i>
              </a>{' '}

              <a href="https://www.ncbi.nlm.nih.gov/genbank/" target="_blank" rel="noopener" className="datasrc-card">
                <div className="datasrc-icon datasrc-emerald"><i className="bi bi-dna"></i></div>
                <div className="datasrc-body">
                  <div className="datasrc-name">NCBI GenBank</div>
                  <div className="datasrc-desc">Reference genome sequences and resistance gene annotations</div>
                </div>{' '}
                <i className="bi bi-arrow-up-right-circle-fill datasrc-arrow"></i>
              </a>{' '}

              <a href="https://www.eucast.org/" target="_blank" rel="noopener" className="datasrc-card">
                <div className="datasrc-icon datasrc-amber"><i className="bi bi-clipboard2-pulse"></i></div>
                <div className="datasrc-body">
                  <div className="datasrc-name">EUCAST 2023</div>
                  <div className="datasrc-desc">European clinical MIC breakpoints for resistance threshold calibration</div>
                </div>{' '}
                <i className="bi bi-arrow-up-right-circle-fill datasrc-arrow"></i>
              </a>{' '}

              <a href="https://www.who.int/initiatives/glass" target="_blank" rel="noopener" className="datasrc-card">
                <div className="datasrc-icon datasrc-rose"><i className="bi bi-globe2"></i></div>
                <div className="datasrc-body">
                  <div className="datasrc-name">WHO GLASS</div>
                  <div className="datasrc-desc">Global AMR surveillance providing population-level resistance statistics</div>
                </div>{' '}
                <i className="bi bi-arrow-up-right-circle-fill datasrc-arrow"></i>
              </a>

            </div>
          </div>

          {/* Quick Links */}
          <div className="info-card mb-4">
            <h6 className="card-section-title"><i className="bi bi-lightning-charge text-accent me-2"></i>Quick Links</h6>
            <div className="d-grid gap-2">{' '}
              <Link to="/forecast" className="btn btn-model"><i className="bi bi-graph-up-arrow me-2"></i>AMR Forecasting</Link>{' '}
              <Link to="/predict" className="btn btn-model btn-model-green"><i className="bi bi-dna me-2"></i>Resistance Prediction</Link>{' '}
              <Link to="/timeline" className="btn btn-model btn-model-red"><i className="bi bi-activity me-2"></i>Mutation Timeline</Link>{' '}
              <Link to="/datasets" className="btn btn-model"><i className="bi bi-database me-2"></i>Dataset Details</Link>{' '}
              <Link to="/train" className="btn btn-model"><i className="bi bi-cpu me-2"></i>Train Models</Link>
            </div>
          </div>

          {/* Citation / References */}
          <div className="info-card">
            <h6 className="card-section-title"><i className="bi bi-journal-text text-accent me-2"></i>Key References</h6>
            <div className="method-steps">
              <div className="method-step">{' '}
                <span className="step-num about-ref-num">1</span>{' '}
                <div className="small text-muted">{' '}
                  Olson RD et al. (2023). Introducing the Bacterial and Viral Bioinformatics Resource Center (BV-BRC).{' '}
                  <em>Nucleic Acids Research</em>, 51(D1), D678–D689.{' '}
                  <a href="https://academic.oup.com/nar/article/51/D1/D678/6840395" target="_blank" rel="noopener" className="src-link">[Full text]</a>
                </div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num about-ref-num">2</span>{' '}
                <div className="small text-muted">{' '}
                  Ke G et al. (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree.{' '}
                  <em>Advances in Neural Information Processing Systems (NeurIPS)</em>, 30.{' '}
                  <a href="https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html" target="_blank" rel="noopener" className="src-link">[NeurIPS 2017]</a>
                </div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num about-ref-num">3</span>{' '}
                <div className="small text-muted">{' '}
                  Drouin A et al. (2016). Predictive computational phenotyping and biomarker discovery using reference-free genome comparisons.{' '}
                  <em>BMC Genomics</em>, 17, 754.{' '}
                  <a href="https://bmcgenomics.biomedcentral.com/articles/10.1186/s12864-016-2777-6" target="_blank" rel="noopener" className="src-link">[Full text]</a>
                </div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num about-ref-num">4</span>{' '}
                <div className="small text-muted">{' '}
                  Murray CJ et al. (2022). Global burden of bacterial antimicrobial resistance in 2019: a systematic analysis.{' '}
                  <em>The Lancet</em>, 399(10325), 629–655.{' '}
                  <a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext" target="_blank" rel="noopener" className="src-link">[Full text]</a>
                </div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num about-ref-num">5</span>{' '}
                <div className="small text-muted">{' '}
                  WHO (2022). Global Antimicrobial Resistance and Use Surveillance System (GLASS) Report 2022.
                  World Health Organization, Geneva.{' '}
                  <a href="https://www.who.int/publications/i/item/9789240062702" target="_blank" rel="noopener" className="src-link">[WHO Publication]</a>
                </div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num about-ref-num">6</span>{' '}
                <div className="small text-muted">{' '}
                  O'Neill J (2016). Tackling Drug-Resistant Infections Globally: Final Report and Recommendations.{' '}
                  <em>Review on Antimicrobial Resistance</em>.{' '}
                  <a href="https://amr-review.org/sites/default/files/160518_Final%20paper_with%20cover.pdf" target="_blank" rel="noopener" className="src-link">[Full report PDF]</a>
                </div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num about-ref-num">7</span>{' '}
                <div className="small text-muted">{' '}
                  CDC (2019). Antibiotic Resistance Threats in the United States, 2019.
                  Centers for Disease Control and Prevention, Atlanta, GA.{' '}
                  <a href="https://www.cdc.gov/antimicrobial-resistance/data-research/threats/index.html" target="_blank" rel="noopener" className="src-link">[CDC Report]</a>
                </div>
              </div>
            </div>
          </div>

        </div>{/* /col-lg-4 */}
      </div>{/* /row */}
    </div>
    </>
  );
}
