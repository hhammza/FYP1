/* The dashboard's filters, kept in the URL so any view can be shared as a link
   (/explore/heatmap?gram=negative&subfamily=Carbapenems&country=PAK). The view is the path. */
import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router';

export const LIST_KEYS = ['gram', 'genus', 'species', 'family', 'subfamily', 'antibiotic', 'chemical_group',
  'country', 'infection_type', 'disease'] as const;
export type ListKey = typeof LIST_KEYS[number];

export interface Filters {
  lists: Record<ListKey, string[]>;
  year_from: string; year_to: string; include_intermediate: boolean; min_n: string;
}

const split = (v: string | null) => (v ? v.split(',').filter(Boolean) : []);

export function readFilters(params: URLSearchParams): Filters {
  const lists = Object.fromEntries(LIST_KEYS.map(k => [k, split(params.get(k))])) as Record<ListKey, string[]>;
  return {
    lists,
    year_from: params.get('year_from') || '', year_to: params.get('year_to') || '',
    include_intermediate: params.get('include_intermediate') === '1', min_n: params.get('min_n') || '',
  };
}

/** The filters as an API query string (only the filters, not the view or panel). */
export function filterQuery(f: Filters, extra: Record<string, string> = {}): string {
  const q = new URLSearchParams();
  for (const k of LIST_KEYS) if (f.lists[k].length) q.set(k, f.lists[k].join(','));
  if (f.year_from) q.set('year_from', f.year_from);
  if (f.year_to) q.set('year_to', f.year_to);
  if (f.include_intermediate) q.set('include_intermediate', '1');
  if (f.min_n) q.set('min_n', f.min_n);
  for (const [k, v] of Object.entries(extra)) if (v) q.set(k, v);
  const s = q.toString();
  return s ? `?${s}` : '';
}

/** Filters, group and open drug from the URL, and setters that write them back. */
export function useExploreFilters() {
  const [params, setParams] = useSearchParams();
  const filters = useMemo(() => readFilters(params), [params]);
  const update = useCallback((changes: Record<string, string | string[] | boolean | null>) => {
    setParams(prev => {
      const next = new URLSearchParams(prev);
      for (const [k, v] of Object.entries(changes)) {
        const value = Array.isArray(v) ? v.join(',') : v === true ? '1' : v === false || v === null ? '' : v;
        if (value) next.set(k, value); else next.delete(k);
      }
      return next;
    }, { replace: true });
  }, [setParams]);
  const clear = useCallback(() => {
    setParams(prev => {
      const next = new URLSearchParams();
      for (const k of ['group', 'drug']) { const v = prev.get(k); if (v) next.set(k, v); }
      return next;
    }, { replace: true });
  }, [setParams]);
  return {
    filters, update, clear,
    group: params.get('group') || '',
    drug: params.get('drug') || '',
    split: params.get('split') || '',
  };
}

export const activeCount = (f: Filters) =>
  LIST_KEYS.reduce((n, k) => n + (f.lists[k].length ? 1 : 0), 0)
  + (f.year_from || f.year_to ? 1 : 0) + (f.include_intermediate ? 1 : 0);
