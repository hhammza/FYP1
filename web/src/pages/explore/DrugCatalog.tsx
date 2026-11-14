/* The chemistry view (point 9): chemical groups (or drug families) on the left,
   ranked or A to Z with their resistance; the selected group's drugs on the
   right as tiles that open the drug popup. One search box narrows both. */
import { useMemo, useState, type CSSProperties } from 'react';
import { capitalise } from '../../lib/vocab';
import { filterQuery, type Filters } from './filters';
import type { ExploreMeta, Summary, SummaryRow } from './types';
import { useExplore } from './views';

type GroupBy = 'chemical_group' | 'family';
type SortBy = 'name' | 'resistance';

interface Drug { name: string; chem: string; family: string; subfamily: string; row: SummaryRow }
interface Group { title: string; items: Drug[]; r: number; n: number; pct: number | null }

/* resistance colour band: low, moderate, high */
const band = (pct: number | null) => (pct === null ? 'none' : pct >= 50 ? 'high' : pct >= 20 ? 'mid' : 'low');

function Bar({ pct }: { pct: number | null }) {
  return <span className={`drug-tile-bar ${band(pct)}`}><span style={{ width: `${pct ?? 0}%` }}></span></span>;
}

export default function DrugCatalog({ filters, meta, onDrug }: { filters: Filters; meta: ExploreMeta; onDrug: (d: string) => void }) {
  const res = useExplore<Summary>(`explore/summary/${filterQuery(filters, { by: 'antibiotic', split: 'chemical_group' })}`);
  const [groupBy, setGroupBy] = useState<GroupBy>('chemical_group');
  const [sortBy, setSortBy] = useState<SortBy>('resistance');
  const [find, setFind] = useState('');
  const [picked, setPicked] = useState('');

  // drug -> family and subfamily, from the hierarchy the page already has
  const familyOf = useMemo(() => {
    const m = new Map<string, [string, string]>();
    for (const f of meta.antibiotic_hierarchy) for (const s of f.subfamilies) for (const a of s.antibiotics) m.set(a.value, [f.family, s.subfamily]);
    return m;
  }, [meta]);

  const drugs: Drug[] = useMemo(() => (res.state === 'ready'
    ? res.data.rows.map(r => {
      const [family, subfamily] = familyOf.get(String(r.value)) || ['Others', ''];
      return { name: String(r.value), chem: String(r.split || 'Other'), family, subfamily, row: r };
    })
    : []), [res, familyOf]);

  const q = find.trim().toLowerCase();
  const shown = drugs.filter(d => !q || [d.name, d.chem, d.family, d.subfamily].some(x => x.toLowerCase().includes(q)));

  const groups: Group[] = (() => {
    const m = new Map<string, Drug[]>();
    for (const d of shown) {
      const k = groupBy === 'family' ? d.family : d.chem;
      m.set(k, [...(m.get(k) || []), d]);
    }
    return [...m.entries()].map(([title, items]) => {
      const r = items.reduce((s, x) => s + x.row.r, 0);
      const n = items.reduce((s, x) => s + x.row.n, 0);
      return { title, items, r, n, pct: n ? (100 * r) / n : null };
    }).sort((a, b) => (sortBy === 'name' ? a.title.localeCompare(b.title)
      : (b.pct ?? -1) - (a.pct ?? -1) || a.title.localeCompare(b.title)));
  })();

  if (res.state !== 'ready') return null;
  // opens on the group with the most drugs, until the user picks one
  const current = groups.find(g => g.title === picked) || [...groups].sort((a, b) => b.items.length - a.items.length)[0];
  const drugOrder = (a: Drug, b: Drug) => (sortBy === 'name' ? a.name.localeCompare(b.name)
    : (b.row.resistant_pct ?? -1) - (a.row.resistant_pct ?? -1) || a.name.localeCompare(b.name));
  const what = groupBy === 'family' ? 'family' : 'chemical group';

  return (
    <div className="chem-explorer">
      <div className="catalog-tools mb-3">
        <input type="search" className="form-control form-control-sm form-control-custom catalog-search"
               placeholder="Search drugs, groups, families" aria-label="Search drugs" value={find}
               onChange={e => setFind(e.target.value)} />
        <div className="catalog-seg" role="group" aria-label="Group by">
          {(['chemical_group', 'family'] as GroupBy[]).map(k => (
            <button key={k} type="button" className={groupBy === k ? 'active' : ''} aria-pressed={groupBy === k}
                    onClick={() => { setGroupBy(k); setPicked(''); }}>{k === 'family' ? 'Family' : 'Chemical group'}</button>))}
        </div>
        <select className="form-select form-select-sm form-select-custom w-auto" aria-label="Sort by" value={sortBy}
                onChange={e => setSortBy(e.target.value as SortBy)}>
          <option value="resistance">Sort: highest resistance</option>
          <option value="name">Sort: name</option>
        </select>
        <span className="catalog-legend small text-muted ms-lg-auto">
          <span className="catalog-key low"></span>under 20%
          <span className="catalog-key mid"></span>20 to 50%
          <span className="catalog-key high"></span>50% or more resistant
        </span>
      </div>

      {!groups.length
        ? <div className="small text-muted py-3">No drug, group or family matches “{find}”.</div>
        : (
          <div className="chem-split">
            {/* left: the groups */}
            <div className="chem-groups" role="listbox" aria-label={what === 'family' ? 'Families' : 'Chemical groups'}>
              <div className="chem-groups-head small text-muted">{groups.length} {what === 'family' ? 'families' : 'chemical groups'} · {shown.length} drugs</div>
              {groups.map(g => (
                <button key={g.title} type="button" role="option" aria-selected={g === current}
                        className={'chem-group' + (g === current ? ' active' : '')} onClick={() => setPicked(g.title)}>
                  <span className="chem-group-name">{g.title}</span>
                  <span className="chem-group-count">{g.items.length}</span>
                  <Bar pct={g.pct} />
                  <span className="chem-group-pct">{g.pct === null ? 'n/a' : `${g.pct.toFixed(0)}%`}</span>
                </button>))}
            </div>

            {/* right: the selected group's drugs */}
            <div className="chem-detail">
              <div key={current.title} className="chem-detail-head">
                <div>
                  <div className="small text-muted text-uppercase chem-eyebrow">{what}</div>
                  <h3 className="h5 mb-1">{current.title}</h3>
                  <div className="small text-muted">{current.items.length} {current.items.length === 1 ? 'drug' : 'drugs'} ·{' '}
                    {current.r.toLocaleString()} of {current.n.toLocaleString()} lab-tested isolates resistant</div>
                </div>
                <div className={`chem-detail-pct ${band(current.pct)}`}>{current.pct === null ? 'n/a' : `${current.pct.toFixed(1)}%`}</div>
              </div>
              <div className="small text-muted mb-2">Click a drug for its structure, nomenclature and where it meets resistance.</div>
              <div key={`${groupBy}:${current.title}`} className="drug-tiles chem-tiles">
                {[...current.items].sort(drugOrder).map((d, i) => {
                  const p = d.row.resistant_pct;
                  const none = p === null || d.row.n === 0;
                  return (
                    <button key={d.name} type="button" className="drug-tile" onClick={() => onDrug(d.name)} style={{ '--i': Math.min(i, 24) } as CSSProperties}
                            title={`${capitalise(d.name)}: ${none ? 'intermediate results only' : `${(p as number).toFixed(1)}% of ${d.row.n.toLocaleString()} isolates resistant`}`}>
                      <span className="drug-tile-row">
                        <span className="drug-tile-name">{capitalise(d.name)}</span>
                        <span className="drug-tile-pct">{none ? 'n/a' : `${(p as number).toFixed(0)}%`}</span>
                      </span>
                      <Bar pct={none ? null : p} />
                      <span className="drug-tile-sub">{none ? 'Intermediate results only' : `${d.row.n.toLocaleString()} tested`}{groupBy === 'chemical_group' ? ` · ${d.subfamily || d.family}` : ` · ${d.chem}`}</span>
                    </button>);
                })}
              </div>
            </div>
          </div>)}
    </div>
  );
}
