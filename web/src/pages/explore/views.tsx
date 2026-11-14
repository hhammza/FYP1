/* The dashboard's outcome views (points 6 to 10 of docs/INSTRUCTOR_REQUIREMENTS_PLAN.md).
   Each one reads the shared filters and asks /api/explore/ for its numbers. */
import { useCallback, useEffect, useMemo, useState } from 'react';
import Plot, { type PlotTheme } from '../../components/Plot';
import { apiGet, errorText } from '../../lib/api';
import { capitalise } from '../../lib/vocab';
import { BINS, dominantMap, rateBars, rateMap, splitBars, trendLines } from './charts';
import DrugCatalog from './DrugCatalog';
import { filterQuery, type Filters } from './filters';
import type { Countries, ExploreMeta, Summary, SummaryRow } from './types';
import CellLoader from '../../components/CellLoader';

// the mouse wheel scrolls the page, not the map; drag pans and double-click zooms
const MAP_CONFIG = { topojsonURL: '/topojson/', scrollZoom: false };

type Loaded<T> = { state: 'loading' } | { state: 'ready'; data: T } | { state: 'failed'; error: string };

/** GET an /api/explore/ path again whenever it changes; retry() asks again. */
export function useExplore<T>(path: string | null): Loaded<T> & { retry: () => void } {
  const [value, setValue] = useState<Loaded<T>>({ state: 'loading' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!path) return;
    let alive = true;
    setValue({ state: 'loading' });
    apiGet<T>(path).then(data => { if (alive) setValue({ state: 'ready', data }); })
      .catch(e => { if (alive) setValue({ state: 'failed', error: errorText(e) }); });
    return () => { alive = false; };
  }, [path, attempt]);
  return useMemo(() => ({ ...value, retry: () => setAttempt(a => a + 1) }), [value]);
}

/** A failed request: what went wrong and a button to ask again. */
export function LoadError({ error, retry }: { error: string; retry: () => void }) {
  return (
    <div className="explore-error" role="alert">
      <i className="bi bi-plug explore-error-icon" aria-hidden="true"></i>
      <div className="flex-grow-1">
        <div className="fw-600">Could not load the Explorer data</div>
        <div className="small">{error}</div>
      </div>
      <button type="button" className="btn btn-sm btn-model" onClick={retry}><i className="bi bi-arrow-clockwise me-1"></i>Try again</button>
    </div>
  );
}

function Status({ value }: { value: Loaded<unknown> & { retry: () => void } }) {
  if (value.state === 'loading') return <CellLoader />;
  if (value.state === 'failed') return <LoadError error={value.error} retry={value.retry} />;
  return null;
}

/** In place of a chart when the filters match no lab results. */
export function NoResults() {
  return (
    <div className="text-muted small py-4 text-center" role="status">
      <i className="bi bi-funnel me-1"></i>No lab results for these filters. Clear a filter or widen the years.
    </div>
  );
}

