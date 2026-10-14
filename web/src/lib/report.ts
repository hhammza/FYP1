/* Shared chart helpers for the report pages, /models and /compare
   (report-charts.js in the Flask frontend), and the /api/models/ types. */
import type { Layout } from 'plotly.js-dist-min';
import type { PlotTheme } from '../components/Plot';

/** Series colours from the CSS tokens, so light and dark stay in one place. */
export function palette() {
  const css = getComputedStyle(document.documentElement);
  const v = (name: string) => css.getPropertyValue(name).trim();
  return {
    c1: v('--viz-1'), c2: v('--viz-2'), c3: v('--viz-3'),
    c4: v('--viz-4'), c5: v('--viz-5'), other: v('--viz-other'),
    text: v('--text-1'), text2: v('--text-2'), card: v('--bg-card'),
    danger: v('--danger'),
    dark: document.documentElement.getAttribute('data-theme') === 'dark',
  };
}
export type Palette = ReturnType<typeof palette>;

type Obj = Record<string, unknown>;

/** A theme-aware layout; xaxis/yaxis in `extra` merge into the defaults. */
export function reportLayout(t: PlotTheme, extra: Obj = {}): Partial<Layout> {
  const p = palette();
  const axis = {
    tickfont: { color: t.tickColor, size: 11 },
    gridcolor: t.gridColor, linecolor: t.lineColor, zeroline: false, automargin: true,
    title: { font: { color: t.tickColor, size: 12 } },
  };
  const base: Obj = {
    paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor,
    font: { family: t.fontFamily, color: p.text2 },
    margin: { t: 10, r: 16, b: 48, l: 56 },
    hoverlabel: { bgcolor: p.card, bordercolor: t.lineColor, font: { color: p.text, family: t.fontFamily } },
    legend: { orientation: 'h', y: -0.18, font: { color: p.text2, size: 11 } },
    xaxis: structuredClone(axis),
    yaxis: structuredClone(axis),
  };
  for (const [key, value] of Object.entries(extra)) {
    if (key === 'xaxis' || key === 'yaxis') {
      const ax = Object.assign(base[key] as Obj, value as Obj);
      if ((value as Obj).title) ax.title = { font: axis.title.font, ...((value as Obj).title as Obj) };
    } else {
      base[key] = value;
    }
  }
  /* On phones a legend below the plot collides with the (angled) axis
     labels, so any chart's bottom legend moves above the plot instead. */
  const legend = base.legend as Obj | undefined;
  if (window.innerWidth < 576 && legend && typeof legend.y === 'number' && legend.y < 0) {
    base.legend = { ...legend, y: 1.02, yanchor: 'bottom' };
  }
  return base as Partial<Layout>;
}

export const fmt = (x: number) => x.toFixed(3);
export const pct = (x: number) => (100 * x).toFixed(1) + '%';
/** Plotly can undersize horizontal legend entries by a few pixels; pad so text is never clipped. */
export const legendName = (name: string) => name + '   ';   // non-breaking: Plotly keeps them

// ── /api/models/ (experiments/export_report.py; progress/formats/README.md §6) ──

export interface Run {
  id: string;
  run_id?: string;
  clean_version?: string;
  description?: string;
  group?: string;
  split?: string;
  model?: string;
  rows: number;
  test_rows?: number;
  auc_roc: number;
  auc_ci: [number, number];
  auc_pr: number;
  f1: number;
  very_major_error: number;
  major_error: number;
  threshold: number;
}

export interface ShippedResult {
  subset: string;
  rows: number;
  auc_roc: number;
  auc_ci: [number, number];
  very_major_error: number;
  major_error: number;
  roc?: { fpr: number[]; tpr: number[] };
}

export interface ShippedModel {
  name: string;
  short_name?: string;
  page: string;
  run_id?: string;
  trees: number;
  known_antibiotics: number;
  train_rows: number;
  train_genomes: number;
  claimed_auc: string | number;
  split: string;
  threshold?: number;
  results: ShippedResult[];
  head_to_head_a2?: { rows: number; shipped_auc: number; a2_auc: number };
  known_genera?: string[];
  within_antibiotic_auc?: number;
  served_fallback_rate?: number;
  [k: string]: unknown;
}

export interface GenomeRun {
  id: string;
  description?: string;
  clean_version?: string;
  label_version?: string;
  model?: string;
  features?: string;
  split?: string;
  auc_roc_lab?: number | null;
  auc_roc_lab_ci?: [number, number] | null;
  n_lab?: number | null;
}

export interface Strategy {
  train_genomes: number;
  test_genomes: number;
  shared_genomes: number;
  test_rows_from_seen_genomes: number;
  train_prevalence: number;
  test_prevalence: number;
  [k: string]: unknown;
}

export interface ModelReport {
  generated_at: string;
  best_run: string;
  clean_version?: string;
  runs: Run[];
  split: {
    strategies: { grouped: Strategy; random: Strategy };
    total_rows: number;
    total_genomes: number;
    rows_per_genome: number;
    fit_rows: number;
    validation_rows: number;
    test_rows: number;
    encoding_folds: number;
    validation_folds: number;
  };
  best: {
    id: string;
    model_info: { kind: string; n_trees: number };
    features: string[];
    confusion: { tn: number; fp: number; fn: number; tp: number };
    test: { threshold: number; major_error: number; very_major_error: number; sensitivity: number; specificity: number };
    per_antibiotic_best: { antibiotic: string; auc_roc: number; rows: number; prevalence: number }[];
    per_antibiotic_worst: { antibiotic: string; auc_roc: number; rows: number; prevalence: number }[];
    per_antibiotic_count: number;
  };
  roc: Record<string, { fpr: number[]; tpr: number[] }>;
  shipped?: { lightgbm: ShippedModel; kmer: ShippedModel } | null;
  genome_runs?: GenomeRun[] | null;
  insights?: { icon: string; title: string; text: string; evidence: string }[];
  [k: string]: unknown;
}

/** Section 5's runs, as the template chose them: the newest label version
    (v6 and v7 share rows and labels for genome runs), a lab score present,
    and a run re-done on v7 kept only as its v7 copy. */
export function shownGenomeRuns(all: GenomeRun[] | null | undefined) {
  const runs = (all || []).map(r => ({ ...r, label_version: r.label_version ?? r.clean_version }));
  const versions = runs.map(r => r.label_version).filter((v): v is string => !!v).sort();
  const version = versions.length ? versions[versions.length - 1] : undefined;
  const scored = runs.filter(r => r.label_version === version && typeof r.auc_roc_lab === 'number');
  const v7 = new Set(scored.filter(r => r.clean_version === 'v7').map(r => r.id.replace('_v7', '')));
  const kept = scored.filter(r => r.clean_version === 'v7' || !v7.has(r.id.replace('_v6', '')));
  return { runs: kept, version, hasV7: kept.some(r => r.clean_version === 'v7') };
}
