/* Display strings for one model, from the metrics.json that /api/health/
   passes through (format: progress/formats/README.md). Port of
   summarize_metrics() in frontend/app.py.

   Nothing here is typed in by hand: when the file is missing every value
   reads "not measured" instead of falling back to an old figure. */
import type { ModelStatus } from './types';

export interface ModelSummary {
  measured: boolean;
  auc: string;
  auc_ci: string;
  recall: string;
  very_major_error: string;
  major_error: string;
  threshold: number | undefined;
  threshold_rule: string;
  run_id: string;
  algorithm: string;
  split: string;
  train_rows: string;
  train_rows_short: string;
  train_genomes: string;
  antibiotics: number | string;
  genera: number | string;
  genomes_total: string;
}

const isNum = (x: unknown): x is number => typeof x === 'number' && Number.isFinite(x);

export const pct = (x: unknown): string => (isNum(x) ? `${pyFixed(x * 100, 1)}%` : 'not measured');

/** 1217307 -> '1.2M', 6002 -> '6.0K', for tiles too narrow for the full count. */
export function compact(n: number | undefined): string {
  if (!n) return 'n/a';
  for (const [size, unit] of [[1_000_000, 'M'], [1_000, 'K']] as const) {
    if (n >= size) return `${pyFixed(n / size, 1)}${unit}`;
  }
  return String(n);
}

/** 1217307 -> '1,217,307', as Python's format with a comma. */
export const thousands = (n: number): string => n.toLocaleString('en-US');

export function summarizeMetrics(status: ModelStatus | undefined | null): ModelSummary {
  const s = status || {};
  const m = s.metrics || {};
  const test = m.test || {};
  const data = m.data || {};
  const auc = test.auc_roc;
  const ci = test.auc_roc_ci || [];
  const out: ModelSummary = {
    measured: isNum(auc),
    auc: 'not measured',
    auc_ci: 'not measured',
    recall: pct(test.recall),
    very_major_error: pct(test.very_major_error),
    major_error: pct(test.major_error),
    threshold: s.default_threshold ?? m.threshold,
    threshold_rule: m.threshold_rule || '',
    run_id: m.run_id || s.run_id || '',
    algorithm: m.algorithm || '',
    split: m.evaluation?.split || '',
    train_rows: data.train_rows ? thousands(data.train_rows) : 'not measured',
    train_rows_short: compact(data.train_rows),
    train_genomes: data.train_genomes ? thousands(data.train_genomes) : 'not measured',
    antibiotics: data.antibiotics || 'n/a',
    genera: Array.isArray(data.genera) ? data.genera.length : (data.genera || 'n/a'),
    // every genome the model was trained or tested on (the k-mer model: all genomes with a FASTA)
    genomes_total: data.train_genomes && data.test_genomes
      ? thousands(data.train_genomes + data.test_genomes) : 'n/a',
  };
  if (isNum(auc)) {
    out.auc = pyFixed(auc, 3);
    out.auc_ci = ci.length === 2 ? `${out.auc} [${pyFixed(ci[0], 3)}–${pyFixed(ci[1], 3)}]` : out.auc;
  }
  return out;
}

/** A float as Python prints it: 100.0 stays "100.0" (JSON has dropped the ".0"). */
export const pyFloat = (n: number): string => (Number.isInteger(n) ? n.toFixed(1) : String(n));

/** Jinja's title filter: each word capitalised, words split at spaces,
    hyphens and brackets (so 'beta-lactam' -> 'Beta-Lactam', but a drug pair
    'a/b' -> 'A/b'). */
export const jinjaTitle = (s: string): string =>
  s.split(/([-\s({[<]+)/).map(w => (w ? w.charAt(0).toUpperCase() + w.slice(1).toLowerCase() : w)).join('');

/** x with d decimals, rounded as Python's format does: an exact tie goes to
    the even digit (23.25 -> '23.2'), where toFixed would round it up ('23.3').
    For every number the Flask templates formatted. */
export function pyFixed(x: number, d: number): string {
  if (!Number.isFinite(x)) return String(x);
  const exact = Math.abs(x).toFixed(Math.min(100, d + 30));      // the double's own decimal digits
  const dot = exact.indexOf('.');
  const rest = exact.slice(dot + 1 + d);
  if (!/^50*$/.test(rest)) return x.toFixed(d);                    // not a tie: toFixed agrees with Python
  // a tie: keep the digits if the last is even, else add one to the last digit
  let digits = exact.slice(0, dot + 1 + d).replace('.', '');
  if (Number(digits.slice(-1)) % 2 === 1) {
    const up = (BigInt(digits) + 1n).toString();
    digits = up.padStart(digits.length, '0');
  }
  const int = digits.slice(0, digits.length - d) || '0';
  const out = d ? `${int}.${digits.slice(digits.length - d)}` : int;
  return (x < 0 && /[1-9]/.test(out) ? '-' : '') + out;
}
