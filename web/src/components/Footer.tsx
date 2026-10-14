import { Link } from 'react-router';
import { useMetrics } from '../lib/health';

export default function Footer() {
  const m = useMetrics();
  return (
    <footer className="footer mt-auto">
      <div className="container-xl">
        <div className="row g-4">
          {/* Brand */}
          <div className="col-lg-4 col-md-6">
            <div className="d-flex align-items-center gap-2 mb-2">
              <div className="brand-icon brand-icon-sm"><i className="bi bi-virus2"></i></div>
              <span className="fw-700 text-white fs-14">AMR<span className="text-accent">Predict</span></span>
            </div>
            <p className="meta-text mb-2">
              Forecasting antimicrobial resistance with machine learning using LightGBM gradient boosting and k-mer genomic analysis. Includes a biological simulation tool for mutation timeline visualisation.
            </p>
            <div className="caption-text">
              <i className="bi bi-mortarboard me-1 text-primary-tok"></i>
              BioInformatics &amp; ML Final Year Project · 2026–2027
            </div>
          </div>
          {/* Links */}
          <div className="col-lg-2 col-md-3 col-6">
            <div className="sec-label mb-2">Navigate</div>
            <ul className="list-unstyled mb-0 fs-12h">
              <li className="mb-1"><Link to="/" className="footer-link"><i className="bi bi-grid-1x2 me-1"></i>Dashboard</Link></li>
              <li className="footer-nav-divider">ML Models</li>
              <li className="mb-1"><Link to="/forecast" className="footer-link"><i className="bi bi-graph-up-arrow me-1"></i>AMR Forecasting</Link></li>
              <li className="mb-1"><Link to="/predict" className="footer-link"><i className="bi bi-dna me-1"></i>Resistance Prediction</Link></li>
              <li className="footer-nav-divider">Tools</li>
              <li className="mb-1"><Link to="/timeline" className="footer-link"><i className="bi bi-activity me-1"></i>Bio-Simulation</Link></li>
              <li className="footer-nav-divider">Insights</li>
              <li className="mb-1"><Link to="/models" className="footer-link"><i className="bi bi-clipboard-data me-1"></i>Model Report</Link></li>
              <li className="mb-1"><Link to="/compare" className="footer-link"><i className="bi bi-layout-split me-1"></i>Model Comparison</Link></li>
              <li className="mb-1"><Link to="/datasets" className="footer-link"><i className="bi bi-database me-1"></i>Datasets</Link></li>
              <li className="mb-1"><Link to="/genes" className="footer-link"><i className="bi bi-bacteria me-1"></i>Resistance Genes</Link></li>
              <li className="mb-1 mt-2"><Link to="/about" className="footer-link"><i className="bi bi-info-circle me-1"></i>About</Link></li>
            </ul>
          </div>
          {/* Stats */}
          <div className="col-lg-3 col-md-12">
            <div className="sec-label mb-2">System Stats</div>
            <div className="row g-2">
              <div className="col-6">
                <div className="footer-stat-box">
                  <div className="footer-stat-val">{m.lgbm.auc}</div>
                  <div className="footer-stat-lbl">Forecaster AUC (unseen genomes)</div>
                </div>
              </div>
              <div className="col-6">
                <div className="footer-stat-box">
                  <div className="footer-stat-val">{m.lgbm.train_rows_short}</div>
                  <div className="footer-stat-lbl">Training rows</div>
                </div>
              </div>
              <div className="col-6">
                <div className="footer-stat-box">
                  <div className="footer-stat-val">{m.lgbm.antibiotics}</div>
                  <div className="footer-stat-lbl">Antibiotics</div>
                </div>
              </div>
              <div className="col-6">
                <div className="footer-stat-box">
                  <div className="footer-stat-val">2</div>
                  <div className="footer-stat-lbl">ML Models</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* Bottom bar */}
        <div className="footer-bottom mt-4 pt-3">
          <div className="footer-copy"></div>
          <div className="footer-copy">
            Data source: <a href="https://www.bv-brc.org" target="_blank" rel="noopener" className="footer-link">BVBRC / PATRIC</a>
            &nbsp;&middot;&nbsp;
            <Link to="/about" className="footer-link">Documentation</Link>
            &nbsp;&middot;&nbsp;
            <Link to="/train" className="footer-link"><i className="bi bi-play-circle me-1"></i>Train Models</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
