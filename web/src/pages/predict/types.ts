/* /api/predict/ response (progress/formats/README.md §2). */

export interface Gene {
  gene: string;
  name?: string;
  type?: 'gene' | 'point_mutation' | string;
  drug_class?: string;
  subclass?: string;
  /** linked to the chosen drug's class; absent when the model does not score it */
  relevant?: boolean;
}

export interface PredictResult {
  antibiotic: string;
  prediction: 'Resistant' | 'Susceptible' | string;
  probability: number;
  confidence: number;
  threshold?: number;
  antibiotic_known?: boolean;
  sequence_length: number;
  gc_content?: number | null;
  top_kmers?: { kmer: string; frequency: number }[];
  model_used?: string;
  model_run?: string;
  /** absent: the model does not search for genes; [] searched, none found */
  genes_found?: Gene[] | null;
  species_detected?: { species?: string; genus?: string; [k: string]: unknown } | null;
  /** the gene search failed, so the k-mer model answered */
  warning?: string;
  [k: string]: unknown;
}

export interface PredictInputs {
  antibiotic: string;
  threshold: string;
}
