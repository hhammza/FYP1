/* /explore: the instructor's dashboard (docs/INSTRUCTOR_REQUIREMENTS_PLAN.md).
   Filters (organism by Gram stain, antibiotic group, country, infection type
   and disease, chemical group) apply to every view; all of it lives in the
   URL, so a view can be shared as a link. Data: /api/explore/. */
import { useCallback, useMemo } from 'react';
import { Link, Navigate, useLocation, useParams } from 'react-router';
import { useTitle } from '../lib/pageEffects';
import DrugDetail from './explore/DrugDetail';
import FilterBar from './explore/FilterBar';
import { EXPLORE_VIEWS } from './explore/nav';
import { filterQuery, useExploreFilters } from './explore/filters';
import type { ExploreMeta } from './explore/types';
import { ChemistryView, CountryHeatMap, DrugComparison, GroupComparison, GroupMap, LoadError, useExplore } from './explore/views';
import CellLoader from '../components/CellLoader';
import BioIcon from '../components/BioIcon';
import HeaderScene from '../components/HeaderScene';

/** /explore and old ?view= links go to the matching page, keeping the filters. */
export function ExploreRedirect() {
  const { search } = useLocation();
  const params = new URLSearchParams(search);
  let view = params.get('view') || 'heatmap';
  if (view === 'heatmap' && params.get('mode') === 'dominant') view = 'dominant';
  params.delete('view'); params.delete('mode');
  const q = params.toString();
  return <Navigate replace to={`/explore/${EXPLORE_VIEWS.some(v => v.key === view) ? view : 'heatmap'}${q ? `?${q}` : ''}`} />;
}

export default function Explore() {
  const { view: param = 'heatmap' } = useParams();
  const current = EXPLORE_VIEWS.find(v => v.key === param) ?? EXPLORE_VIEWS[0];
  const view = current.key;
  useTitle(`${current.label} | Resistance Explorer`);
  const { filters, update, clear, group, drug, split } = useExploreFilters();
  // the filters and the selected group carry over when moving between views
  const carry = filterQuery(filters, { group });
  const meta = useExplore<ExploreMeta>('explore/meta/');
  const onCountry = useCallback((iso3: string) => update({ country: [iso3] }), [update]);
  const onDrug = useCallback((d: string) => update({ drug: d }), [update]);
  const setGroup = useCallback((g: string) => update({ group: g }), [update]);
  const countryNames = useMemo(() => new Map(meta.state === 'ready' ? meta.data.countries.map(c => [c.value, c.label]) : []), [meta]);

  return (
    <>
      <div className="page-header">
        <HeaderScene kind="world" />
        <div className="container-xl">
          <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
            <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
            <li className="breadcrumb-item">Insights</li>
            <li className="breadcrumb-item"><Link to={`/explore/heatmap${carry}`}>Resistance Explorer</Link></li>
            <li className="breadcrumb-item active" aria-current="page">{current.label}</li>
          </ol></nav>
          <div className="d-flex align-items-center gap-3">
            <div className="page-header-icon"><BioIcon icon={current.icon} live /></div>
            <div>
              <h1 className="page-title">{current.label}</h1>
              <p className="page-subtitle">{current.hint}, from laboratory-confirmed BV-BRC results.</p>
            </div>
          </div>
          <div className="explore-facts">
            {meta.state === 'ready' && meta.data.build.lab_rows ? <span><i className="bi bi-clipboard2-pulse"></i>{meta.data.build.lab_rows.toLocaleString()} laboratory results</span> : null}
            <span><i className="bi bi-percent"></i>Resistance = resistant ÷ tested</span>
            <span><i className="bi bi-funnel"></i>Intermediate left out unless switched on</span>
          </div>
        </div>
      </div>

      <div className="container-xl py-4">
        <nav className="explore-tabs mb-3" aria-label="Explorer views">
          {EXPLORE_VIEWS.map(v => (
            <Link key={v.key} to={`/explore/${v.key}${carry}`} aria-current={view === v.key ? 'page' : undefined}
                  className={'explore-tab' + (view === v.key ? ' active' : '')}><BioIcon icon={v.icon} /><span>{v.label}</span></Link>))}
        </nav>

        {meta.state === 'loading' && <CellLoader label="Loading the Explorer…" />}
        {meta.state === 'failed' && <LoadError error={meta.error} retry={meta.retry} />}
        {meta.state === 'ready' && <>
          <FilterBar meta={meta.data} filters={filters} update={update} clear={clear} />

          <div key={view} className="explore-view">
          {(view === 'heatmap' || view === 'dominant') && <CountryHeatMap filters={filters} mode={view === 'dominant' ? 'dominant' : 'rate'} onCountry={onCountry} />}
          {view === 'map' && <GroupMap filters={filters} meta={meta.data} group={group} setGroup={setGroup} onCountry={onCountry} />}
          {view === 'groups' && <GroupComparison filters={filters} split={split} setSplit={s => update({ split: s })} />}
          {view === 'drugs' && <DrugComparison filters={filters} meta={meta.data} group={group} setGroup={setGroup} onDrug={onDrug} />}
          {view === 'chemistry' && <ChemistryView filters={filters} meta={meta.data} onDrug={onDrug} />}
          </div>

          {drug && <DrugDetail name={drug} filters={filters} onClose={() => update({ drug: null })}
                               onClearFilters={clear} countryName={iso3 => countryNames.get(iso3) || iso3} />}
        </>}
      </div>
    </>
  );
}
