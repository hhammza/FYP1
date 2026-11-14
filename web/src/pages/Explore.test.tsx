import { fireEvent, screen, within } from '@testing-library/react';
import { Route, Routes, useLocation } from 'react-router';
import Explore, { ExploreRedirect } from './Explore';
import { describeFilters, readFilters, filterQuery } from './explore/filters';
import { yearsReversed } from './explore/FilterBar';
import { HEALTH, mockBackend, renderPage } from '../test-utils';

vi.mock('plotly.js-dist-min', () => ({ default: { react: vi.fn(), purge: vi.fn(), toImage: vi.fn(async () => '') } }));

afterEach(() => vi.unstubAllGlobals());

const META = {
  organisms: [
    { gram: 'positive', genera: [{ genus: 'Staphylococcus', n: 100, species: [] }] },
    { gram: 'negative', genera: [{ genus: 'Escherichia', n: 500, species: [] }] },
    { gram: 'other', genera: [{ genus: 'Mycobacterium', n: 50, species: [] }] },
  ],
  antibiotic_hierarchy: [{ family: 'Beta-lactams', subfamilies: [{ subfamily: 'Carbapenems', antibiotics: [
    { value: 'meropenem', n: 300, aware: 'Watch' }, { value: 'imipenem', n: 200, aware: 'Watch' }] }] }],
  chemical_groups: [{ value: 'Beta-lactam ring', label: 'Beta-lactam ring', n: 500 }],
  countries: [{ value: 'PAK', label: 'Pakistan', n: 40 }],
  infection_types: [{ value: 'Urinary tract infection', label: 'Urinary tract infection', n: 30 }],
  diseases: [{ value: 'urinary tract infection', label: 'urinary tract infection', n: 10 }],
  disease_by_infection_type: { 'Urinary tract infection': ['urinary tract infection'] },
  disease_infection_type: { 'urinary tract infection': 'Urinary tract infection' },
  aware: [], year_range: [2000, 2022], resistance_types: [], min_n_default: 30, build: { lab_rows: 649944 },
};
const COUNTRIES = { min_n: 30, include_intermediate: false, resistance_types: [], countries: [
  { iso3: 'PAK', country: 'Pakistan', tested: 40, n: 40, resistant_pct: 55, low_sample: false, top_types: [], dominant_type: null, dominant_pct: null, top_organism: 'Klebsiella pneumoniae' }] };

describe('Explore', () => {
  it('shows the filters and the heat map from /api/explore/', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { body: META }, 'explore/countries/': { body: COUNTRIES } });
    renderPage(<Explore />, '/explore');
    expect(await screen.findByText('Which country has which resistance')).toBeInTheDocument();
    for (const label of ['Organism', 'Antibiotic group', 'Country', 'Infection type', 'Disease', 'Chemical group']) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
    expect(screen.getByText('649,944 laboratory results')).toBeInTheDocument();
  });

  it('groups organisms under Gram-positive and Gram-negative', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { body: META }, 'explore/countries/': { body: COUNTRIES } });
    renderPage(<Explore />, '/explore');
    fireEvent.click(await screen.findByLabelText('Organism'));
    expect(screen.getAllByText('Gram-positive').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Gram-negative').length).toBeGreaterThan(0);
    expect(screen.getByText('Staphylococcus')).toBeInTheDocument();
  });

  it('says when the backend has no dashboard data', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { status: 503, body: { error: 'Dashboard data not built.' } } });
    renderPage(<Explore />, '/explore');
    expect(await screen.findByText('Dashboard data not built.', { exact: false })).toBeInTheDocument();
  });
});

function Where() { const l = useLocation(); return <span data-testid="where">{l.pathname + l.search}</span>; }

describe('explore pages', () => {
  it('sends /explore and old ?view= links to the page for that view, keeping the filters', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { body: META } });
    renderPage(<Routes><Route path="/explore" element={<ExploreRedirect />} /><Route path="/explore/:view" element={<Where />} /></Routes>,
      '/explore?view=heatmap&mode=dominant&gram=negative');
    expect((await screen.findByTestId('where')).textContent).toBe('/explore/dominant?gram=negative');
  });

  it('opens the view named in the path and links to the others with the same filters', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { body: META }, 'explore/summary/': { body: { rows: [], min_n: 30 } } });
    renderPage(<Routes><Route path="/explore/:view" element={<Explore />} /></Routes>, '/explore/groups?country=PAK');
    expect(await screen.findByRole('heading', { level: 1, name: /Group-wise comparison/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Chemistry/ })).toHaveAttribute('href', '/explore/chemistry?country=PAK');
  });
});

