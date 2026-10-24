import { fireEvent, screen, within } from '@testing-library/react';
import Forecast, { forecastPayload } from './Forecast';
import { organismOptions, recognitionMessage } from './forecast/ForecastForm';
import { barColour } from './forecast/ForecastResult';
import { agrees, micText } from './forecast/GenomeInfo';
import type { OrganismGenus } from '../lib/vocab';
import { HEALTH, mockBackend, renderPage } from '../test-utils';

// Plotly needs a real browser; the page tests check everything around the chart
vi.mock('plotly.js-dist-min', () => ({ default: { react: vi.fn(), purge: vi.fn(), toImage: vi.fn(async () => '') } }));

const TREE: OrganismGenus[] = [
  { genus: 'Escherichia', species: [{ name: 'coli', label: 'Escherichia coli', taxon_ids: [562] }],
    other_taxon_ids: [{ id: 561, label: 'Escherichia' }] },
  { genus: 'Campylobacter', species: [{ name: 'coli', label: 'Campylobacter coli', taxon_ids: [195] },
                                      { name: 'jejuni', label: 'Campylobacter jejuni', taxon_ids: [197] }],
    other_taxon_ids: [] },
];

const RESULT = {
  antibiotic: 'ciprofloxacin', prediction: 'Resistant', probability: 0.81, confidence: 100.0, threshold: 0.15,
  drug_class: 'fluoroquinolone', model_used: 'LightGBM (trained)', related_antibiotics: ['levofloxacin'],
  comparison_chart: [{ antibiotic: 'ampicillin', resistance_probability: 43.0 }],
  evidence: { level: 'isolate', label: 'Isolate-level estimate', summary: 'Based on a measured MIC.',
              used_count: 2, total_count: 2,
              inputs: [{ field: 'Antibiotic', value: 'trimethoprim/sulfamethoxazole', state: 'used', detail: 'rate' },
                       { field: 'MIC', value: 4, state: 'used', detail: '4.0 mg/L' }] },
};

afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); });

function backend(extra: Record<string, { status?: number; body: unknown }> = {}) {
  return mockBackend({
    'health/': { body: HEALTH },
    'antibiotics/': { body: { antibiotics: ['ciprofloxacin', 'gentamicin'] } },
    'vocabulary/': { body: { lgbm: { organisms: TREE }, kmer: null } },
    'mic-values/': { body: { antibiotic: 'ciprofloxacin', values: ['0.25', '4'], level: 'species' } },
    'forecast/': { body: RESULT },
    ...extra,
  });
}

describe('organism lists', () => {
  it('offers only the species and taxa of the chosen genus', () => {
    const o = organismOptions(TREE[1], '');
    expect(o.species.map(([v]) => v)).toEqual(['coli', 'jejuni']);
    expect(o.taxa.map(([v]) => v)).toEqual(['195', '197']);
    expect(organismOptions(TREE[1], 'jejuni').taxa).toEqual([['197', '197 · Campylobacter jejuni']]);
  });

  it('adds the genus-level IDs when no species is chosen', () => {
    expect(organismOptions(TREE[0], '').taxa.map(([v]) => v)).toEqual(['562', '561']);
    expect(organismOptions(TREE[0], 'coli').taxa.map(([v]) => v)).toEqual(['562']);
  });

  it('is empty without a genus', () => {
    expect(organismOptions(undefined, 'coli')).toEqual({ species: [], taxa: [] });
  });
});

describe('forecast helpers', () => {
  it('warns what the result will represent', () => {
    expect(recognitionMessage(false, false)).toMatch(/population resistance rate/);
    expect(recognitionMessage(false, true)).toMatch(/historical rates/);
    expect(recognitionMessage(true, false)).toMatch(/MIC drives the result/);
    expect(recognitionMessage(true, true)).toBe('');
  });

  it('never sends the Genome ID or empty fields to the model', () => {
    expect(forecastPayload({ antibiotic: 'ciprofloxacin', genus: 'unknown', species: 'unknown', taxon_id: '',
                             mic_value: '4', mic_sign: '>=', threshold: '0.15', genome_id: '562.1' }))
      .toEqual({ antibiotic: 'ciprofloxacin', mic_value: '4', mic_sign: '>=', threshold: '0.15' });
  });

  it('colours a bar red exactly at the threshold', () => {
    expect(barColour(15, 15)).toMatch(/239,68,68/);
    expect(barColour(14.9, 15)).toMatch(/245,158,11/);
    expect(barColour(5, 15)).toMatch(/34,197,94/);
  });

  it('compares the model with the lab, an Intermediate counting as Resistant', () => {
    expect(agrees('Resistant', 'Intermediate')).toBe(true);
    expect(agrees('Susceptible', 'Resistant')).toBe(false);
    expect(agrees(undefined, 'Resistant')).toBeNull();
    expect(micText({ antibiotic: 'x', value: '16', sign: '>=', is_mic: true })).toBe(' (MIC >= 16 mg/L)');
    expect(micText({ antibiotic: 'x', value: '22', unit: 'mm' })).toBe(' (22 mm, not a MIC)');
  });
});

