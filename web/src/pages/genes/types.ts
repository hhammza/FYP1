/* /api/genes/ and /api/genes/<id>/ (experiments/genome/features/export_gene_report.py). */

export interface LabPair {
  gene: string;
  gene_class?: string;
  gene_subclass?: string;
  antibiotic: string;
  carriers: number;
  carriers_resistant: number | null;
  others: number;
  others_resistant: number | null;
}

export interface LabView {
  min_carriers: number;
  pairs: LabPair[];
  pairs_total: number;
  genomes_labelled: number;
}

export interface GeneReport {
  run: {
    generated_at: string;
    git_commit?: string;
    amrfinder_version?: string;
    database_version?: string;
    genomes_downloaded: number;
    genomes_searched: number;
    complete: boolean;
    filter: string;
  };
  summary: { genomes: number; with_gene: number; symbols: number; genes: number; point_mutations: number; median_genes: number; max_genes: number };
  matrix: {
    genomes: number; symbols: number; cells: number; ones: number;
    preview: { genes: string[]; rows: { genome: string; species: string; values: number[]; total: number }[] };
  };
  genes_per_genome: { genes: number; genomes: number; capped: boolean }[];
  top_genes: { gene: string; name?: string; type: string; class?: string; subclass?: string; genomes: number; share: number }[];
  classes: { class: string; genomes: number; share: number; symbols: number }[];
  genera: { genus: string; genomes: number; with_gene: number; median_genes: number; top: { gene: string; share: number }[] }[];
  heatmap: { genera: string[]; genes: string[]; share: number[][]; min_genomes: number };
  gene_vs_lab: { lab: LabView; all: LabView };
}

export interface GenomeGenes {
  genome_id: string;
  searched: boolean;
  species?: string;
  genes: { gene: string; name?: string; type: string; class?: string; subclass?: string; identity: number; coverage: number; method: string }[];
}
