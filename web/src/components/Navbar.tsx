import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router';
import { Collapse } from 'bootstrap';
import { setTheme, useDarkTheme } from '../lib/theme';

export default function Navbar() {
  const { pathname } = useLocation();
  const dark = useDarkTheme();
  const nav = useRef<HTMLElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const update = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', update, { passive: true });
    update();
    return () => window.removeEventListener('scroll', update);
  }, []);

  // A link opened from the phone menu closes the menu
  useEffect(() => {
    if (menu.current?.classList.contains('show')) Collapse.getOrCreateInstance(menu.current).hide();
  }, [pathname]);

  const on = (...paths: string[]) => (paths.some(p => (p === '/' ? pathname === '/' : pathname.startsWith(p))) ? ' active' : '');

  return (
    <nav className="navbar navbar-expand-lg navbar-dark fixed-top" id="mainNav" ref={nav}
         style={scrolled ? { boxShadow: '0 4px 24px rgba(0,0,0,0.15)' } : undefined}>
      <div className="container-xl">
        <Link className="navbar-brand d-flex align-items-center gap-2" to="/">
          <div className="brand-icon"><i className="bi bi-virus2"></i></div>
          <div>
            <span className="brand-name">AMR<span className="text-accent">Predict</span></span>
            <span className="brand-sub d-none d-xxl-inline">Antibiotic Resistance Forecasting</span>
          </div>
        </Link>
        <button className="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu"
                aria-label="Menu">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navMenu" ref={menu}>
          <ul className="navbar-nav ms-auto align-items-lg-center gap-1">
            <li className="nav-item">
              <Link className={'nav-link' + on('/')} to="/"><i className="bi bi-grid-1x2 me-1"></i>Dashboard</Link>
            </li>
            <li className="nav-item dropdown">
              <a className={'nav-link dropdown-toggle' + on('/forecast', '/predict')}
                 href="#" role="button" data-bs-toggle="dropdown" onClick={e => e.preventDefault()}>
                <i className="bi bi-cpu me-1"></i>ML Models
              </a>
              <ul className="dropdown-menu dropdown-menu-dark">
                <li><h6 className="dropdown-header dropdown-section-label">TRAINED ML MODELS</h6></li>
                <li><Link className="dropdown-item" to="/forecast"><i className="bi bi-graph-up-arrow me-2 text-accent"></i>AMR Forecasting <span className="badge bg-success ms-1 badge-xs">LightGBM</span></Link></li>
                <li><Link className="dropdown-item" to="/predict"><i className="bi bi-dna me-2 text-emerald2"></i>Resistance Prediction <span className="badge bg-primary ms-1 badge-xs">K-mer RF</span></Link></li>
              </ul>
            </li>
            <li className="nav-item">
              <Link className={'nav-link' + on('/timeline')} to="/timeline"><i className="bi bi-activity me-1"></i>Bio-Simulator</Link>
            </li>
            {/* Pages that explain results; nothing here predicts */}
            <li className="nav-item dropdown">
              <a className={'nav-link dropdown-toggle' + on('/models', '/compare', '/genes', '/datasets')}
                 href="#" role="button" data-bs-toggle="dropdown" onClick={e => e.preventDefault()}>
                <i className="bi bi-lightbulb me-1"></i>Insights
              </a>
              <ul className="dropdown-menu dropdown-menu-dark">
                <li><h6 className="dropdown-header dropdown-section-label">MODEL RESULTS</h6></li>
                <li><Link className="dropdown-item" to="/models"><i className="bi bi-clipboard-data me-2 text-accent"></i>Model Report <span className="badge bg-secondary ms-1 badge-xs">All models</span></Link></li>
                <li><Link className="dropdown-item" to="/compare"><i className="bi bi-layout-split me-2 text-accent"></i>Deployed vs Experimental</Link></li>
                <li><hr className="dropdown-divider" /></li>
                <li><h6 className="dropdown-header dropdown-section-label">DATA</h6></li>
                <li><Link className="dropdown-item" to="/datasets"><i className="bi bi-database me-2 text-accent"></i>Datasets <span className="badge bg-secondary ms-1 badge-xs">BV-BRC</span></Link></li>
                <li><Link className="dropdown-item" to="/genes"><i className="bi bi-bacteria me-2 text-emerald2"></i>Resistance Genes <span className="badge bg-secondary ms-1 badge-xs">AMRFinderPlus</span></Link></li>
              </ul>
            </li>
            <li className="nav-item">
              <Link className={'nav-link' + on('/library')} to="/library"><i className="bi bi-box-seam me-1"></i>Library</Link>
            </li>
            <li className="nav-item">
              <Link className={'nav-link' + on('/about')} to="/about"><i className="bi bi-info-circle me-1"></i>About</Link>
            </li>
            <li className="nav-item ms-lg-2">
              <Link className={'nav-link nav-train' + on('/train')} to="/train"><i className="bi bi-play-circle me-1"></i>Train</Link>
            </li>
            <li className="nav-item ms-lg-1 d-flex align-items-center">
              <button className="theme-toggle" id="themeToggle" aria-label="Toggle theme"
                      title={dark ? 'Switch to light mode' : 'Switch to dark mode'} onClick={() => setTheme(!dark)}>
                <i className={dark ? 'bi bi-sun' : 'bi bi-moon'}></i>
              </button>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}
