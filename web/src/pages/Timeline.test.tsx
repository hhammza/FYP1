import { fireEvent, render, screen, within } from '@testing-library/react';
import Timeline from './Timeline';
import RlPanel, { firstFailedWeek, givenResistance, shortDrug, startResistance } from './timeline/RlPanel';
import MlForecastCard, { errorSentence } from './timeline/MlForecastCard';
import TimelineResult from './timeline/TimelineResult';
import { forecastGenera, SAMPLE_GENOME } from './timeline/TimelineForm';
import type { MlForecast, RlBlock, TimelineResult as Result } from './timeline/types';
import { jinjaTitle } from '../lib/metrics';
import { HEALTH, mockBackend, renderPage } from '../test-utils';
import { ToastProvider } from '../components/Toasts';

vi.mock('plotly.js-dist-min', () => ({ default: { react: vi.fn(), purge: vi.fn(), toImage: vi.fn(async () => '') } }));

afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); });

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

function backend(extra: Record<string, { status?: number; body: unknown }> = {}) {
  return mockBackend({
    'health/': { body: HEALTH },
    'antibiotics/': { body: { antibiotics: ['ciprofloxacin'] } },
    'timeline/': { body: { ...RESULT, antibiotic: 'ciprofloxacin' } },
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
    render(<ToastProvider><TimelineResult result={RESULT} inputs={{ antibiotic: RESULT.antibiotic, n_weeks: '2' }} /></ToastProvider>);
    expect(screen.getByText('Trimethoprim/sulfamethoxazole')).toBeInTheDocument();
    expect(screen.getByText(/Beta-Lactam \| 2-week simulation/)).toBeInTheDocument();
    expect(screen.getByText('Not reached')).toBeInTheDocument();
    expect(screen.getByText('12.0%')).toBeInTheDocument();
    expect(screen.getByText('12,345')).toBeInTheDocument();
    expect(screen.getByText(/Trimethoprim\/sulfamethoxazole was not among the drugs fitted/)).toBeInTheDocument();
    expect(screen.getByText(/±2\.9 points on 10 hospital series/)).toBeInTheDocument();
  });

  it('opens and closes the weekly table', () => {
    render(<ToastProvider><TimelineResult result={RESULT} inputs={{ antibiotic: 'x', n_weeks: '2' }} /></ToastProvider>);
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

const ML: MlForecast = {
  model_run: 'TL_timeline_ml', organism: 'Salmonella', antibiotic: 'ciprofloxacin',
  history: [{ year: 2020, resistant_pct: 100, n: 4 }, { year: 2021, resistant_pct: 54.5, n: 44 }],
  forecast: [{ year: 2022, resistant_pct: 50.5, lo: 25.2, hi: 75.7 }, { year: 2023, resistant_pct: 47.5, lo: 11.8, hi: 83.2 }],
  metrics: { model: { mae_pct: 13.98, ci: [11.84, 16.33] }, last_value: { mae_pct: 14.33, ci: [12.16, 16.73] },
             linear_trend: { mae_pct: 16.75, ci: [14.32, 19.3] }, historical_mean: { mae_pct: 17.25, ci: [15.07, 19.67] } },
  label: 'ML model trained on BV-BRC laboratory results',
};

describe('the ML forecast', () => {
  it('offers only the genera with history for the drug', () => {
    const g = { ciprofloxacin: ['Escherichia', 'Salmonella'] };
    expect(forecastGenera(g, 'Ciprofloxacin')).toEqual(['Escherichia', 'Salmonella']);
    expect(forecastGenera(g, 'ampicillin')).toEqual([]);
    expect(forecastGenera(undefined, 'ciprofloxacin')).toEqual([]);
  });

  it('shows the forecast, its label and its error against the baselines', () => {
    render(<MlForecastCard ml={ML} antibiotic="ciprofloxacin" genus="Salmonella" />);
    expect(screen.getByText(ML.label)).toBeInTheDocument();
    expect(screen.getByText('54.5%')).toBeInTheDocument();
    expect(screen.getByText('Observed in 2021 (44 lab results)')).toBeInTheDocument();
    expect(screen.getByText('Forecast for 2023 (80%: 11.8 to 83.2)')).toBeInTheDocument();
    expect(errorSentence(ML.metrics)).toBe('On years it never saw, the model is off by 13.98 percentage points on average, '
      + 'against 14.33 for last year’s value, 16.75 for a straight-line trend, 17.25 for the average so far.');
    expect(document.getElementById('mlForecastChart')).not.toBeNull();
  });

  it('says why there is none', () => {
    const { unmount } = render(<MlForecastCard ml={undefined} antibiotic="ampicillin" genus="Vibrio" />);
    expect(screen.getByText(/Vibrio has too little yearly lab history for ampicillin/)).toBeInTheDocument();
    unmount();
    render(<MlForecastCard ml={null} antibiotic="ampicillin" />);
    expect(screen.getByText(/Choose an organism above, or upload a complete genome/)).toBeInTheDocument();
  });

  it('puts the forecast first and labels the simulation as the what-if tool', () => {
    render(<ToastProvider><TimelineResult result={{ ...RESULT, ml_forecast: ML }} inputs={{ antibiotic: 'x', n_weeks: '2', genus: 'Salmonella' }} /></ToastProvider>);
    const card = document.getElementById('mlForecast')!, sim = document.getElementById('simulationHeading')!;
    expect(card.compareDocumentPosition(sim) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(sim).getByText('Simulation, not a trained model')).toBeInTheDocument();
  });
});

describe('Timeline page', () => {
  it('asks for a genome before sending anything', async () => {
    const calls = backend();
    renderPage(<Timeline />, '/timeline');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate Timeline/ }));
    expect(screen.getByText('Upload a FASTA file or paste a sequence before generating a timeline.')).toBeVisible();
    expect(calls.some(c => c.url.endsWith('/timeline/'))).toBe(false);
  });

  it('sends the weeks with a pasted genome and shows the simulation', async () => {
    const calls = backend();
    renderPage(<Timeline />, '/timeline');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.change(screen.getByLabelText(/^Simulation Weeks/), { target: { value: '12' } });
    expect(document.getElementById('weeksVal')).toHaveTextContent('12');
    fireEvent.click(screen.getByRole('button', { name: 'Load Sample' }));
    fireEvent.click(screen.getByRole('button', { name: /Generate Timeline/ }));
    expect(await screen.findByText('Week-by-Week Resistance Evolution')).toBeInTheDocument();
    const body = JSON.parse(String(calls.find(c => c.url.endsWith('/timeline/'))?.init?.body));
    expect(body).toEqual({ fasta_text: SAMPLE_GENOME, antibiotic: 'ciprofloxacin', n_weeks: '12' });   // no genus chosen
    expect(screen.getByText(/Every download is labelled "Simulation, not a trained model"/)).toBeInTheDocument();
    expect(screen.getByText(/No ML forecast for this request/)).toBeInTheDocument();
  });

  it('sends the organism chosen for the ML forecast', async () => {
    const calls = backend();
    renderPage(<Timeline />, '/timeline');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    await screen.findByRole('option', { name: 'Salmonella' });
    expect(screen.getByText('2 genera have yearly lab history for ciprofloxacin')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/^Organism for the ML forecast/), { target: { value: 'Salmonella' } });
    fireEvent.click(screen.getByRole('button', { name: 'Load Sample' }));
    fireEvent.click(screen.getByRole('button', { name: /Generate Timeline/ }));
    await screen.findByText('Week-by-Week Resistance Evolution');
    const body = JSON.parse(String(calls.find(c => c.url.endsWith('/timeline/'))?.init?.body));
    expect(body.genus).toBe('Salmonella');
  });

  it("shows the backend's refusal", async () => {
    backend({ 'timeline/': { status: 400, body: { error: 'n_weeks must be a whole number from 2 to 24, not "99".' } } });
    renderPage(<Timeline />, '/timeline');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Load Sample' }));
    fireEvent.click(screen.getByRole('button', { name: /Generate Timeline/ }));
    expect(await screen.findByText(/n_weeks must be a whole number/)).toBeInTheDocument();
  });
});
