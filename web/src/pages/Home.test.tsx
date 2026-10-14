import { screen } from '@testing-library/react';
import Home from './Home';
import { HEALTH, mockBackend, renderPage } from '../test-utils';

afterEach(() => vi.unstubAllGlobals());

describe('Home', () => {
  it('shows the numbers from /api/health/ and both models as trained', async () => {
    mockBackend({ 'health/': { body: HEALTH } });
    renderPage(<Home />);
    expect(await screen.findAllByText('Trained')).toHaveLength(2);
    expect(screen.getByText('LightGBM AUC 0.774', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('Genome k-mers AUC 0.935', { exact: false })).toBeInTheDocument();
    expect(document.title).toBe('Dashboard | BioAnalytics FYP');
  });

  it('marks both models offline when the backend does not answer', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockBackend({ 'health/': 'down' });
    renderPage(<Home />);
    expect(await screen.findAllByText('Offline')).toHaveLength(2);
    expect(screen.getAllByText('LightGBM AUC not measured', { exact: false }).length).toBeGreaterThan(0);
    vi.useRealTimers();
  });

  it('says "Heuristic" for a model that is loaded but not trained', async () => {
    mockBackend({ 'health/': { body: { models: { lgbm_forecasting: { trained: false }, kmer_resistance: HEALTH.models.kmer_resistance } } } });
    renderPage(<Home />);
    expect(await screen.findByText('Heuristic')).toBeInTheDocument();
    expect(screen.getByText('Trained')).toBeInTheDocument();
  });

  it('links to the tool pages inside the app', async () => {
    mockBackend({ 'health/': { body: HEALTH } });
    renderPage(<Home />);
    await screen.findAllByText('Trained');
    expect(screen.getByText('Start Predicting').closest('a')).toHaveAttribute('href', '/forecast');
    expect(screen.getByText('Run Prediction').closest('a')).toHaveAttribute('href', '/predict');
  });
});
