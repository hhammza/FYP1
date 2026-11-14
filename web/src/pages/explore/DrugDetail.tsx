/* Points 9 and 12: a drug's nomenclature and chemistry, in a side panel that
   opens from any dropdown, bar or button (the drug is kept in the URL). */
import { apiUrl } from '../../lib/api';
import { capitalise } from '../../lib/vocab';
import { filterQuery, type Filters } from './filters';
import type { DrugDetail as Detail } from './types';
import { useExplore } from './views';

const AWARE_CLASS: Record<string, string> = { Access: 'bg-success', Watch: 'bg-warning text-dark', Reserve: 'bg-danger' };
const na = <span className="text-muted">not available</span>;

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return <tr><th scope="row" className="text-muted fw-normal" style={{ width: '38%' }}>{label}</th><td>{children || na}</td></tr>;
}

export default function DrugDetail({ name, filters, onClose }: { name: string; filters: Filters; onClose: () => void }) {
  const res = useExplore<Detail>(`explore/drug/${encodeURIComponent(name)}/${filterQuery(filters)}`);
  return (
    <>
      <div className="offcanvas-backdrop fade show" onClick={onClose}></div>
      <aside className="offcanvas offcanvas-end show drug-panel" role="dialog" aria-label={`${capitalise(name)}: nomenclature and chemistry`} style={{ visibility: 'visible', width: 520 }}>
        <div className="offcanvas-header">
          <h2 className="offcanvas-title h5">{capitalise(name)}</h2>
          <button type="button" className="btn-close" aria-label="Close" onClick={onClose}></button>
        </div>
        <div className="offcanvas-body">
          {res.state === 'loading' && <div className="text-muted"><span className="spinner-border spinner-border-sm me-2"></span>Loading…</div>}
          {res.state === 'failed' && <div className="alert-warning-custom">{res.error}</div>}
          {res.state === 'ready' && <Body d={res.data} />}
        </div>
      </aside>
    </>
  );
}

function Body({ d }: { d: Detail }) {
  const brands = [...new Set(d.components.flatMap(c => c.brand_names_guess))];
  return (
    <>
      {d.alias_of && <p className="small text-muted">"{d.requested}" is a spelling of {d.alias_of} in the source data.</p>}
      <div className="d-flex flex-wrap gap-2 mb-3">
        <span className="badge bg-primary">{d.family}</span>
        <span className="badge bg-secondary">{d.subfamily}</span>
        <span className={`badge ${AWARE_CLASS[d.aware] || 'bg-light text-dark'}`}>AWaRe: {d.aware}</span>
      </div>

      <h3 className="h6 section-label">Nomenclature</h3>
      <table className="table table-sm mb-3"><tbody>
        <Row label="Generic name">{capitalise(d.antibiotic)}</Row>
        <Row label="Brand names (from PubChem synonyms, may be incomplete)">{brands.length ? brands.join(', ') : null}</Row>
        <Row label="IUPAC name">{d.components.map(c => <div key={c.pubchem_cid} className="small text-break">{d.components.length > 1 ? `${c.name}: ` : ''}{c.iupac_name}</div>)}</Row>
        <Row label="ATC code">{d.atc_code}</Row>
        <Row label="Family / subfamily">{`${d.family} › ${d.subfamily}`}</Row>
        <Row label="Chemical group">{d.chemical_group}</Row>
        <Row label="WHO AWaRe category">{d.aware}</Row>
        <Row label="PubChem CID">{d.components.length ? d.components.map(c => (
          <a key={c.pubchem_cid} className="me-2" href={c.pubchem_url} target="_blank" rel="noreferrer">{c.pubchem_cid}</a>)) : null}</Row>
        <Row label="Use">{d.use}</Row>
      </tbody></table>

      <h3 className="h6 section-label">Chemistry</h3>
      <div className="d-flex flex-wrap gap-3 mb-2">
        {d.components.filter(c => c.structure_url).map(c => (
          <figure key={c.pubchem_cid} className="text-center mb-0">
            <img src={apiUrl(c.structure_url as string)} alt={`2D structure of ${c.name}`} width={220} className="bg-white rounded border" />
            <figcaption className="small text-muted">{c.name} (PubChem)</figcaption>
          </figure>))}
      </div>
      <table className="table table-sm mb-3"><tbody>
        <Row label="Core structure">{d.core_structure}</Row>
        <Row label="Molecular formula">{d.components.map(c => c.molecular_formula).filter(Boolean).join(' + ') || null}</Row>
        <Row label="Molecular weight">{d.components.filter(c => c.molecular_weight).map(c => `${c.molecular_weight} g/mol`).join(' + ') || null}</Row>
        <Row label="Mechanism of action">{d.mechanism}</Row>
        <Row label="Target">{d.target}</Row>
        <Row label="Resistance mechanisms">{d.resistance_mechanism}</Row>
      </tbody></table>
      {d.missing_from_pubchem.length > 0 && <p className="small text-muted">Not found in PubChem: {d.missing_from_pubchem.join(', ')}.</p>}

      <h3 className="h6 section-label">Laboratory resistance (current filters)</h3>
      <p className="mb-1"><b>{d.resistance.resistant_pct === null ? 'n/a' : `${d.resistance.resistant_pct.toFixed(1)}%`}</b> resistant,{' '}
        {d.resistance.r.toLocaleString()} of {d.resistance.n.toLocaleString()} isolates tested
        {d.resistance.low_sample && <span className="badge bg-secondary ms-2">low sample</span>}</p>
      {d.review && <p className="small text-muted mt-3">Reference note: {d.review}</p>}
    </>
  );
}
