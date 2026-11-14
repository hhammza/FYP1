/* The answers of /api/explore/* (backend/api/explorer.py). */

export interface Option { value: string; label: string; n: number }

export interface ExploreMeta {
  organisms: { gram: 'positive' | 'negative' | 'other'; genera: { genus: string; n: number; species: Option[] }[] }[];
  antibiotic_hierarchy: { family: string; subfamilies: { subfamily: string; antibiotics: { value: string; n: number; aware: string }[] }[] }[];
  chemical_groups: Option[];
  countries: Option[];
  infection_types: Option[];
  diseases: Option[];
  disease_by_infection_type: Record<string, string[]>;
  disease_infection_type: Record<string, string>;
  aware: Option[];
  year_range: [number, number] | null;
  resistance_types: { resistance_type: string; label: string; note: string }[];
  min_n_default: number;
  build: { built?: string; lab_rows?: number };
}

export interface Totals { tested: number; n: number; r: number; intermediate: number; resistant_pct: number | null; low_sample: boolean }

export interface SummaryRow extends Totals { value: string | number; split?: string; label?: string }

export interface Summary { by: string; split: string | null; min_n: number; include_intermediate: boolean; total: Totals; rows: SummaryRow[] }

export interface CountryRow {
  iso3: string; country: string; tested: number; n: number; resistant_pct: number | null; low_sample: boolean;
  top_types: { type: string; resistant_pct: number; n: number; low_sample: boolean }[];
  dominant_type: string | null; dominant_pct: number | null; top_organism: string | null;
}

export interface Countries { min_n: number; include_intermediate: boolean; countries: CountryRow[];
  resistance_types: { resistance_type: string; label: string; note: string }[] }

export interface DrugComponent {
  name: string; pubchem_cid: number; pubchem_title: string | null; iupac_name: string | null;
  molecular_formula: string | null; molecular_weight: number | null; smiles: string | null;
  brand_names_guess: string[]; pubchem_url: string; structure_url: string | null;
}

export interface DrugDetail {
  antibiotic: string; requested: string; alias_of: string | null;
  family: string; subfamily: string; chemical_group: string; atc_code: string | null; aware: string; use: string; review: string | null;
  mechanism: string; target: string; resistance_mechanism: string; core_structure: string | null;
  components: DrugComponent[]; missing_from_pubchem: string[];
  resistance: Totals; by_year: { year: number; n: number; r: number; resistant_pct: number | null; low_sample: boolean }[];
}