function TableView({ rows, label, valueName }: { rows: SummaryRow[]; label: (r: SummaryRow) => string; valueName: string }) {
  return (
    <details className="mt-2">
      <summary className="small text-muted">Show as a table</summary>
      <div className="table-responsive mt-2" style={{ maxHeight: 320 }}>
        <table className="table table-custom table-sm mb-0">
          <thead><tr><th>{valueName}</th><th className="text-end">Resistant %</th><th className="text-end">Resistant</th><th className="text-end">Tested</th><th>Sample</th></tr></thead>
          <tbody>{rows.map(r => (
            <tr key={`${r.value}|${r.split ?? ''}`}>
              <td>{label(r)}{r.split !== undefined && r.split !== null ? ` (${r.split})` : ''}</td>
              <td className="text-end">{r.resistant_pct === null ? 'n/a' : `${r.resistant_pct.toFixed(1)}%`}</td>
              <td className="text-end">{r.r.toLocaleString()}</td><td className="text-end">{r.n.toLocaleString()}</td>
              <td>{r.low_sample ? <span className="badge bg-secondary">low sample</span> : ''}</td>
            </tr>))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

function Legend({ minN }: { minN: number }) {
  return (
    <div className="d-flex flex-wrap align-items-center gap-3 small mt-2" aria-label="Map legend">
      {['0-20', '20-40', '40-60', '60-80', '80-100'].map((b, i) => (
        <span key={b}><span className="legend-swatch" style={{ background: BINS[i] }}></span>{b}%</span>))}
      <span><span className="legend-swatch no-data"></span>No data</span>
      <span><span className="legend-swatch" style={{ background: BINS[3], opacity: 0.35 }}></span>Low sample (n &lt; {minN})</span>
    </div>
  );
}

const hasCountryData = (c: Countries) => c.countries.some(r => r.n > 0);

/** Point 10: choropleth heat map, resistance rate or dominant resistance type; a click sets the Country filter. */
export function CountryHeatMap({ filters, mode, onCountry }: {
  filters: Filters; mode: 'rate' | 'dominant'; onCountry: (iso3: string) => void;
}) {
  const res = useExplore<Countries>(`explore/countries/${filterQuery(filters)}`);
  const figure = useCallback((t: PlotTheme) => {
    if (res.state !== 'ready') return { data: [], layout: {} };
    const rows = res.data.countries;
    return mode === 'rate' ? rateMap(rows, t) : dominantMap(rows, res.data.resistance_types.map(r => r.resistance_type), t);
  }, [res, mode]);
  const click = useCallback((iso3: unknown) => { if (typeof iso3 === 'string') onCountry(iso3); }, [onCountry]);
  return (
    <div className="glass-card">
      <h2 className="h5 mb-2">{mode === 'rate' ? 'Which country has which resistance' : 'The highest resistance type in each country'}</h2>
      <p className="caption-text mb-2">{mode === 'rate'
        ? 'Colour is resistant ÷ tested for the current filters.'
        : 'Colour is the resistance type (MRSA, VRE, CRE and so on) with the highest rate among isolates tested for it.'} Click a country to filter every view to it.
        BV-BRC holds the isolates labs chose to sequence, not a country's surveillance, so a country's figure describes its submitted isolates.</p>
      <Status value={res} />
      {res.state === 'ready' && (!hasCountryData(res.data) ? <NoResults /> : <>
        <Plot id="heatMap" style={{ height: 460 }} figure={figure} config={MAP_CONFIG} onPointClick={click} />
        {mode === 'rate' ? <Legend minN={res.data.min_n} /> : (
          <div className="small text-muted mt-2">{res.data.resistance_types.map(r => <div key={r.resistance_type}><b>{r.resistance_type}</b>: {r.label}{r.note ? ` (${r.note})` : ''}</div>)}</div>
        )}
      </>)}
    </div>
  );
}

/** Point 6: map for one antibiotic group. */
export function GroupMap({ filters, meta, group, setGroup, onCountry }: {
  filters: Filters; meta: ExploreMeta; group: string; setGroup: (g: string) => void; onCountry: (iso3: string) => void;
}) {
  const chosen = group || meta.antibiotic_hierarchy.find(f => f.family === 'Beta-lactams')?.subfamilies.find(s => s.subfamily === 'Carbapenems')?.subfamily || '';
  const res = useExplore<Countries>(`explore/countries/${filterQuery(filters, { subfamily: chosen })}`);
  const figure = useCallback((t: PlotTheme) => (res.state === 'ready' ? rateMap(res.data.countries, t) : { data: [], layout: {} }), [res]);
  const click = useCallback((iso3: unknown) => { if (typeof iso3 === 'string') onCountry(iso3); }, [onCountry]);
  return (
    <div className="glass-card">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
        <h2 className="h5 mb-0">Resistance by antibiotic group</h2>
        <select className="form-select form-select-sm form-select-custom w-auto" aria-label="Antibiotic group" value={chosen} onChange={e => setGroup(e.target.value)}>
          {meta.antibiotic_hierarchy.map(f => (
            <optgroup key={f.family} label={f.family}>
              {f.subfamilies.map(s => <option key={s.subfamily} value={s.subfamily}>{s.subfamily}</option>)}
            </optgroup>))}
        </select>
      </div>
      <Status value={res} />
      {res.state === 'ready' && (!hasCountryData(res.data) ? <NoResults />
        : <><Plot id="groupMap" style={{ height: 440 }} figure={figure} config={MAP_CONFIG} onPointClick={click} /><Legend minN={res.data.min_n} /></>)}
    </div>
  );
}

const SPLITS: Record<string, string> = { '': 'No split', gram: 'Gram stain', genus: 'Organism', country: 'Country', infection_type: 'Infection type' };

/** Point 7: resistance per antibiotic group, sorted, optionally split. */
export function GroupComparison({ filters, split, setSplit }: {
  filters: Filters; split: string; setSplit: (s: string) => void;
}) {
  const [level, setLevel] = useState<'family' | 'subfamily'>('subfamily');
  const res = useExplore<Summary>(`explore/summary/${filterQuery(filters, { by: level, split })}`);
  const figure = useCallback((t: PlotTheme) => {
    if (res.state !== 'ready') return { data: [], layout: {} };
    return split ? splitBars(res.data.rows, t) : rateBars(res.data.rows, t);
  }, [res, split]);
  const rows = res.state === 'ready' ? res.data.rows : [];
  return (
    <div className="glass-card">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
        <h2 className="h5 mb-0">Group-wise comparison</h2>
        <div className="d-flex gap-2">
          <select className="form-select form-select-sm form-select-custom w-auto" aria-label="Group level" value={level} onChange={e => setLevel(e.target.value as 'family' | 'subfamily')}>
            <option value="family">Families</option><option value="subfamily">Subfamilies</option>
          </select>
          <select className="form-select form-select-sm form-select-custom w-auto" aria-label="Split by" value={split} onChange={e => setSplit(e.target.value)}>
            {Object.entries(SPLITS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      </div>
      <Status value={res} />
      {res.state === 'ready' && (!rows.length ? <NoResults /> : <>
        <Plot id="groupBars" style={{ height: Math.max(300, 26 * new Set(rows.map(r => r.value)).size * (split ? 1.6 : 1) + 80) }} figure={figure} />
        <TableView rows={rows} label={r => String(r.value)} valueName="Group" />
      </>)}
    </div>
  );
}

/** Point 8: the drugs of one group side by side, with n and the yearly trend. */
export function DrugComparison({ filters, meta, group, setGroup, onDrug }: {
  filters: Filters; meta: ExploreMeta; group: string; setGroup: (g: string) => void; onDrug: (d: string) => void;
}) {
  const chosen = group || 'Carbapenems';
  const extra = { subfamily: chosen, antibiotic: '' };
  const res = useExplore<Summary>(`explore/summary/${filterQuery({ ...filters, lists: { ...filters.lists, antibiotic: [] } }, { ...extra, by: 'antibiotic' })}`);
  const trend = useExplore<Summary>(`explore/summary/${filterQuery({ ...filters, lists: { ...filters.lists, antibiotic: [] } }, { ...extra, by: 'year', split: 'antibiotic' })}`);
  const bars = useCallback((t: PlotTheme) => (res.state === 'ready' ? rateBars(res.data.rows, t, r => capitalise(String(r.value))) : { data: [], layout: {} }), [res]);
  const lines = useCallback((t: PlotTheme) => (trend.state === 'ready' ? trendLines(trend.data.rows, t, trend.data.min_n) : { data: [], layout: {} }), [trend]);
  const click = useCallback((d: unknown) => { if (typeof d === 'string') onDrug(d); }, [onDrug]);
  return (
    <div className="glass-card">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
        <h2 className="h5 mb-0">Drug-wise comparison</h2>
        <select className="form-select form-select-sm form-select-custom w-auto" aria-label="Antibiotic group to compare" value={chosen} onChange={e => setGroup(e.target.value)}>
          {meta.antibiotic_hierarchy.map(f => (
            <optgroup key={f.family} label={f.family}>
              {f.subfamilies.map(s => <option key={s.subfamily} value={s.subfamily}>{s.subfamily}</option>)}
            </optgroup>))}
        </select>
      </div>
      <p className="caption-text mb-2">Click a bar for the drug's nomenclature and chemistry.</p>
      <Status value={res} />
      {res.state === 'ready' && (!res.data.rows.length ? <NoResults /> : <>
        <Plot id="drugBars" style={{ height: Math.max(220, 34 * res.data.rows.length + 80) }} figure={bars} onPointClick={click} />
        <TableView rows={res.data.rows} label={r => capitalise(String(r.value))} valueName="Antibiotic" />
      </>)}
      <h3 className="h6 mt-4">Trend over collection years</h3>
      <Status value={trend} />
      {trend.state === 'ready' && (trend.data.rows.length
        ? <Plot id="drugTrend" style={{ height: 320 }} figure={lines} />
        : <div className="text-muted small">No dated isolates for these filters.</div>)}
    </div>
  );
}

/** Point 9: resistance across chemical groups, each group's drugs, and each drug's chemistry. */
export function ChemistryView({ filters, meta, onDrug }: { filters: Filters; meta: ExploreMeta; onDrug: (d: string) => void }) {
  const res = useExplore<Summary>(`explore/summary/${filterQuery(filters, { by: 'chemical_group' })}`);
  return (
    <div className="glass-card">
      <h2 className="h5">Chemistry: resistance across chemical groups</h2>
      <p className="caption-text">The structural class of each drug, kept apart from its family (a family can span several
        structures). Pick a group on the left to see its drugs, then a drug for its structure, formula, mechanism and the
        resistance mechanisms that act on its chemistry.</p>
      <Status value={res} />
      <DrugCatalog filters={filters} meta={meta} onDrug={onDrug} />
      {res.state === 'ready' && <TableView rows={res.data.rows} label={r => String(r.value)} valueName="Chemical group" />}
    </div>
  );
}

