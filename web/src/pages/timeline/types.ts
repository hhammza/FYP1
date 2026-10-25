/* /api/timeline/ response (progress/formats/README.md §4). */

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

export interface TimelineResult {
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
  ml_forecast?: MlForecast | null;
  [k: string]: unknown;
}

/** The timeline ML model's block (format §8): observed yearly resistance and
    its forecast, absent when the organism and drug have too little history. */
export interface MlForecast {
  model_run?: string;
  organism: string;
  antibiotic: string;
  history: { year: number; resistant_pct: number; n: number }[];
  forecast: { year: number; resistant_pct: number; lo: number; hi: number }[];
  metrics?: Record<string, { mae_pct: number; ci: [number, number] }>;
  label: string;
}

export interface TimelineInputs {
  antibiotic: string;
  n_weeks: string;
  /** the organism for the ML forecast; '' = identify it from the genome */
  genus?: string;
}
