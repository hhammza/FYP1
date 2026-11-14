/* Points 9 and 12: a drug's nomenclature and chemistry, in a popup that
   opens from any dropdown, bar or button (the drug is kept in the URL). */
import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router';
import { apiUrl } from '../../lib/api';
import { capitalise } from '../../lib/vocab';
import { filterQuery, type Filters } from './filters';
import type { DrugDetail as Detail, Summary } from './types';
import { useExplore } from './views';

const AWARE_CLASS: Record<string, string> = { Access: 'bg-success', Watch: 'bg-warning text-dark', Reserve: 'bg-danger' };
const na = <span className="text-muted">not available</span>;

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return <tr><th scope="row" className="text-muted fw-normal">{label}</th><td>{children || na}</td></tr>;
}

export default function DrugDetail({ name, filters, onClose }: { name: string; filters: Filters; onClose: () => void }) {
  const res = useExplore<Detail>(`explore/drug/${encodeURIComponent(name)}/${filterQuery(filters)}`);
  const closeBtn = useRef<HTMLButtonElement>(null);
  // Escape closes it; the page behind does not scroll while it is open; focus starts on Close
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    document.body.classList.add('modal-open');
    closeBtn.current?.focus();
    return () => { window.removeEventListener('keydown', onKey); document.body.classList.remove('modal-open'); };
  }, [onClose]);
  const titleId = 'drugModalTitle';
  // A centred popup, rendered on <body> so the navbar and footer cannot paint over it
  return createPortal(
    <>
      <div className="modal-backdrop fade show"></div>
      <div className="modal fade show d-block drug-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}
           onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
        <div className="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable drug-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <div className="d-flex flex-wrap align-items-center gap-2">
                <h2 id={titleId} className="modal-title h4 mb-0 me-2">{capitalise(name)}</h2>
                {res.state === 'ready' && <>
                  <span className="badge bg-primary">{res.data.family}</span>
                  <span className="badge bg-secondary">{res.data.subfamily}</span>
                  <span className={`badge ${AWARE_CLASS[res.data.aware] || 'bg-light text-dark'}`}>AWaRe: {res.data.aware}</span>
                </>}
              </div>
              <button ref={closeBtn} type="button" className="btn-close" aria-label="Close" onClick={onClose}></button>
            </div>
            <div className="modal-body">
              {res.state === 'loading' && <div className="text-muted py-4"><span className="spinner-border spinner-border-sm me-2"></span>Loading…</div>}
              {res.state === 'failed' && <div className="alert-warning-custom">{res.error}</div>}
              {res.state === 'ready' && <Body d={res.data} filters={filters} />}
            </div>
          </div>
        </div>
      </div>
    </>,
    document.body,
  );
}

function Body({ d, filters }: { d: Detail; filters: Filters }) {
  const brands = [...new Set(d.components.flatMap(c => c.brand_names_guess))];
  const structures = d.components.filter(c => c.structure_url);
  // Three columns on a wide screen (structure | nomenclature | chemistry), so the
  // whole record fits without scrolling; they stack on a narrow one
  return (
    <div className="row g-4 drug-body">
      <div className="col-lg-3 drug-left">
        {d.alias_of && <p className="small text-muted">"{d.requested}" is a spelling of {d.alias_of} in the source data.</p>}
        {structures.map(c => (
          <figure key={c.pubchem_cid} className="text-center mb-3">
            <img src={apiUrl(c.structure_url as string)} alt={`2D structure of ${c.name}`} className="drug-structure" />
            <figcaption className="small text-muted mt-1">{c.name} (PubChem)</figcaption>
          </figure>))}
        <div className="drug-resistance">
          <div className="small text-muted">Laboratory resistance (current filters)</div>
          <div className="drug-resistance-val">{d.resistance.resistant_pct === null ? 'n/a' : `${d.resistance.resistant_pct.toFixed(1)}%`}</div>
          <div className="small">{d.resistance.r.toLocaleString()} of {d.resistance.n.toLocaleString()} isolates resistant
            {d.resistance.low_sample && <span className="badge bg-secondary ms-2">low sample</span>}</div>
        </div>
      </div>

      <div className="col-lg-5">
        <h3 className="h6 section-label">Nomenclature</h3>
        <table className="table table-sm mb-0 drug-table"><tbody>
          <Row label="Generic name">{capitalise(d.antibiotic)}</Row>
          <Row label="Brand names">{brands.length ? <>{brands.join(', ')}<div className="drug-note">From PubChem synonyms; may be incomplete</div></> : null}</Row>
          <Row label="IUPAC name">{d.components.map(c => <div key={c.pubchem_cid} className="small text-break">{d.components.length > 1 ? `${c.name}: ` : ''}{c.iupac_name}</div>)}</Row>
          <Row label="ATC code">{d.atc_code}</Row>
          <Row label="Family / subfamily">{`${d.family} › ${d.subfamily}`}</Row>
          <Row label="Chemical group">{d.chemical_group}</Row>
          <Row label="WHO AWaRe">{d.aware}</Row>
          <Row label="PubChem CID">{d.components.length ? d.components.map(c => (
            <a key={c.pubchem_cid} className="me-2" href={c.pubchem_url} target="_blank" rel="noreferrer">{c.pubchem_cid}</a>)) : null}</Row>
          <Row label="Use">{d.use}</Row>
        </tbody></table>
      </div>

      <div className="col-lg-4">
        <h3 className="h6 section-label">Chemistry</h3>
        <table className="table table-sm mb-2 drug-table"><tbody>
          <Row label="Core structure">{d.core_structure}</Row>
          <Row label="Formula">{d.components.map(c => c.molecular_formula).filter(Boolean).join(' + ') || null}</Row>
          <Row label="Molecular weight">{d.components.filter(c => c.molecular_weight).map(c => `${c.molecular_weight} g/mol`).join(' + ') || null}</Row>
          <Row label="Mechanism">{d.mechanism}</Row>
          <Row label="Target">{d.target}</Row>
          <Row label="Resistance mechanisms">{d.resistance_mechanism}</Row>
        </tbody></table>
        <ResistanceBy drug={d.antibiotic} filters={filters} />
        {d.missing_from_pubchem.length > 0 && <p className="small text-muted mb-1">Not found in PubChem: {d.missing_from_pubchem.join(', ')}.</p>}
        {d.review && <p className="small text-muted mb-0">Reference note: {d.review}</p>}
      </div>
    </div>
  );
}

