/* The dashboard's filters (points 1 to 5 of docs/INSTRUCTOR_REQUIREMENTS_PLAN.md).
   Every view on the page reads the same filters from the URL. */
import { useMemo } from 'react';
import MultiSelect, { type MSGroup } from '../../components/MultiSelect';
import { capitalise } from '../../lib/vocab';
import { activeCount, type Filters } from './filters';
import type { ExploreMeta } from './types';

const GRAM_LABEL = { positive: 'Gram-positive', negative: 'Gram-negative', other: 'Other (acid-fast)' } as const;

interface Props {
  meta: ExploreMeta;
  filters: Filters;
  update: (changes: Record<string, string | string[] | boolean | null>) => void;
  clear: () => void;
}

/** A From year later than the To year, which matches nothing. */
export const yearsReversed = (f: Filters) =>
  Boolean(f.year_from && f.year_to) && Number(f.year_from) > Number(f.year_to);

export default function FilterBar({ meta, filters, update, clear }: Props) {
  const f = filters.lists;

  // 1. Organisms, under Gram-positive / Gram-negative headers; a header picks the whole stain
  const organismGroups: MSGroup[] = useMemo(() => meta.organisms.map(o => ({
    header: GRAM_LABEL[o.gram],
    options: o.genera.map(g => ({ value: g.genus, label: g.genus, n: g.n })),
    select: () => update({ gram: [o.gram], genus: null, species: null }),
  })), [meta, update]);

  // 2. Antibiotic groups: subfamilies under their family; choosing groups selects their drugs
  const drugsOf = useMemo(() => {
    const m = new Map<string, string[]>();
    for (const fam of meta.antibiotic_hierarchy) for (const s of fam.subfamilies) m.set(s.subfamily, s.antibiotics.map(a => a.value));
    return m;
  }, [meta]);
  const groupGroups: MSGroup[] = useMemo(() => meta.antibiotic_hierarchy.map(fam => ({
    header: fam.family,
    options: fam.subfamilies.map(s => ({ value: s.subfamily, label: s.subfamily, n: s.antibiotics.reduce((t, a) => t + a.n, 0) })),
    select: () => chooseGroups(fam.subfamilies.map(s => s.subfamily)),
  })), [meta]); // eslint-disable-line react-hooks/exhaustive-deps
  function chooseGroups(subfamilies: string[]) {
    update({ subfamily: subfamilies, family: null, antibiotic: subfamilies.flatMap(s => drugsOf.get(s) || []) });
  }
  const drugGroups: MSGroup[] = useMemo(() => meta.antibiotic_hierarchy.flatMap(fam => fam.subfamilies.map(s => ({
    header: `${fam.family} › ${s.subfamily}`,
    options: s.antibiotics.map(a => ({ value: a.value, label: capitalise(a.value), n: a.n })),
  }))), [meta]);

  // 4. Infection type and disease narrow each other
  const diseaseOptions = useMemo(() => {
    const allowed = f.infection_type.length ? new Set(f.infection_type.flatMap(t => meta.disease_by_infection_type[t] || [])) : null;
    return meta.diseases.filter(d => !allowed || allowed.has(d.value));
  }, [meta, f.infection_type]);
  const infectionOptions = useMemo(() => {
    const allowed = f.disease.length ? new Set(f.disease.map(d => meta.disease_infection_type[d])) : null;
    return meta.infection_types.filter(t => !allowed || allowed.has(t.value));
  }, [meta, f.disease]);

  const gram = f.gram[0] || '';
  const n = activeCount(filters);

  return (
    <div className="glass-card mb-4 explore-filters" aria-label="Filters">
      <div className="d-flex flex-wrap align-items-center justify-content-between mb-3 gap-2">
        <div className="section-label mb-0"><i className="bi bi-funnel me-2"></i>Filters {n > 0 && <span className="badge rounded-pill filter-count ms-1">{n}</span>}</div>
        {/* the Gram buttons and Clear stay together on the right; Clear is always
            there (disabled with no filters) so nothing shifts when a filter is set */}
        <div className="d-flex flex-wrap align-items-center gap-2 ms-auto">
        <div className="btn-group btn-group-sm" role="group" aria-label="Gram stain">
          {(['', 'positive', 'negative', 'other'] as const).map(g => (
            <button key={g || 'all'} type="button" className={'btn btn-model' + (gram === g ? ' active' : '')}
                    aria-pressed={gram === g} onClick={() => update({ gram: g ? [g] : null, genus: null, species: null })}>
              {g ? GRAM_LABEL[g] : 'All organisms'}
            </button>
          ))}
        </div>
        <button type="button" className="btn btn-sm btn-model filter-clear" onClick={clear} disabled={n === 0}
                title={n ? 'Clear all filters' : 'No filters set'}><i className="bi bi-x-lg me-1"></i>Clear filters</button>
        </div>
      </div>
      <div className="row g-3">
        <div className="col-md-4 col-lg-3">
          <MultiSelect label="Organism" groups={gram ? organismGroups.filter(g => g.header === GRAM_LABEL[gram as keyof typeof GRAM_LABEL]) : organismGroups}
                       selected={f.genus} onChange={v => update({ genus: v })} placeholder="All organisms" />
        </div>
        <div className="col-md-4 col-lg-3">
          <MultiSelect label="Antibiotic group" groups={groupGroups} selected={f.subfamily}
                       onChange={chooseGroups} placeholder="All groups" />
        </div>
        <div className="col-md-4 col-lg-3">
          <MultiSelect label="Antibiotic" groups={drugGroups} selected={f.antibiotic}
                       onChange={v => update({ antibiotic: v })} placeholder="All antibiotics" />
        </div>
        <div className="col-md-4 col-lg-3">
          <MultiSelect label="Chemical group" groups={[{ header: '', options: meta.chemical_groups }]} selected={f.chemical_group}
                       onChange={v => update({ chemical_group: v })} placeholder="All chemical groups" />
        </div>
        <div className="col-md-4 col-lg-3">
          <MultiSelect label="Country" groups={[{ header: '', options: meta.countries }]} selected={f.country}
                       onChange={v => update({ country: v })} placeholder="All countries" />
        </div>
        <div className="col-md-4 col-lg-3">
          <MultiSelect label="Infection type" groups={[{ header: '', options: infectionOptions }]} selected={f.infection_type}
                       onChange={v => update({ infection_type: v })} placeholder="All infection types" />
        </div>
        <div className="col-md-4 col-lg-3">
          <MultiSelect label="Disease" groups={[{ header: '', options: diseaseOptions.map(d => ({ ...d, label: capitalise(d.label) })) }]}
                       selected={f.disease} onChange={v => update({ disease: v })} placeholder="All diseases" />
        </div>
        <div className="col-md-4 col-lg-3">
          <span className="form-label-custom d-block">Collection years</span>
          <div className="d-flex gap-2">
            <input type="number" className="form-control form-control-custom" aria-label="From year" placeholder={String(meta.year_range?.[0] ?? '')}
                   value={filters.year_from} onChange={e => update({ year_from: e.target.value })} />
            <input type="number" className="form-control form-control-custom" aria-label="To year" placeholder={String(meta.year_range?.[1] ?? '')}
                   value={filters.year_to} onChange={e => update({ year_to: e.target.value })} />
          </div>
          {yearsReversed(filters) && (
            <div className="small text-danger mt-1" role="alert">"From" is after "To": swap the years to see results.</div>)}
        </div>
      </div>
      <div className="d-flex flex-wrap align-items-center gap-4 mt-3 small">
        <div className="form-check form-switch mb-0 d-flex align-items-center gap-2">
          <input className="form-check-input" type="checkbox" id="includeIntermediate" checked={filters.include_intermediate}
                 onChange={e => update({ include_intermediate: e.target.checked })} />
          <label className="form-check-label" htmlFor="includeIntermediate">Count intermediate results as resistant</label>
        </div>
        <div className="d-flex align-items-center gap-2">
          <label htmlFor="minN">Low sample below</label>
          <input id="minN" type="number" min={1} className="form-control form-control-sm form-control-custom" style={{ width: 80 }}
                 placeholder={String(meta.min_n_default)} value={filters.min_n} onChange={e => update({ min_n: e.target.value })} />
          <span className="text-muted">isolates</span>
        </div>
      </div>
    </div>
  );
}
