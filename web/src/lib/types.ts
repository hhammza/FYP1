/* Shapes of the backend's responses (progress/formats/README.md). Only the
   fields the pages read are typed; everything else passes through. */

export interface TestMetrics {
  auc_roc?: number;
  auc_roc_ci?: number[];
  recall?: number;
  very_major_error?: number;
  major_error?: number;
  [k: string]: unknown;
}

export interface MetricsFile {
  test?: TestMetrics;
  data?: {
    train_rows?: number;
    train_genomes?: number;
    test_genomes?: number;
    antibiotics?: number | string;
    genera?: string[] | number;
    [k: string]: unknown;
  };
  threshold?: number;
  threshold_rule?: string;
  run_id?: string;
  algorithm?: string;
  evaluation?: { split?: string; [k: string]: unknown };
  [k: string]: unknown;
}

export interface ModelStatus {
  trained?: boolean;
  default_threshold?: number;
  run_id?: string;
  metrics?: MetricsFile;
  searches_genes?: boolean;
  [k: string]: unknown;
}

export interface Health {
  status?: string;
  models?: {
    lgbm_forecasting?: ModelStatus;
    kmer_resistance?: ModelStatus;
    [k: string]: ModelStatus | undefined;
  };
  [k: string]: unknown;
}
