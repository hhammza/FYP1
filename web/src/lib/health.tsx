/* The backend's /api/health/ response, shared by every page.

   Every page shows model numbers (the footer at least), so it is fetched once
   for the whole site. A failed call is retried after RETRY_MS: a backend that is
   still starting up should not leave the forms on fallback values. */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { apiGet } from './api';
import { summarizeMetrics, type ModelSummary } from './metrics';
import type { Health } from './types';

const RETRY_MS = 5000;

export interface HealthState {
  /** undefined while the first call runs, null when the backend did not answer */
  health: Health | null | undefined;
  metrics: { lgbm: ModelSummary; kmer: ModelSummary };
  refresh: () => void;
}

const HealthContext = createContext<HealthState | null>(null);

export function HealthProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<Health | null | undefined>(undefined);
  const [tick, setTick] = useState(0);
  const refresh = useCallback(() => setTick(t => t + 1), []);

  useEffect(() => {
    let alive = true;
    let retry: ReturnType<typeof setTimeout> | undefined;
    apiGet<Health>('health/', { timeoutS: 5 })
      .then(h => { if (alive) setHealth(h); })
      .catch(() => {
        if (!alive) return;
        setHealth(prev => (prev ? prev : null));
        retry = setTimeout(() => setTick(t => t + 1), RETRY_MS);
      });
    return () => { alive = false; clearTimeout(retry); };
  }, [tick]);

  const value = useMemo<HealthState>(() => ({
    health,
    metrics: {
      lgbm: summarizeMetrics(health?.models?.lgbm_forecasting),
      kmer: summarizeMetrics(health?.models?.kmer_resistance),
    },
    refresh,
  }), [health, refresh]);

  return <HealthContext.Provider value={value}>{children}</HealthContext.Provider>;
}

export function useHealth(): HealthState {
  const ctx = useContext(HealthContext);
  if (!ctx) throw new Error('useHealth outside <HealthProvider>');
  return ctx;
}

/** `m.lgbm` and `m.kmer`: what the templates called `metrics`. */
export const useMetrics = () => useHealth().metrics;
