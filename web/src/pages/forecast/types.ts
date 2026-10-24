/* /api/forecast/, /api/forecast/batch/ and /api/genome/<id>/ responses
   (backend/api/views.py, genome_lookup.py; progress/formats/README.md). */

export interface EvidenceInput {
  field: string;
  value: string | number | null;
  state: 'used' | 'normalized' | 'unrecognized' | 'missing' | string;
  detail: string;
}

export interface ForecastResult {
  antibiotic: string;
  prediction: 'Resistant' | 'Susceptible' | string;
  probability: number;
  confidence: number;
  threshold: number;
  drug_class?: string;
  model_used?: string;
  model_run?: string;
  calibrated?: boolean;
  related_antibiotics?: string[];
  comparison_chart?: { antibiotic: string; resistance_probability: number }[];
  evidence?: {
    level: string;
    label: string;
    summary: string;
    used_count: number;
    total_count: number;
    inputs: EvidenceInput[];
  };
  [k: string]: unknown;
}

export interface BatchRow {
  row: number;
  antibiotic?: string;
  genus?: string;
  species?: string;
  taxon_id?: string | number;
  mic_value?: string | number;
  mic_sign?: string;
  prediction?: string;
  probability?: number;
  error?: string;
}

export interface BatchResult {
  rows: BatchRow[];
  summary: {
    rows: number;
    predicted: number;
    errors: number;
    resistant: number;
    susceptible: number;
    by_antibiotic: { antibiotic: string; n: number; resistant: number }[];
  };
  threshold: number;
  model_run?: string;
  calibrated?: boolean;
}

export interface LabResult {
  antibiotic: string;
  phenotype?: string;
  sign?: string;
  value?: string;
  unit?: string;
  is_mic?: boolean;
  method?: string;
}

export interface GenomeLookup {
  error?: string;
  genome_id: string;
  taxon_id: number;
  organism?: { name?: string; genus?: string; species?: string; taxon_id?: number | string };
  lab_results?: LabResult[];
  lab_for_antibiotic?: LabResult[];
  models?: { forecast?: { role?: 'train' | 'test' | null } | null; [k: string]: unknown };
  genes_url: string;
}

/** What the form sent, kept for the downloads (the Flask page's form_data). */
export interface ForecastInputs {
  antibiotic: string;
  genus: string;
  species: string;
  taxon_id: string;
  mic_value: string;
  mic_sign: string;
  threshold: string;
  genome_id: string;
}
