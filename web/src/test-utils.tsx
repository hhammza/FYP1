/* Rendering a page as the app does (router, health, toasts) with the
   backend's answers replaced by fixed ones. */
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import type { ReactElement } from 'react';
import { HealthProvider } from './lib/health';
import { ToastProvider } from './components/Toasts';

type Answer = { status?: number; body: unknown } | 'down';

/** fetch() answering each path under /api/ from `routes` ('down' = no backend). */
export function mockBackend(routes: Record<string, Answer>) {
  const calls: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    calls.push({ url, init });
    const path = url.replace(/^\/api\//, '').split('?')[0];
    const answer = routes[path];
    if (answer === undefined) return new Response(JSON.stringify({ error: `no mock for ${path}` }), { status: 404 });
    if (answer === 'down') throw new TypeError('Failed to fetch');
    return new Response(JSON.stringify(answer.body), { status: answer.status ?? 200 });
  }));
  return calls;
}

export function renderPage(ui: ReactElement, path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <HealthProvider>
        <ToastProvider>{ui}</ToastProvider>
      </HealthProvider>
    </MemoryRouter>,
  );
}

export const HEALTH = {
  status: 'ok',
  models: {
    lgbm_forecasting: {
      trained: true,
      default_threshold: 0.15,
      metrics: { test: { auc_roc: 0.774 }, data: { train_rows: 6271378, antibiotics: 126 } },
    },
    kmer_resistance: {
      trained: true,
      default_threshold: 0.43,
      metrics: { test: { auc_roc: 0.935 }, data: { train_rows: 6002, train_genomes: 20000, test_genomes: 4285 } },
    },
  },
};
