import { Link } from 'react-router';
import ModelStatus from '../components/ModelStatus';
import { useHealth } from '../lib/health';
import { useTitle } from '../lib/pageEffects';

export default function Home() {
  useTitle('Dashboard');
  const { health, metrics: m } = useHealth();
  return (
    <>
    {/* ══ HERO ══════════════════════════════════════════════════ */}
    <div className="hero-section">
      <div className="container-xl position-relative">
        <div className="row align-items-center g-4 g-lg-5">
          <div className="col-lg-7">{' '}
            <div className="hero-eyebrow">{' '}
              <span className="dot"></span>Machine Learning · Final Year Project
            </div>
            <h1 className="hero-title">{' '}
              Forecasting<br />{' '}
              <span className="text-gradient-blue">Antibiotic Resistance</span><br />{' '}
              with Machine Learning
            </h1>
            <p className="hero-desc">{' '}
              Two trained ML models, both LightGBM gradient boosting (one on lab metadata, one on the k-mers of a complete genome), predict
              antimicrobial resistance in bacterial pathogens from {m.lgbm.train_rows_short} labelled records.
              A separate biological simulation tool models resistance evolution over time.
            </p>
            <div className="hero-actions">{' '}
              <Link to="/forecast" className="btn btn-primary-custom btn-lg px-4">{' '}
                <i className="bi bi-graph-up-arrow me-2"></i>Start Predicting
              </Link>{' '}
              <Link to="/train" className="btn btn-outline-custom btn-lg px-4">{' '}
                <i className="bi bi-cpu me-2"></i>Train Models
              </Link>{' '}
              <Link to="/about" className="btn btn-outline-custom btn-lg px-4">{' '}
                <i className="bi bi-info-circle me-2"></i>About
              </Link>
            </div>
            {/* Model badges row */}
            <div className="d-flex gap-2 flex-wrap mt-4">{' '}
              <span className="status-badge trained"><i className="bi bi-check-circle-fill"></i> LightGBM  AUC {m.lgbm.auc}</span>{' '}
              <span className="status-badge trained"><i className="bi bi-check-circle-fill"></i> Genome k-mers  AUC {m.kmer.auc}</span>{' '}
              <span className="status-badge simulated"><i className="bi bi-diagram-3"></i> Timeline: Bio-Sim</span>
            </div>
          </div>
          <div className="col-lg-5 d-none d-lg-block">
            <div className="hero-panel">
              <div className="hero-panel-header">{' '}
                <span className="hero-panel-dot green"></span>{' '}
                <span className="hero-panel-dot yellow"></span>{' '}
                <span className="hero-panel-dot red"></span>{' '}
                <span className="hero-panel-title">AMR Analysis Engine · v2.0</span>
              </div>
              <div className="hero-panel-body">
                <div className="hpanel-row">
                  <div className="hpanel-icon lgbm"><i className="bi bi-graph-up-arrow"></i></div>
                  <div className="hpanel-info">
                    <div className="hpanel-name">LightGBM Forecasting</div>
                    <div className="hpanel-meta">{m.lgbm.train_rows} training rows &middot; 14 features</div>
                  </div>
                  <div className="hpanel-badge trained">AUC {m.lgbm.auc}</div>
                </div>
                <div className="hpanel-row">
                  <div className="hpanel-icon kmer"><i className="bi bi-dna"></i></div>
                  <div className="hpanel-info">
                    <div className="hpanel-name">K-mer LightGBM (complete genomes)</div>
                    <div className="hpanel-meta">{m.kmer.train_rows} training rows &middot; 256 k-mer features</div>
                  </div>
                  <div className="hpanel-badge trained">AUC {m.kmer.auc}</div>
                </div>
                <div className="hpanel-row">
                  <div className="hpanel-icon timeline"><i className="bi bi-activity"></i></div>
                  <div className="hpanel-info">
                    <div className="hpanel-name">Mutation Timeline</div>
                    <div className="hpanel-meta">Logistic growth simulation</div>
                  </div>
                  <div className="hpanel-badge sim">Simulation</div>
                </div>
                <div className="hpanel-divider"></div>
                <div className="hpanel-stats">
                  <div className="hpanel-stat">
                    <div className="hpanel-stat-val">{m.lgbm.train_rows_short}</div>
                    <div className="hpanel-stat-label">Records</div>
                  </div>
                  <div className="hpanel-stat">
                    <div className="hpanel-stat-val">{m.lgbm.antibiotics}</div>
                    <div className="hpanel-stat-label">Antibiotics</div>
                  </div>
                  <div className="hpanel-stat">
                    <div className="hpanel-stat-val">{m.kmer.genomes_total}</div>
                    <div className="hpanel-stat-label">Genomes</div>
                  </div>
                  <div className="hpanel-stat">
                    <div className="hpanel-stat-val">2</div>
                    <div className="hpanel-stat-label">ML Models</div>
                  </div>
                </div>
                <div className="hpanel-divider"></div>
                <div className="hpanel-bars-label"><i className="bi bi-bar-chart me-1"></i>Resistance rate by antibiotic class</div>
                <div className="hpanel-bars">
                  <div className="hpanel-bar-row">{' '}
                    <span className="hpanel-bar-name">Penicillins</span>{' '}
                    <div className="hpanel-bar-track"><div className="hpanel-bar-fill danger" data-pct="72"></div></div>{' '}
                    <span className="hpanel-bar-pct">72%</span>
                  </div>
                  <div className="hpanel-bar-row">{' '}
                    <span className="hpanel-bar-name">Fluoroquinolones</span>{' '}
                    <div className="hpanel-bar-track"><div className="hpanel-bar-fill warning" data-pct="61"></div></div>{' '}
                    <span className="hpanel-bar-pct">61%</span>
                  </div>
                  <div className="hpanel-bar-row">{' '}
                    <span className="hpanel-bar-name">Aminoglycosides</span>{' '}
                    <div className="hpanel-bar-track"><div className="hpanel-bar-fill amber" data-pct="45"></div></div>{' '}
                    <span className="hpanel-bar-pct">45%</span>
                  </div>
                  <div className="hpanel-bar-row">{' '}
                    <span className="hpanel-bar-name">Carbapenems</span>{' '}
                    <div className="hpanel-bar-track"><div className="hpanel-bar-fill success" data-pct="28"></div></div>{' '}
                    <span className="hpanel-bar-pct">28%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    {/* ══ GLOBAL AMR STATISTICS STRIP ══════════════════════════ */}
    <div className="stats-strip">
      <div className="container-xl">
        <div className="d-flex align-items-center justify-content-between flex-wrap gap-3 stats-strip-row">
          <div className="stat-item">
            <div className="stat-number blue">1.27M</div>
            <div className="stat-label">Annual deaths directly<br />attributable to AMR (2019){' '}
              <br /><a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext" target="_blank" rel="noopener" className="src-link">Murray et al., The Lancet 2022</a>
            </div>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <div className="stat-number rose">4.95M</div>
            <div className="stat-label">Deaths associated<br />with AMR per year (2019){' '}
              <br /><a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext" target="_blank" rel="noopener" className="src-link">Murray et al., The Lancet 2022</a>
            </div>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <div className="stat-number amber">10M</div>
            <div className="stat-label">Projected annual deaths<br />from AMR by 2050{' '}
              <br /><a href="https://amr-review.org/sites/default/files/160518_Final%20paper_with%20cover.pdf" target="_blank" rel="noopener" className="src-link">O'Neill Review, 2016</a>
            </div>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <div className="stat-number indigo">$100T</div>
            <div className="stat-label">Cumulative global GDP<br />loss from AMR by 2050{' '}
              <br /><a href="https://amr-review.org/sites/default/files/160518_Final%20paper_with%20cover.pdf" target="_blank" rel="noopener" className="src-link">O'Neill Review, 2016</a>
            </div>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <div className="stat-number emerald">{m.lgbm.train_rows_short}</div>
            <div className="stat-label">Genomic AMR records<br />used for model training{' '}
              <br /><a href="https://www.bv-brc.org/" target="_blank" rel="noopener" className="src-link">BVBRC / PATRIC Database</a>
            </div>
          </div>
        </div>
        <div className="mt-3 pt-2 border-top-subtle fs-105 text-3">{' '}
          <strong className="text-2">Sources:</strong>&nbsp;{' '}
          <a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext" target="_blank" rel="noopener" className="src-link">Murray CJ et al. "Global burden of bacterial antimicrobial resistance in 2019." <em>The Lancet</em> 399, 629–655 (2022)</a>{' '}
          &nbsp;·&nbsp;{' '}
          <a href="https://amr-review.org/sites/default/files/160518_Final%20paper_with%20cover.pdf" target="_blank" rel="noopener" className="src-link">O'Neill J. "Tackling Drug-Resistant Infections Globally." <em>Review on Antimicrobial Resistance</em> (2016)</a>{' '}
          &nbsp;·&nbsp;{' '}
          <a href="https://www.bv-brc.org/" target="_blank" rel="noopener" className="src-link">Olson et al. "Introducing the Bacterial and Viral Bioinformatics Resource Center (BV-BRC)." <em>Nucleic Acids Research</em> 51, D678–D689 (2023)</a>
        </div>
      </div>
    </div>

    <div className="container-xl py-5">

      {/* ══ AMR CRISIS SECTION ══════════════════════════════════ */}
      <div className="row mb-5">
        <div className="col-12">
          <div className="sec-eyebrow"><i className="bi bi-exclamation-triangle me-2"></i>The Challenge</div>
          <h2 className="sec-title">Antimicrobial Resistance: A Global Health Emergency</h2>
          <p className="sec-sub mb-4">{' '}
            AMR occurs when bacteria, viruses, fungi, and parasites evolve mechanisms to defeat the drugs
            designed to kill them. Machine learning can predict resistance <em>before</em> it becomes
            clinically apparent.
          </p>
        </div>
        <div className="col-md-3 col-6 mb-3">
          <div className="crisis-card blue h-100">
            <div className="crisis-icon"><i className="bi bi-bacteria"></i></div>
            <div className="crisis-val">1.27M</div>
            <div className="crisis-desc">Deaths directly attributable to bacterial AMR in 2019  surpassing HIV/AIDS and malaria</div>
            <div className="mt-2"><a href="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext" target="_blank" rel="noopener" className="src-link">Murray et al., The Lancet (2022)</a></div>
          </div>
        </div>
        <div className="col-md-3 col-6 mb-3">
          <div className="crisis-card rose h-100">
            <div className="crisis-icon"><i className="bi bi-capsule-pill"></i></div>
            <div className="crisis-val">~80%</div>
            <div className="crisis-desc">Of E. coli isolates show fluoroquinolone resistance in several high-burden countries, per WHO surveillance data</div>
            <div className="mt-2"><a href="https://www.who.int/publications/i/item/9789240062702" target="_blank" rel="noopener" className="src-link">WHO GLASS Report (2022)</a></div>
          </div>
        </div>
        <div className="col-md-3 col-6 mb-3">
          <div className="crisis-card amber h-100">
            <div className="crisis-icon"><i className="bi bi-dna"></i></div>
            <div className="crisis-val">2.8M+</div>
            <div className="crisis-desc">Antibiotic-resistant infections occur in the United States every year, causing at least 35,000 deaths</div>
            <div className="mt-2"><a href="https://www.cdc.gov/antimicrobial-resistance/data-research/threats/index.html" target="_blank" rel="noopener" className="src-link">CDC AR Threats Report (2019)</a></div>
          </div>
        </div>
        <div className="col-md-3 col-6 mb-3">
          <div className="crisis-card indigo h-100">
            <div className="crisis-icon"><i className="bi bi-activity"></i></div>
            <div className="crisis-val">AUC {m.lgbm.auc}</div>
            <div className="crisis-desc">The resistance forecaster, tested on genomes it never saw in training ({m.lgbm.split || 'genome-grouped split'})</div>
            <div className="mt-2"><a href="https://www.bv-brc.org/" target="_blank" rel="noopener" className="src-link">Training data: BVBRC / PATRIC</a></div>
          </div>
        </div>
      </div>

      {/* ══ ML MODEL STATUS CARDS ════════════════════════════════ */}
      <div className="sec-eyebrow"><i className="bi bi-cpu me-2"></i>Machine Learning Models</div>
      <h2 className="sec-title mb-1">Trained ML Prediction Models</h2>
      <p className="sec-sub mb-4">Two ML models trained on real BVBRC / PATRIC genomic data   each producing a data-driven binary classification: <strong>Resistant</strong> or <strong>Susceptible</strong>.</p>

      <div className="row g-4 mb-5">
        {/* LightGBM */}
        <div className="col-lg-6">
          <div className="model-card h-100">
            <div className="d-flex align-items-start gap-3 mb-3">
              <div className="model-icon lgbm-icon"><i className="bi bi-graph-up-arrow"></i></div>
              <div className="flex-grow-1">
                <div className="fw-700 text-white fs-15">AMR Resistance Forecasting</div>
                <div className="model-subtitle">LightGBM Gradient Boosting · Trained on real data</div>
              </div>
              <ModelStatus status={health?.models?.lgbm_forecasting} loading={health === undefined} />
            </div>
            <p className="body-text mb-14">{' '}
              Predicts <strong className="text-1">Resistant vs Susceptible</strong> from genome metadata:
              MIC values, organism taxonomy, drug class, and target encoding of per-antibiotic resistance rates.
              Trained on <strong className="text-1">{m.lgbm.train_rows} labeled samples</strong> from the BVBRC database.
            </p>
            <div className="row g-2 mb-3 text-center">
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value fs-16">{m.lgbm.auc}</div><div className="stat-mini-label">AUC-ROC</div></div></div>
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value fs-16">14</div><div className="stat-mini-label">Features</div></div></div>
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value fs-16">500</div><div className="stat-mini-label">Estimators</div></div></div>
            </div>
            <div className="model-features mb-3">{' '}
              <span className="feature-tag">MIC Values</span>{' '}
              <span className="feature-tag">Taxonomy</span>{' '}
              <span className="feature-tag">Drug Class</span>{' '}
              <span className="feature-tag">Target Encoding</span>
            </div>{' '}
            <Link to="/forecast" className="btn btn-model w-100"><i className="bi bi-arrow-right-circle me-2"></i>Run Forecasting</Link>
          </div>
        </div>

        {/* K-mer */}
        <div className="col-lg-6">
          <div className="model-card h-100">
            <div className="d-flex align-items-start gap-3 mb-3">
              <div className="model-icon kmer-icon"><i className="bi bi-dna"></i></div>
              <div className="flex-grow-1">
                <div className="fw-700 text-white fs-15">Genomic Resistance Prediction</div>
                <div className="model-subtitle">K-mer Spectrum of the complete genome + LightGBM · Trained on real data</div>
              </div>
              <ModelStatus status={health?.models?.kmer_resistance} loading={health === undefined} />
            </div>
            <p className="body-text mb-14">{' '}
              Extracts <strong className="text-1">4-mer frequency spectra</strong> (256 features) from raw FASTA genome sequences.
              No reference genome needed   works alignment-free on any bacterial genome.
              Trained on <strong className="text-1">6,002 genome–antibiotic pairs</strong> across 62 antibiotics.
            </p>
            <div className="row g-2 mb-3 text-center">
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value fs-16">{m.kmer.auc}</div><div className="stat-mini-label">AUC-ROC</div></div></div>
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value fs-16">256</div><div className="stat-mini-label">K-mer Feats</div></div></div>
              <div className="col-4"><div className="stat-mini"><div className="stat-mini-value fs-16">62</div><div className="stat-mini-label">Antibiotics</div></div></div>
            </div>
            <div className="model-features mb-3">{' '}
              <span className="feature-tag">FASTA Input</span>{' '}
              <span className="feature-tag">4-mer Spectrum</span>{' '}
              <span className="feature-tag">GC Content</span>{' '}
              <span className="feature-tag">Balanced Weights</span>
            </div>{' '}
            <Link to="/predict" className="btn btn-model w-100 btn-model-green"><i className="bi bi-arrow-right-circle me-2"></i>Run Prediction</Link>
          </div>
        </div>
      </div>

      {/* ══ BIOLOGICAL SIMULATION TOOL ════════════════════════════ */}
      <div className="sec-eyebrow"><i className="bi bi-activity me-2"></i>Analytical Tool</div>
      <h2 className="sec-title mb-1">Biological Simulation</h2>
      <p className="sec-sub mb-2">Not a machine learning model a mathematical simulation tool based on published biological kinetics.</p>

      <div className="row g-4 mb-5">
        <div className="col-lg-8">
          <div className="glass-card h-100 card-border-warning">
            <div className="d-flex align-items-start gap-3 mb-3">
              <div className="model-icon timeline-icon"><i className="bi bi-activity"></i></div>
              <div className="flex-grow-1">
                <div className="fw-700 text-white fs-15">Mutation Timeline Simulator</div>
                <div className="model-subtitle">Logistic Growth Equation · Hand-set Constants</div>
              </div>{' '}
              <span className="status-badge simulated"><i className="bi bi-diagram-3"></i>Simulation</span>
            </div>
            <div className="alert-warning-tok">{' '}
              <i className="bi bi-info-circle-fill me-2"></i>{' '}
              <strong>This is not an ML model.</strong> Predictions are generated by a logistic growth equation parameterised with hand-set, literature-based antibiotic-specific constants, not learned from data.
            </div>
            <p className="body-text mb-14">{' '}
              Simulates <strong className="text-1">week-by-week resistance evolution</strong> under antibiotic pressure
              using the logistic growth equation:{' '}
              <code className="code-pill d-inline-block mt-1">{' '}
                R(t) = R₀ + (R_peak − R₀) / (1 + e<sup>−k(t−t₀)</sup>)
              </code>
            </p>
            <p className="body-text mb-14">{' '}
              Each antibiotic has hand-set parameters (growth rate <em>k</em>, peak resistance, midpoint); only the curve's shape has been checked against published data. An optional FASTA file adjusts the curve via genome GC content; a higher GC deviation suggests higher baseline mutation pressure.
            </p>
            <div className="model-features mb-3">{' '}
              <span className="feature-tag">Logistic Growth</span>{' '}
              <span className="feature-tag">GC Modifier</span>{' '}
              <span className="feature-tag">Hotspot Detection</span>{' '}
              <span className="feature-tag">Gene Activation</span>{' '}
              <span className="feature-tag">13 Antibiotics</span>
            </div>{' '}
            <Link to="/timeline" className="btn btn-model w-100 btn-model-red"><i className="bi bi-arrow-right-circle me-2"></i>Open Simulator</Link>
          </div>
        </div>
        <div className="col-lg-4">
          <div className="glass-card h-100">
            <div className="sec-label mb-3">How it differs from ML models</div>
            <ul className="list-unstyled mb-0 fs-12h text-2">
              <li className="mb-3 d-flex gap-2">{' '}
                <i className="bi bi-x-circle-fill mt-1 flex-shrink-0 text-danger-tok fs-13"></i>{' '}
                <span>Does <strong className="text-1">not</strong> learn from labeled data and has no training phase</span>
              </li>
              <li className="mb-3 d-flex gap-2">{' '}
                <i className="bi bi-x-circle-fill mt-1 flex-shrink-0 text-danger-tok fs-13"></i>{' '}
                <span>Has <strong className="text-1">no AUC or accuracy score</strong>; outputs are simulated, not predicted</span>
              </li>
              <li className="mb-3 d-flex gap-2">{' '}
                <i className="bi bi-check-circle-fill mt-1 flex-shrink-0 text-success-tok fs-13"></i>{' '}
                <span>Parameters grounded in <strong className="text-1">published microbiology</strong> (resistance gene kinetics)</span>
              </li>
              <li className="mb-3 d-flex gap-2">{' '}
                <i className="bi bi-check-circle-fill mt-1 flex-shrink-0 text-success-tok fs-13"></i>{' '}
                <span>Useful for <strong className="text-1">visualising resistance trajectories</strong> and treatment planning</span>
              </li>
              <li className="mb-0 d-flex gap-2">{' '}
                <i className="bi bi-check-circle-fill mt-1 flex-shrink-0 text-success-tok fs-13"></i>{' '}
                <span>Complements ML predictions with <strong className="text-1">temporal evolution context</strong></span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Formulation (unavailable) */}
      <div className="row g-4 mb-5">
        <div className="col-lg-4">
          <div className="model-card model-card-disabled">
            <div className="d-flex align-items-start gap-3 mb-3">
              <div className="model-icon formulation-icon"><i className="bi bi-capsule"></i></div>
              <div className="flex-grow-1">
                <div className="fw-700 text-white fs-15">Formulation Forecasting</div>
                <div className="model-subtitle">Dataset Not Available</div>
              </div>{' '}
              <span className="status-badge unavailable"><i className="bi bi-database-x"></i>No Dataset</span>
            </div>
            <p className="body-text text-3 mb-12">{' '}
              Would predict optimal antibiotic formulations and dosing strategies to counteract
              resistance patterns. Excluded from scope because the pharmaceutical formulation dataset was not available.
            </p>
            <div className="alert-warning-custom fs-12"><i className="bi bi-info-circle me-2"></i>Excluded from project scope. Dataset required before training can begin.</div>
          </div>
        </div>

        {/* System Architecture Panel */}
        <div className="col-lg-8">
          <div className="glass-card h-100">
            <h5 className="fw-700 text-white mb-1"><i className="bi bi-diagram-3 me-2 text-primary-tok"></i>System Architecture</h5>
            <p className="fs-13 text-3 mb-20">Full-stack ML deployment: Flask frontend → Django REST API → Trained ML models</p>

            <div className="pipeline-diagram">
              <div className="pipeline-step">
                <div className="pipeline-icon"><i className="bi bi-person-fill"></i></div>
                <div className="pipeline-label">User Input<br /><small>FASTA / Form</small></div>
              </div>
              <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
              <div className="pipeline-step">
                <div className="pipeline-icon"><i className="bi bi-layout-text-window"></i></div>
                <div className="pipeline-label">Flask UI<br /><small>Port 5001</small></div>
              </div>
              <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
              <div className="pipeline-step">
                <div className="pipeline-icon"><i className="bi bi-server"></i></div>
                <div className="pipeline-label">Django API<br /><small>Port 8000</small></div>
              </div>
              <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
              <div className="pipeline-step">
                <div className="pipeline-icon"><i className="bi bi-cpu"></i></div>
                <div className="pipeline-label">ML Models<br /><small>LightGBM / RF</small></div>
              </div>
              <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
              <div className="pipeline-step active-step">
                <div className="pipeline-icon"><i className="bi bi-clipboard2-pulse"></i></div>
                <div className="pipeline-label">Results<br /><small>Prediction + Charts</small></div>
              </div>
            </div>

            <div className="row g-3 mt-2">
              <div className="col-sm-3 col-6"><div className="stat-mini"><div className="stat-mini-value">{m.lgbm.train_rows_short}</div><div className="stat-mini-label">Training samples</div></div></div>
              <div className="col-sm-3 col-6"><div className="stat-mini"><div className="stat-mini-value">{m.kmer.genomes_total}</div><div className="stat-mini-label">FASTA genomes</div></div></div>
              <div className="col-sm-3 col-6"><div className="stat-mini"><div className="stat-mini-value">{m.lgbm.antibiotics}</div><div className="stat-mini-label">Antibiotics</div></div></div>
              <div className="col-sm-3 col-6"><div className="stat-mini"><div className="stat-mini-value">{m.lgbm.auc}</div><div className="stat-mini-label">Forecaster AUC</div></div></div>
            </div>
          </div>
        </div>
      </div>

      {/* ══ HOW IT WORKS ═══════════════════════════════════════ */}
      <div className="sec-eyebrow"><i className="bi bi-question-circle me-2"></i>Methodology</div>
      <h2 className="sec-title mb-1">How the System Works</h2>
      <p className="sec-sub mb-4">Two trained ML models for resistance prediction, plus one mathematical simulation tool for visualising resistance evolution over time.</p>

      <div className="row g-3 mb-5">
        <div className="col-md-6 col-lg-4">
          <div className="how-step h-100">
            <div className="how-num">01</div>
            <div>
              <div className="how-title">Data Collection: BVBRC/PATRIC</div>
              <div className="how-desc">AMR phenotype records (Resistant/Susceptible/Intermediate) linked to bacterial genome metadata including MIC values, laboratory methods, and FASTA genome sequences from the BVBRC database.</div>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-4">
          <div className="how-step h-100">
            <div className="how-num">02</div>
            <div>
              <div className="how-title">Feature Engineering: K-mer Spectra</div>
              <div className="how-desc">Bacterial genomes are converted to 4-mer frequency vectors (256 dimensions). Each genome produces a fixed-length fingerprint capturing codon composition, GC content, and repeat patterns. No reference genome is needed.</div>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-4">
          <div className="how-step h-100">
            <div className="how-num">03</div>
            <div>
              <div className="how-title">LightGBM: Tabular Metadata</div>
              <div className="how-desc">For records without FASTA files, a LightGBM gradient boosted tree model uses tabular features: MIC value, antibiotic identity, drug class, organism taxonomy, and cross-encoded resistance rates per antibiotic.</div>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-4">
          <div className="how-step h-100">
            <div className="how-num">04</div>
            <div>
              <div className="how-title">Class Imbalance Correction</div>
              <div className="how-desc">Training data is typically imbalanced (more Susceptible than Resistant isolates). Both models are LightGBM with <code className="code-pill">is_unbalance=True</code>, and each one's decision threshold is set on validation genomes to miss at most 10% of resistant isolates, without synthetic oversampling.</div>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-4">
          <div className="how-step h-100 how-step-warning">
            <div className="how-num step-warning">05</div>
            <div>
              <div className="how-title">Bio-Simulator: Logistic Growth <span className="badge-not-ml">Not ML</span></div>
              <div className="how-desc">Resistance spread follows logistic kinetics. The timeline simulator uses a mathematical equation, not trained on data, to show week-by-week resistance evolution per antibiotic. It complements the ML predictions with temporal context.</div>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-4">
          <div className="how-step h-100">
            <div className="how-num">06</div>
            <div>
              <div className="how-title">Validation: AUC-ROC &amp; F1</div>
              <div className="how-desc">Both models are tested on genomes they never saw in training: the forecaster scores AUC-ROC {m.lgbm.auc_ci} and the k-mer model {m.kmer.auc_ci}. The forecaster's threshold ({m.lgbm.threshold}) is chosen on validation genomes to keep missed resistance (very major error) at or below 10%, because calling a resistant isolate susceptible is the dangerous mistake.</div>
            </div>
          </div>
        </div>
      </div>

      {/* ══ QUICK START ════════════════════════════════════════ */}
      <div className="sec-eyebrow"><i className="bi bi-lightning-charge me-2"></i>Get Started</div>
      <h2 className="sec-title mb-4">Quick Start Guide</h2>
      <div className="glass-card">
        <div className="row g-4">
          <div className="col-md-4">
            <div className="quickstart-step">
              <div className="qs-number">01</div>
              <h6>Train Models (optional)</h6>
              <p>Models are pre-trained. To retrain on your dataset, go to <Link to="/train">Train Models</Link>{' '}
                 or run <code className="code-pill code-pill-success">python train_models.py --model all</code> in the backend folder.</p>
            </div>
          </div>
          <div className="col-md-4">
            <div className="quickstart-step">
              <div className="qs-number">02</div>
              <h6>AMR Forecasting</h6>
              <p>Go to <Link to="/forecast">AMR Forecasting</Link> and enter an antibiotic name, MIC value, and organism genus/species. The LightGBM model returns resistance probability instantly.</p>
            </div>
          </div>
          <div className="col-md-4">
            <div className="quickstart-step">
              <div className="qs-number">03</div>
              <h6>Genome-level Analysis</h6>
              <p>Upload a <code className="code-pill code-pill-primary">.fasta</code> file to <Link to="/predict">Resistance Prediction</Link> for k-mer analysis, or to <Link to="/timeline">Mutation Timeline</Link> for a week-by-week evolution forecast.</p>
            </div>
          </div>
        </div>
      </div>

    </div>
    </>
  );
}
