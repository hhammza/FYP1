import { fireEvent, render, screen, within } from '@testing-library/react';
import Timeline from './Timeline';
import RlPanel, { givenResistance, shortDrug } from './timeline/RlPanel';
import TimelineResult from './timeline/TimelineResult';
import { SAMPLE_GENOME } from './timeline/TimelineForm';
import type { RlBlock, TimelineResult as Result } from './timeline/types';
import { jinjaTitle } from '../lib/metrics';
import { HEALTH, mockBackend, renderPage } from '../test-utils';
import { ToastProvider } from '../components/Toasts';

vi.mock('plotly.js-dist-min', () => ({ default: { react: vi.fn(), purge: vi.fn(), toImage: vi.fn(async () => '') } }));

afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); });

const RL: RlBlock = {
  drugs: ['ciprofloxacin', 'ampicillin'], n_weeks: 3, agent: 'PPO (stable-baselines3)', best: 'rl',
  policies: [
    { name: 'fixed', label: 'Same drug every week', policy: ['ciprofloxacin', 'ciprofloxacin', 'ciprofloxacin'],
      resistant_fraction: { ciprofloxacin: [1, 20, 45, 70], ampicillin: [1, 1, 1, 1] },
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
    expect(chips[2]).toHaveClass('rl-chip-failed');
    expect(chips[2]).toHaveAttribute('title', 'Week 3: ciprofloxacin, 70.0% resistant');
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
    expect(body).toEqual({ fasta_text: SAMPLE_GENOME, antibiotic: 'ciprofloxacin', n_weeks: '12' });
    expect(screen.getByText(/Every download is labelled "Simulation, not a trained model"/)).toBeInTheDocument();
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