describe('explore views with little or no data', () => {
  const view = (path: string) => renderPage(<Routes><Route path="/explore/:view" element={<Explore />} /></Routes>, path);

  it('says so when the filters match no lab results, instead of an empty chart', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { body: META }, 'explore/summary/': { body: { rows: [], min_n: 30 } } });
    view('/explore/groups?country=XXX');
    expect(await screen.findByText(/No lab results for these filters/)).toBeInTheDocument();
  });

  it('says so on a map when no country has results', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { body: META },
                  'explore/countries/': { body: { ...COUNTRIES, countries: [] } } });
    view('/explore/heatmap?country=XXX');
    expect(await screen.findByText(/No lab results for these filters/)).toBeInTheDocument();
  });

  it('marks a drug tested on too few isolates as a low sample', async () => {
    const row = { value: 'meropenem', split: 'Beta-lactam ring', tested: 7, n: 7, r: 7, intermediate: 0, resistant_pct: 100, low_sample: true };
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { body: META },
                  'explore/summary/': { body: { rows: [row], min_n: 30, total: row } } });
    view('/explore/chemistry');
    const tile = await screen.findByRole('button', { name: /Meropenem/ });
    expect(tile).toHaveClass('low-sample');
    expect(tile).toHaveTextContent('7 tested · low sample');
  });
});

describe('the drug popup', () => {
  const DRUG = {
    antibiotic: 'methicillin', requested: 'methicillin', alias_of: '', family: 'Beta-lactams', subfamily: 'Penicillins',
    aware: 'Not classified', atc_code: 'J01CF03', chemical_group: 'Beta-lactam ring', use: 'Human', core_structure: '',
    mechanism: '', target: '', resistance_mechanism: '', review: '', components: [], missing_from_pubchem: [],
    resistance: { tested: 1, n: 1, r: 1, intermediate: 0, resistant_pct: 100, low_sample: true }, by_year: [],
  };
  const small = { value: 'Staphylococcus aureus', tested: 1, n: 1, r: 1, intermediate: 0, resistant_pct: 100, low_sample: true };

  it('says which filters it uses, and shows small groups faded rather than nothing', async () => {
    mockBackend({ 'health/': { body: HEALTH }, 'explore/meta/': { body: META }, 'explore/countries/': { body: COUNTRIES },
                  'explore/drug/methicillin/': { body: DRUG }, 'explore/summary/': { body: { rows: [small], min_n: 30 } } });
    renderPage(<Routes><Route path="/explore/:view" element={<Explore />} /></Routes>, '/explore/heatmap?country=PAK&drug=methicillin');
    expect(await screen.findByText(/use the page's filters: Country: Pakistan/)).toBeInTheDocument();
    expect(within(screen.getByRole('dialog')).getByRole('button', { name: 'Clear filters' })).toBeInTheDocument();
    expect(await screen.findByText(/the small groups are shown faded/)).toBeInTheDocument();
    expect(screen.getByTitle('Staphylococcus aureus').closest('.drug-country')).toHaveClass('low-sample');
  });
});

describe('explore filters in the URL', () => {
  it('warns when the From year is after the To year', () => {
    expect(yearsReversed(readFilters(new URLSearchParams('year_from=2022&year_to=2010')))).toBe(true);
    expect(yearsReversed(readFilters(new URLSearchParams('year_from=2010&year_to=2022')))).toBe(false);
    expect(yearsReversed(readFilters(new URLSearchParams('year_from=2010')))).toBe(false);
  });

  it('describes the active filters in words', () => {
    const f = readFilters(new URLSearchParams('gram=negative&country=PAK&antibiotic=meropenem&year_from=2015&include_intermediate=1'));
    expect(describeFilters(f, (k, v) => (k === 'country' && v === 'PAK' ? 'Pakistan' : v), ['antibiotic']))
      .toEqual(['Gram stain: Gram-negative', 'Country: Pakistan', 'Years: 2015 to any', 'Intermediate counted as resistant']);
  });

  it('round-trips through the query string', () => {
    const f = readFilters(new URLSearchParams('gram=negative&subfamily=Carbapenems&country=PAK,IND&include_intermediate=1&view=map'));
    expect(f.lists.country).toEqual(['PAK', 'IND']);
    expect(filterQuery(f)).toBe('?gram=negative&subfamily=Carbapenems&country=PAK%2CIND&include_intermediate=1');
  });
});
