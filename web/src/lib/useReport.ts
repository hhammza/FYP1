/* /api/models/ for the report pages (/models, /compare). */
import { useEffect, useState } from 'react';
import { apiGet, errorText } from './api';
import type { ModelReport } from './report';

export type ReportState = { state: 'loading' } | { state: 'ready'; report: ModelReport } | { state: 'failed'; error: string };

export function useModelReport(): ReportState {
  const [value, setValue] = useState<ReportState>({ state: 'loading' });
  useEffect(() => {
    let alive = true;
    apiGet<ModelReport & { error?: string }>('models/')
      .then(report => { if (alive) setValue({ state: 'ready', report }); })
      .catch(e => { if (alive) setValue({ state: 'failed', error: errorText(e) }); });
    return () => { alive = false; };
  }, []);
  return value;
}
