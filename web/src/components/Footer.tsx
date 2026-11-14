import { Link } from 'react-router';
import { useMetrics } from '../lib/health';
import { EXPLORE_VIEWS } from '../pages/explore/nav';
import BioIcon from './BioIcon';
import FooterScene from './FooterScene';

type FooterLink = { to: string; label: string; icon: string };

const COLUMNS: { title: string; links: FooterLink[] }[] = [
  { title: 'Predict', links: [
    { to: '/forecast', label: 'AMR Forecasting', icon: 'bi-graph-up-arrow' },
    { to: '/predict', label: 'Resistance Prediction', icon: 'bi-dna' },
    { to: '/timeline', label: 'Bio-Simulator', icon: 'bi-activity' },
  ] },
  { title: 'Resistance Explorer', links: EXPLORE_VIEWS.map(v => ({ to: `/explore/${v.key}`, label: v.label, icon: v.icon })) },
  { title: 'Insights & data', links: [
    { to: '/models', label: 'Model Report', icon: 'bi-clipboard-data' },
    { to: '/compare', label: 'Deployed vs Experimental', icon: 'bi-layout-split' },
    { to: '/datasets', label: 'Datasets', icon: 'bi-database' },
    { to: '/genes', label: 'Resistance Genes', icon: 'bi-bacteria' },
  ] },
  { title: 'Project', links: [
    { to: '/library', label: 'Python Library', icon: 'bi-box-seam' },
    { to: '/about', label: 'About & docs', icon: 'bi-info-circle' },
    { to: '/train', label: 'Train Models', icon: 'bi-play-circle' },
  ] },
];

const SOURCES = [
  { href: 'https://www.bv-brc.org', label: 'BV-BRC' },
  { href: 'https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/', label: 'NCBI AMRFinderPlus' },
  { href: 'https://pubchem.ncbi.nlm.nih.gov', label: 'PubChem' },
];

export default function Footer() {
  const m = useMetrics();
  const stats = [
    { value: m.lgbm.auc, label: 'Forecaster AUC' },
    { value: m.kmer.auc, label: 'Genome model AUC' },
    { value: m.lgbm.train_rows_short, label: 'Training rows' },
    { value: String(m.lgbm.antibiotics), label: 'Antibiotics' },
  ];
  return (
    <footer className="footer mt-auto">
      <FooterScene />
      <div className="container-xl">
        <div className="ft-grid">
          <div className="ft-brand">
            <Link to="/" className="d-inline-flex align-items-center gap-2 text-decoration-none mb-3">
              <div className="brand-icon brand-icon-sm"><BioIcon icon="bi-virus2" /></div>
              <span className="ft-name">AMR<span className="text-accent">Predict</span></span>
            </Link>
            <p className="ft-about">
              Predicts antimicrobial resistance from laboratory data and bacterial genomes, simulates how resistance
              grows under treatment, and maps laboratory resistance across the world.
            </p>
            <div className="ft-stats" aria-label="Model figures, measured on genomes the models never saw">
              {stats.map(s => (
                <div key={s.label} className="ft-stat"><span className="ft-stat-val">{s.value}</span><span className="ft-stat-lbl">{s.label}</span></div>))}
            </div>
            <div className="ft-note">AUC on genomes the models never saw in training.</div>
          </div>

          {COLUMNS.map(c => (
            <nav key={c.title} className="ft-col" aria-label={c.title}>
              <div className="ft-col-title">{c.title}</div>
              <ul className="list-unstyled mb-0">
                {c.links.map(l => (
                  <li key={l.to}><Link to={l.to} className="ft-link"><BioIcon icon={l.icon} />{l.label}</Link></li>))}
              </ul>
            </nav>))}
        </div>

        <div className="ft-bottom">
          <div className="ft-copy">
            <i className="bi bi-mortarboard me-1"></i>Final Year Project, BS Computer Science · COMSATS University Islamabad, Lahore · 2026–2027
          </div>
          <div className="ft-copy">
            Data: {SOURCES.map((s, i) => (
              <span key={s.href}>{i ? ' · ' : ''}<a href={s.href} target="_blank" rel="noopener noreferrer" className="ft-inline-link">{s.label}</a></span>))}
          </div>
          <div className="ft-copy ft-disclaimer"><i className="bi bi-shield-exclamation me-1"></i>For research and teaching, not clinical decisions</div>
          <button type="button" className="ft-top" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Back to top">
            <i className="bi bi-arrow-up"></i>
          </button>
        </div>
      </div>
    </footer>
  );
}
