/* The lists the forms offer: each model's antibiotics and the forecaster's
   organisms, from the backend. Cached for the browser tab, as dropdowns.js
   did, so moving between pages does not ask again. */
import { useEffect, useState } from 'react';
import { apiGet } from './api';

export interface OrganismSpecies { name: string; label: string; taxon_ids: number[] }
export interface OrganismGenus {
  genus: string;
  species: OrganismSpecies[];
  other_taxon_ids: { id: number; label: string }[];
}
export interface Vocabulary {
  lgbm: { antibiotics?: string[]; organisms?: OrganismGenus[]; [k: string]: unknown } | null;
  kmer: { antibiotics?: string[] } | null;
}

function cached<T>(key: string, load: () => Promise<T>): Promise<T> {
  try {
    const hit = sessionStorage.getItem('amr_' + key);
    if (hit) return Promise.resolve(JSON.parse(hit) as T);
  } catch { /* storage blocked */ }
  return load().then(data => {
    try { sessionStorage.setItem('amr_' + key, JSON.stringify(data)); } catch { /* full or blocked */ }
    return data;
  });
}

export type Loaded<T> = { state: 'loading' } | { state: 'ready'; data: T } | { state: 'failed' };

function useLoad<T>(key: string, load: () => Promise<T>, keep: (d: T) => boolean): Loaded<T> {
  const [value, setValue] = useState<Loaded<T>>({ state: 'loading' });
  useEffect(() => {
    let alive = true;
    // a list that came back empty (models not loaded yet) is not kept
    cached(key, () => load().then(d => { if (!keep(d)) throw new Error('empty'); return d; }))
      .then(data => { if (alive) setValue({ state: 'ready', data }); })
      .catch(() => { if (alive) setValue({ state: 'failed' }); });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return value;
}

/** The antibiotics a model was trained on, each under its canonical name. */
export function useAntibiotics(model: 'lgbm' | 'kmer'): Loaded<string[]> {
  return useLoad(`antibiotics_${model}`,
    () => apiGet<{ antibiotics: string[] }>(`antibiotics/?model=${model}`).then(d => d.antibiotics),
    d => d.length > 0);
}

export function useVocabulary(): Loaded<Vocabulary> {
  return useLoad('vocabulary', () => apiGet<Vocabulary>('vocabulary/'), d => !!(d.lgbm || d.kmer));
}

/** 'ciprofloxacin' -> 'Ciprofloxacin', as the Flask dropdowns showed names. */
export const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export const MIC_SIGNS = [
  { value: '<=', label: '≤  (less than or equal)' },
  { value: '<', label: '<  (less than)' },
  { value: '=', label: '=  (equal)' },
  { value: '>', label: '>  (greater than)' },
  { value: '>=', label: '≥  (greater than or equal)' },
];