const BREAKDOWNS = [
  { by: 'country', tab: 'Country', plural: ['country', 'countries'] },
  { by: 'species', tab: 'Bacteria', plural: ['species', 'species'] },
  { by: 'infection_type', tab: 'Infection type', plural: ['infection type', 'infection types'] },
  { by: 'disease', tab: 'Disease', plural: ['disease', 'diseases'] },
] as const;

/** Where this drug meets the most resistance: by country, bacterial species,
    infection type or recorded disease, under the current filters. The groups
    with the highest resistant share among those with enough isolates. */
function ResistanceBy({ drug, filters }: { drug: string; filters: Filters }) {
  const [tab, setTab] = useState<typeof BREAKDOWNS[number]['by']>('country');
  const b = BREAKDOWNS.find(x => x.by === tab)!;
  const mine: Filters = { ...filters, lists: { ...filters.lists, antibiotic: [drug] } };
  const res = useExplore<Summary>(`explore/summary/${filterQuery(mine, { by: tab })}`);
  const rows = res.state === 'ready'
    ? res.data.rows.filter(r => r.resistant_pct !== null && String(r.value) !== '' && String(r.value) !== 'Unknown') : [];
  const enough = rows.filter(r => !r.low_sample);
  const top = enough.slice(0, 6);
  const minN = res.state === 'ready' ? res.data.min_n : 30;
  const name = (r: Summary['rows'][number]) => {
    const v = String(r.label || r.value);
    return tab === 'disease' ? v.charAt(0).toUpperCase() + v.slice(1) : v;
  };
  return (
    <div className="drug-countries mt-3">
      <div className="d-flex justify-content-between align-items-baseline mb-1">
        <h3 className="h6 section-label mb-0">Resistance by</h3>
        {tab === 'country' && <Link className="small" to={`/explore/heatmap${filterQuery(mine)}`}>See on the map</Link>}
      </div>
      <div className="drug-tabs mb-2" role="tablist" aria-label="Resistance by">
        {BREAKDOWNS.map(x => (
          <button key={x.by} type="button" role="tab" aria-selected={tab === x.by}
                  className={'drug-tab' + (tab === x.by ? ' active' : '')} onClick={() => setTab(x.by)}>{x.tab}</button>))}
      </div>
      <div className="drug-note mb-2">% of lab-tested isolates resistant to this drug, per {b.plural[0]}</div>
      {res.state === 'loading' && <div className="small text-muted py-2"><span className="spinner-border spinner-border-sm me-2"></span>Loading…</div>}
      {res.state === 'failed' && <div className="small text-muted">{res.error}</div>}
      {res.state === 'ready' && (top.length ? top.map(r => (
        <div key={String(r.value)} className="drug-country">
          <span className={'drug-country-name' + (tab === 'species' ? ' fst-italic' : '')} title={name(r)}>{name(r)}</span>
          <span className="drug-country-bar"><span style={{ width: `${r.resistant_pct}%` }}></span></span>
          <span className="drug-country-val" title={`${r.r.toLocaleString()} of ${r.n.toLocaleString()} isolates resistant`}>{(r.resistant_pct as number).toFixed(0)}% <span className="text-muted">of {r.n.toLocaleString()}</span></span>
        </div>)) : <div className="small text-muted">{rows.length ? `None has ${minN} or more isolates tested.` : 'Not recorded for this drug.'}</div>)}
      {res.state === 'ready' && rows.length > 0 && (
        <div className="drug-note mt-1" title="BV-BRC holds the isolates labs chose to submit, not a surveillance sample">
          Highest first · {rows.length} {rows.length === 1 ? b.plural[0] : b.plural[1]}{rows.length > enough.length ? `, ${rows.length - enough.length} under ${minN} isolates hidden` : ''} · submitted isolates</div>)}
    </div>
  );
}
