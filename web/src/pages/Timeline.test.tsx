import { fireEvent, render, screen, within } from '@testing-library/react';
import Timeline from './Timeline';
import MlForecastCard, { errorSentence, forecastFigure } from './timeline/MlForecastCard';
import RlPanel, { firstFailedWeek, givenResistance, shortDrug, startResistance } from './timeline/RlPanel';
import SimulationResult from './timeline/SimulationResult';
import { SAMPLE_GENOME } from './timeline/SimulationForm';
import type { PlotTheme } from '../components/Plot';
import { forecastGenera } from './timeline/TimelineForm';
import type { MlForecast, RlBlock, SimulationResult as Result } from './timeline/types';
import { jinjaTitle } from '../lib/metrics';
import { HEALTH, mockBackend, renderPage } from '../test-utils';
import { ToastProvider } from '../components/Toasts';

vi.mock('plotly.js-dist-min', () => ({ default: { react: vi.fn(), purge: vi.fn(), toImage: vi.fn(async () => '') } }));

afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); });

const ML: MlForecast = {
  model_run: 'TL_timeline_ml', organism: 'Salmonella', antibiotic: 'ciprofloxacin',
  history: [{ year: 2020, resistant_pct: 100, n: 4 }, { year: 2021, resistant_pct: 54.5, n: 44 }],
  forecast: [{ year: 2022, resistant_pct: 50.5, lo: 25.2, hi: 75.7 }, { year: 2023, resistant_pct: 47.5, lo: 11.8, hi: 83.2 }],
  metrics: { model: { mae_pct: 13.98, ci: [11.84, 16.33] }, last_value: { mae_pct: 14.33, ci: [12.16, 16.73] },
             linear_trend: { mae_pct: 16.75, ci: [14.32, 19.3] }, historical_mean: { mae_pct: 17.25, ci: [15.07, 19.67] } },
  label: 'ML model trained on BV-BRC laboratory results',
};

const RL: RlBlock = {
  drugs: ['ciprofloxacin', 'ampicillin'], n_weeks: 3, agent: 'PPO (stable-baselines3)', best: 'rl',
  policies: [
    { name: 'fixed', label: 'Same drug every week', policy: ['ciprofloxacin', 'ciprofloxacin', 'ciprofloxacin'],
      resistant_fraction: { ciprofloxacin: [1, 20, 55, 70], ampicillin: [1, 1, 1, 1] },
      failure_week: 3, total_reward: -5.123, effective_weeks: 2, mean_burden: 45 },
    { name: 'rl', label: 'RL agent', policy: ['ciprofloxacin', 'ampicillin', 'ciprofloxacin'],
      resistant_fraction: { ciprofloxacin: [1, 20, 15, 30], ampicillin: [1, 1, 8, 6] },
      failure_week: null, total_reward: -1.5, effective_weeks: 3, mean_burden: null },
  ],
};

const RESULT: Result = {
  antibiotic: 'trimethoprim/sulfamethoxazole', antibiotic_class: 'beta-lactam', sequence_length: 461, gc_content: 45.99,
  n_weeks: 2, failure_week: null, final_resistant_percent: 12.0, model_used: 'Biological Simulation',
  summary: 'Resistance stays below 50%.', calibration: { curves: 15, rmse: 2.94, surveillance_curves: 10, drugs: ['meropenem'] },
  timeline: [0, 1, 2].map(w => ({ week: w, susceptible_fraction: 90, intermediate_fraction: 5, resistant_fraction: 5.5 * w,
                                  cumulative_mutations: w, mic_fold_change: 1, treatment_effective: true })),
  mutation_hotspots: [{ position: 12345, original_nucleotide: 'C', mutated_nucleotide: 'T', mutation_type: 'Point mutation' }],
  resistance_genes: [{ gene: 'gyrA', activation_week: 2, resistance_contribution: 4.5 }],
};

const TIMELINE_METRICS = {
  data: { series: 467, lab_results: 534996, train_until: 2016 },
  test_mae_pp: { model: [13.98, [11.84, 16.33]], 'last value': [14.33, [12.16, 16.73]],
                 'linear trend': [16.75, [14.32, 19.3]], 'historical mean': [17.25, [15.07, 19.67]] },
};