describe('Forecast page', () => {
  it('links genus to species to taxon and suggests MICs', async () => {
    backend();
    renderPage(<Forecast />, '/forecast');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    await screen.findByRole('option', { name: 'Campylobacter' });
    expect(screen.getByLabelText(/^Species/)).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/^Genus/), { target: { value: 'Campylobacter' } });
    expect(screen.getByText('2 species of Campylobacter')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/^Species/), { target: { value: 'jejuni' } });
    const taxa = within(screen.getByLabelText(/^Taxon ID/)).getAllByRole('option').map(o => o.getAttribute('value'));
    expect(taxa).toEqual(['', '197']);
    expect(await screen.findByText(/Suggested: MICs recorded in BV-BRC for Campylobacter jejuni/)).toBeInTheDocument();
  });

  it('starts the threshold at the model’s validated one and sends it', async () => {
    const calls = backend();
    renderPage(<Forecast />, '/forecast');
    await screen.findByText('0.15', { selector: '#threshVal' });
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.change(screen.getByLabelText(/^MIC Value/), { target: { value: '4' } });
    fireEvent.click(screen.getByRole('button', { name: /Predict Resistance/ }));
    expect(await screen.findByText('Resistant', { selector: '.result-main-label' })).toBeInTheDocument();
    const sent = calls.find(c => c.url.endsWith('/forecast/'));
    expect(JSON.parse(String(sent?.init?.body))).toEqual({ antibiotic: 'ciprofloxacin', mic_value: '4', threshold: '0.15' });
  });

  it('shows the result as the Flask page did', async () => {
    backend();
    renderPage(<Forecast />, '/forecast');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.click(screen.getByRole('button', { name: /Predict Resistance/ }));
    await screen.findByText('Resistant', { selector: '.result-main-label' });
    expect(screen.getByText('ciprofloxacin | Confidence: 100.0%')).toBeInTheDocument();
    expect(screen.getByText('81.0%')).toBeInTheDocument();
    expect(screen.getByText('4.0')).toBeInTheDocument();                     // the MIC as Python printed it
    expect(document.querySelector('wbr')).not.toBeNull();                  // drug pairs can wrap
    expect(screen.getByText('Treatment Concern')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Chart \(PNG\)/ })).toBeInTheDocument();
    expect(document.getElementById('comparisonChart')).not.toBeNull();
  });

  it("shows the backend's refusal instead of a result", async () => {
    backend({ 'forecast/': { status: 400, body: { error: 'mic_value must be a positive number, not "-5".' } } });
    renderPage(<Forecast />, '/forecast');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.click(screen.getByRole('button', { name: /Predict Resistance/ }));
    expect(await screen.findByText(/mic_value must be a positive number/)).toBeInTheDocument();
    expect(screen.getByText('Ready to Forecast')).toBeInTheDocument();
  });

  it('fills the organism from a Genome ID and flags a training genome', async () => {
    backend({ 'genome/1001988.3/': { body: {
      genome_id: '1001988.3', taxon_id: 195, genes_url: '/genes#genome=1001988.3',
      organism: { name: 'Campylobacter coli', genus: 'Campylobacter', species: 'coli', taxon_id: 195 },
      models: { forecast: { role: 'train' } }, lab_results: [], lab_for_antibiotic: [] } } });
    renderPage(<Forecast />, '/forecast');
    await screen.findByRole('option', { name: 'Campylobacter' });
    fireEvent.change(screen.getByLabelText(/^Fill from Genome ID/), { target: { value: '1001988.3' } });
    fireEvent.click(screen.getByRole('button', { name: /Fill/ }));
    expect(await screen.findByText(/The forecaster was trained on this genome/)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Genus/)).toHaveValue('Campylobacter');
    expect(screen.getByLabelText(/^Species/)).toHaveValue('coli');
    expect(screen.getByLabelText(/^Taxon ID/)).toHaveValue('195');
    expect(screen.getByText('Resistance genes for this genome')).toHaveAttribute('href', '/genes#genome=1001988.3');
  });

  it('checks a Genome ID before asking the backend', async () => {
    const calls = backend();
    renderPage(<Forecast />, '/forecast');
    fireEvent.change(screen.getByLabelText(/^Fill from Genome ID/), { target: { value: 'abc' } });
    fireEvent.click(screen.getByRole('button', { name: /Fill/ }));
    expect(await screen.findByText(/looks like 562\.1234/)).toBeInTheDocument();
    expect(calls.some(c => c.url.includes('/genome/'))).toBe(false);
  });

  it('uploads a batch CSV and shows the rows', async () => {
    const calls = backend({ 'forecast/batch/': { body: {
      rows: [{ row: 1, antibiotic: 'ampicillin', genus: 'Klebsiella', species: 'pneumoniae', prediction: 'Resistant', probability: 0.7 },
             { row: 2, antibiotic: 'nope', error: 'Unknown antibiotic' }],
      summary: { rows: 2, predicted: 1, errors: 1, resistant: 1, susceptible: 0,
                 by_antibiotic: [{ antibiotic: 'ampicillin', n: 1, resistant: 1 }] },
      threshold: 0.15, model_run: 'v7', calibrated: true } } });
    renderPage(<Forecast />, '/forecast');
    fireEvent.click(screen.getByRole('tab', { name: /Upload CSV/ }));
    const file = new File(['antibiotic\nampicillin\n'], 'isolates.csv', { type: 'text/csv' });
    fireEvent.change(screen.getByLabelText(/^CSV file/), { target: { files: [file] } });
    // jsdom does not count a file set this way as chosen, so submit the form itself
    fireEvent.submit(screen.getByRole('button', { name: /Predict All Rows/ }).closest('form')!);
    expect(await screen.findByText('Batch results')).toBeInTheDocument();
    expect(screen.getByText('Unknown antibiotic')).toBeInTheDocument();
    expect(screen.getByText(/Model v7, calibrated/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /PDF report/ })).toBeNull();     // batch is CSV only
    const upload = calls.find(c => c.url.endsWith('/forecast/batch/'));
    expect((upload?.init?.body as FormData).get('file')).toBeInstanceOf(File);
  });
});
