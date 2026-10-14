import { screen } from '@testing-library/react';
import About from './About';
import Datasets from './Datasets';
import Library from './Library';
import { HEALTH, mockBackend, renderPage } from '../test-utils';

afterEach(() => vi.unstubAllGlobals());

describe('static pages', () => {
  it('About shows the k-mer threshold from /api/health/', async () => {
    mockBackend({ 'health/': { body: HEALTH } });
    renderPage(<About />);
    expect(await screen.findByText('0.43 (training default)')).toBeInTheDocument();
    expect(document.title).toBe('About the AMR Prediction System | BioAnalytics FYP');
  });

  it('About says "not measured" when the backend is down', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockBackend({ 'health/': 'down' });
    renderPage(<About />);
    expect(await screen.findByText('not measured (training default)')).toBeInTheDocument();
    vi.useRealTimers();
  });

  it('Datasets shows both models’ thresholds', async () => {
    mockBackend({ 'health/': { body: HEALTH } });
    renderPage(<Datasets />);
    expect(await screen.findByText(/Default 0\.15 \(LightGBM\), 0\.43 \(K-mer\)/)).toBeInTheDocument();
  });

  it('Library shows the package version from amrpredict-lib/pyproject.toml', () => {
    mockBackend({ 'health/': { body: HEALTH } });
    renderPage(<Library />);
    expect(screen.getByText(`v${__LIB_VERSION__}`)).toBeInTheDocument();
    expect(__LIB_VERSION__).toMatch(/^\d+\.\d+\.\d+/);
  });

  it('Library keeps the line breaks of its code samples', () => {
    mockBackend({ 'health/': { body: HEALTH } });
    renderPage(<Library />);
    const sample = screen.getByText(/r = amrpredict\.forecast\(/);
    expect(sample.textContent).toContain("r = amrpredict.forecast(\n    'ciprofloxacin',");
    expect(screen.getAllByRole('button', { name: /Copy/ }).length).toBeGreaterThanOrEqual(6);
  });
});
