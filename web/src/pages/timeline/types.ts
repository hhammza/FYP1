/* /api/timeline/ (the ML forecast, progress/formats/README.md §8) and
   /api/timeline/simulate/ (the what-if simulation, §4) responses. */

/** The timeline ML model's block: observed yearly resistance and its forecast. */
export interface MlForecast {
  model_run?: string;
  organism: string;
  antibiotic: string;
  history: { year: number; resistant_pct: number; n: number }[];
  forecast: { year: number; resistant_pct: number; lo: number; hi: number }[];
  metrics?: Record<string, { mae_pct: number; ci: [number, number] }>;
  label: string;
}

export interface TimelineResult {
  ml_forecast: MlForecast;
  /** 'genome' when the genus was identified from an uploaded genome */
  organism_source?: 'chosen' | 'genome';
}

/* ── the what-if simulation (§4) ── */

export interface Week {
  week: number;
  susceptible_fraction: number;
  intermediate_fraction: number;
  resistant_fraction: number;
  cumulative_mutations: number;
  mic_fold_change: number;
  treatment_effective: boolean;
}

export interface RlPolicy {
  name: string;
  label: string;
  /** the drug given each week, weeks 1..n */
  policy: string[];
  /** each drug's resistant %, weeks 0..n (index 0 = the start) */
  resistant_fraction: Record<string, number[]>;
  failure_week: number | null;
  total_reward?: number | null;
  effective_weeks?: number | null;
  mean_burden?: number | null;
}

export interface RlBlock {
  drugs: string[];
  n_weeks?: number;
  agent?: string | null;
  best?: string;
  policies: RlPolicy[];
}

export interface SimulationResult {
  antibiotic: string;
  antibiotic_class?: string;
  sequence_length: number;
  gc_content: number;
  n_weeks: number;
  failure_week: number | null;
  final_resistant_percent: number;
  model_used?: string;
  summary?: string;
  seed?: number;
  timeline: Week[];
  mutation_hotspots?: { position: number; original_nucleotide: string; mutated_nucleotide: string; mutation_type: string }[];
  resistance_genes?: { gene: string; activation_week: number; resistance_contribution: number }[];
  calibration?: { curves: number; rmse: number; surveillance_curves: number; drugs: string[] } | null;
  rl?: RlBlock | null;
  [k: string]: unknown;
}

export interface SimulationInputs {
  antibiotic: string;
  n_weeks: string;
}