function backend(extra: Record<string, { status?: number; body: unknown }> = {}) {
  return mockBackend({
    'health/': { body: { ...HEALTH, models: { ...HEALTH.models, timeline_ml: { trained: true, metrics: TIMELINE_METRICS } } } },
    'timeline/': { body: { ml_forecast: ML, organism_source: 'chosen' } },
    'timeline/simulate/': { body: { ...RESULT, antibiotic: 'ciprofloxacin' } },
    'antibiotics/': { body: { antibiotics: ['ciprofloxacin'] } },
    'vocabulary/': { body: { lgbm: null, kmer: { antibiotics: ['ciprofloxacin'] }, timeline: { genera: { ciprofloxacin: ['Escherichia', 'Salmonella'] } } } },
    ...extra,
  });
}

describe('helpers', () => {
  it('titles words as Jinja did', () => {
    expect(jinjaTitle('beta-lactam')).toBe('Beta-Lactam');
    expect(jinjaTitle('trimethoprim/sulfamethoxazole')).toBe('Trimethoprim/sulfamethoxazole');
    expect(jinjaTitle('polymyxin b')).toBe('Polymyxin B');
  });

  it('reads the resistance of the drug given, at the end of each week', () => {
    expect(givenResistance(RL.policies[1])).toEqual([20, 8, 30]);
    expect(shortDrug('ciprofloxacin')).toBe('ciprofl.');
    expect(shortDrug('ampicil')).toBe('ampicil');
  });
});

describe('RL panel', () => {
  it('is not shown when RL was not run', () => {
    const { container } = render(<RlPanel rl={undefined} nWeeks={8} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('starts on the best policy, marks failed weeks and fills the table', () => {
    render(<RlPanel rl={RL} nWeeks={3} />);
    expect(screen.getByLabelText('Drugs given by')).toHaveValue('1');
    expect(screen.getByRole('option', { name: 'RL agent (best)' })).toBeInTheDocument();
    expect(screen.getByText(/The agent \(PPO \(stable-baselines3\)\)/)).toBeInTheDocument();
    const rows = within(document.querySelector('.rl-table tbody')!).getAllByRole('row');
    expect(rows[0].textContent).toBe('Same drug every weekWeek 32 / 345.0%-5.12');
    expect(rows[1].textContent).toBe('RL agent BestNever in 3 weeks3 / 3—-1.50');
    expect(rows[1]).toHaveClass('report-best-row');
    expect(document.querySelectorAll('.rl-chip-failed')).toHaveLength(0);
    fireEvent.change(screen.getByLabelText('Drugs given by'), { target: { value: '0' } });
    const chips = Array.from(document.querySelectorAll('.rl-chip'));
    expect(chips.map(c => c.textContent)).toEqual(['W1ciprofl.', 'W2ciprofl.', 'W3ciprofl.']);
    // a week fails on the drug's resistance at its start (format §4, answer 4): week 3, as failure_week says
    expect(chips[1]).not.toHaveClass('rl-chip-failed');
    expect(chips[2]).toHaveClass('rl-chip-failed');
    expect(chips[2]).toHaveAttribute('title', 'Week 3: ciprofloxacin, 55.0% resistant at the start, 70.0% at the end');
  });
});

describe('timeline result', () => {
  it('shows the numbers as the Flask page did', () => {
    render(<ToastProvider><SimulationResult result={RESULT} inputs={{ antibiotic: RESULT.antibiotic, n_weeks: '2' }} /></ToastProvider>);
    expect(screen.getByText('Trimethoprim/sulfamethoxazole')).toBeInTheDocument();
    expect(screen.getByText(/Beta-Lactam \| 2-week simulation/)).toBeInTheDocument();
    expect(screen.getByText('Not reached')).toBeInTheDocument();
    expect(screen.getByText('12.0%')).toBeInTheDocument();
    expect(screen.getByText('12,345')).toBeInTheDocument();
    expect(screen.getByText(/Trimethoprim\/sulfamethoxazole was not among the drugs fitted/)).toBeInTheDocument();
    expect(screen.getByText(/±2\.9 points on 10 hospital series/)).toBeInTheDocument();
  });

  it('opens and closes the weekly table', () => {
    render(<ToastProvider><SimulationResult result={RESULT} inputs={{ antibiotic: 'x', n_weeks: '2' }} /></ToastProvider>);
    const table = document.getElementById('timelineTable')!;
    expect(table).toHaveClass('d-none');
    fireEvent.click(screen.getByRole('button', { name: /Toggle/ }));
    expect(table).not.toHaveClass('d-none');
    expect(within(table).getByText('11.0%')).toBeInTheDocument();
    expect(within(table).getAllByText('1.0x')).toHaveLength(3);
  });
});

describe('the RL week rule', () => {
  it('counts a failed week from its start, as failure_week does', () => {
    const p = RL.policies[0];
    expect(startResistance(p)).toEqual([1, 20, 55]);
    expect(givenResistance(p)).toEqual([20, 55, 70]);
    expect(firstFailedWeek(p)).toBe(3);                 // the end-of-week value would say week 2
    for (const q of RL.policies) expect(firstFailedWeek(q)).toBe(q.failure_week);
  });

  it('agrees with the served agent on a 52-week request', () => {
    // imipenem, 52 weeks, from /api/timeline/ (2026-10-25): cycle fails in week 32 on the start rule, 26 on the end rule
    const drugs = ['ciprofloxacin', 'gentamicin', 'imipenem'];
    const rf: Record<string, number[]> = Object.fromEntries(drugs.map(d => [d, Array(53).fill(10)]));
    rf.imipenem[31] = 50;            // the start of week 32
    rf.gentamicin[26] = 52;          // the end of week 26, a gentamicin week, back under 50 at the start of week 27
    const policy = Array.from({ length: 52 }, (_, i) => drugs[(i + 1) % 3]);
    policy[25] = 'gentamicin';
    policy[31] = 'imipenem';
    expect(firstFailedWeek({ name: 'cycle', label: 'Cycle', policy, resistant_fraction: rf, failure_week: 32 })).toBe(32);
  });
});

describe('the forecast card', () => {
  it('draws years with few lab results hollow and faded, and says why', () => {
    const observed = forecastFigure(ML, {} as PlotTheme).data[2] as { marker: { symbol: string[]; opacity: number[] } };
    expect(observed.marker.symbol).toEqual(['circle-open', 'circle']);   // 2020 has 4 results, 2021 has 44
    expect(observed.marker.opacity).toEqual([0.5, 1]);
    render(<MlForecastCard ml={ML} />);
    expect(screen.getByText(/Hollow points are years with fewer than 30 lab/)).toBeInTheDocument();
  });

  it('offers only the genera with history for the drug', () => {
    const g = { ciprofloxacin: ['Escherichia', 'Salmonella'] };
    expect(forecastGenera(g, 'Ciprofloxacin')).toEqual(['Escherichia', 'Salmonella']);
    expect(forecastGenera(g, 'ampicillin')).toEqual([]);
    expect(forecastGenera(undefined, 'ciprofloxacin')).toEqual([]);
  });

  it('shows the forecast, its label and its error against the baselines', () => {
    render(<MlForecastCard ml={ML} />);
    expect(screen.getByText(ML.label)).toBeInTheDocument();
    expect(screen.getByText('54.5%')).toBeInTheDocument();
    expect(screen.getByText('Observed in 2021 (44 lab results)')).toBeInTheDocument();
    expect(screen.getByText('Forecast for 2023 (80%: 11.8 to 83.2)')).toBeInTheDocument();
    expect(errorSentence(ML.metrics)).toBe('On years it never saw, the model is off by 13.98 percentage points on average, '
      + 'against 14.33 for last year’s value, 16.75 for a straight-line trend, 17.25 for the average so far.');
    expect(document.getElementById('mlForecastChart')).not.toBeNull();
    expect(document.getElementById('genusFromGenome')).toBeNull();
  });

  it('says when the genus came from the genome', () => {
    render(<MlForecastCard ml={ML} source="genome" />);
    expect(document.getElementById('genusFromGenome')).toHaveTextContent('The uploaded genome was identified as Salmonella');
  });
});

/** The form, once the drug list has loaded. */
async function openForm() {
  const form = within(document.getElementById('trendPane')!);
  await form.findByRole('option', { name: 'Ciprofloxacin' });
  return form;
}

describe('Timeline page', () => {
  it('opens on the ML forecast, and shows the model and its error', async () => {
    backend();
    renderPage(<Timeline />, '/timeline');
    expect(screen.getByRole('tab', { name: /ML trend forecast/ })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: /What-if simulation/ })).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByText('Forecast a Resistance Trend')).toBeInTheDocument();
    expect(await screen.findByText('467')).toBeInTheDocument();
    expect(screen.getByText('534,996')).toBeInTheDocument();
    expect(document.getElementById('timelineModelCard')).toHaveTextContent(
      'off by 14.0 pp on average, against 14.3 pp for repeating last year\'s value');
  });

  it('sends the chosen organism and shows the forecast with downloads', async () => {
    const calls = backend();
    renderPage(<Timeline />, '/timeline');
    const form = await openForm();
    const go = form.getByRole('button', { name: /Forecast Resistance Trend/ });
    expect(go).toBeDisabled();
    fireEvent.change(form.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    await form.findByRole('option', { name: 'Salmonella' });
    fireEvent.change(form.getByLabelText('Organism (genus)'), { target: { value: 'Salmonella' } });
    fireEvent.change(form.getByLabelText('Years ahead'), { target: { value: '2' } });
    fireEvent.click(go);
    expect(await screen.findByText(/Resistance forecast:/)).toBeInTheDocument();
    const body = JSON.parse(String(calls.find(c => c.url.endsWith('/api/timeline/'))?.init?.body));
    expect(body).toEqual({ antibiotic: 'ciprofloxacin', genus: 'Salmonella', years_ahead: '2' });
    expect(screen.getByText('Download this result')).toBeInTheDocument();
    expect(document.querySelector('.export-bar')).not.toHaveTextContent(/Simulation/);
  });

  it('asks for a genome before sending anything, then sends it without a genus', async () => {
    const calls = backend({ 'timeline/': { body: { ml_forecast: ML, organism_source: 'genome' } } });
    renderPage(<Timeline />, '/timeline');
    const form = await openForm();
    fireEvent.change(form.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.click(form.getByRole('button', { name: /From a genome/ }));
    expect(form.queryByLabelText('Organism (genus)')).toBeNull();
    fireEvent.click(form.getByRole('button', { name: /Forecast Resistance Trend/ }));
    expect(screen.getByText('Upload a FASTA file or paste a sequence, or choose the organism instead.')).toBeVisible();
    expect(calls.some(c => c.url.endsWith('/timeline/'))).toBe(false);

    fireEvent.click(form.getByRole('button', { name: /Paste Sequence/ }));
    fireEvent.change(form.getByLabelText(/^FASTA Sequence|^Paste/), { target: { value: '>g\nACGT' } });
    fireEvent.click(form.getByRole('button', { name: /Forecast Resistance Trend/ }));
    expect(await screen.findByText(/The uploaded genome was identified as/)).toBeInTheDocument();
    const body = JSON.parse(String(calls.find(c => c.url.endsWith('/api/timeline/'))?.init?.body));
    expect(body).toEqual({ fasta_text: '>g\nACGT', antibiotic: 'ciprofloxacin', years_ahead: '5' });
  });

  it("shows the backend's refusal", async () => {
    backend({ 'timeline/': { status: 422, body: { error: 'The organism could not be identified from this genome' } } });
    renderPage(<Timeline />, '/timeline');
    const form = await openForm();
    fireEvent.change(form.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    await form.findByRole('option', { name: 'Salmonella' });
    fireEvent.change(form.getByLabelText('Organism (genus)'), { target: { value: 'Salmonella' } });
    fireEvent.click(form.getByRole('button', { name: /Forecast Resistance Trend/ }));
    expect(await screen.findByText(/could not be identified/)).toBeInTheDocument();
  });

  it('keeps the what-if simulation in its own tab, labelled, on its own endpoint', async () => {
    const calls = backend();
    renderPage(<Timeline />, '/timeline');
    fireEvent.click(screen.getByRole('tab', { name: /What-if simulation/ }));
    const sim = within(document.getElementById('simulationPane')!);
    expect(sim.getByText('Simulation, not a trained model.')).toBeInTheDocument();
    await sim.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(sim.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.click(sim.getByRole('button', { name: /Generate Timeline/ }));
    expect(screen.getByText('Upload a FASTA file or paste a sequence before generating a timeline.')).toBeVisible();
    fireEvent.change(sim.getByLabelText(/^Simulation Weeks/), { target: { value: '12' } });
    fireEvent.click(sim.getByRole('button', { name: 'Load Sample' }));
    fireEvent.click(sim.getByRole('button', { name: /Generate Timeline/ }));
    expect(await screen.findByText('Week-by-Week Resistance Evolution')).toBeInTheDocument();
    const body = JSON.parse(String(calls.find(c => c.url.endsWith('/timeline/simulate/'))?.init?.body));
    expect(body).toEqual({ fasta_text: SAMPLE_GENOME, antibiotic: 'ciprofloxacin', n_weeks: '12' });
    expect(screen.getByText(/Every download is labelled "Simulation, not a trained model"/)).toBeInTheDocument();
    expect(calls.some(c => c.url.endsWith('/api/timeline/'))).toBe(false);
  });
});
