import requests
import pandas as pd
import os
import time

# ─────────────────────────────────────────
# TEST CONFIG
# ─────────────────────────────────────────
TEST_MAX_GENOMES = 10
TEST_MAX_TAXONS  = 2

output_folder = "bacteria_by_taxon_TEST"
os.makedirs(output_folder, exist_ok=True)
print(f"[TEST] Output folder: {output_folder}/")

HEADERS = {"Accept": "application/json"}


# ─────────────────────────────────────────
# STEP 2: Fetch genomes (limited)
# RQL format: eq(field,value)&select(f1,f2)&limit(count,start)
# ─────────────────────────────────────────

def fetch_all_genomes(max_records=10):
    base_url = "https://www.bv-brc.org/api/genome/"
    all_data = []
    batch_size = min(100, max_records)
    start = 0

    fields = "genome_id,genome_name,organism_name,strain"

    print(f"\n[TEST] Downloading up to {max_records} genomes...")

    while len(all_data) < max_records:
        remaining = max_records - len(all_data)
        count     = min(batch_size, remaining)

        # RQL query string appended after '?'
        # Using taxon 562 (E. coli) to ensure AMR records exist for testing
        rql = f"eq(taxon_lineage_ids,562)&select({fields})&limit({count},{start})"
        response = requests.get(base_url + "?" + rql, headers=HEADERS)

        if response.status_code != 200:
            print(f"  Error {response.status_code}: {response.text[:300]}")
            break

        batch = response.json()
        if not batch:
            print("  No more data returned.")
            break

        all_data.extend(batch)
        print(f"  {len(all_data)} genomes downloaded...")
        start += count
        time.sleep(1)

    df = pd.DataFrame(all_data)
    if df.empty or "genome_id" not in df.columns:
        print(f"  [ERROR] Unexpected response. Columns: {list(df.columns)}")
        return df

    df["species_taxon_id"] = df["genome_id"].astype(str).str.split(".").str[0]
    df["variant_number"]   = df["genome_id"].astype(str).str.split(".").str[1]
    return df


# ─────────────────────────────────────────
# STEP 3: Fetch AMR data
# ─────────────────────────────────────────

def fetch_amr(genome_ids):
    base_url = "https://www.bv-brc.org/api/genome_amr/"
    all_data = []
    batch_size = 20
    genome_list = list(genome_ids)

    fields = ("genome_id,genome_name,antibiotic,resistant_phenotype,"
              "measurement,measurement_sign,measurement_value,measurement_unit,"
              "laboratory_typing_method,laboratory_typing_method_version,laboratory_typing_platform,"
              "vendor,testing_standard,testing_standard_year,"
              "computational_method,computational_method_version,computational_method_performance,"
              "evidence,source,pmid")

    for i in range(0, len(genome_list), batch_size):
        batch = genome_list[i:i + batch_size]
        in_values = ",".join(batch)

        rql = f"in(genome_id,({in_values}))&select({fields})&limit(500,0)"
        response = requests.get(base_url + "?" + rql, headers=HEADERS)

        if response.status_code == 200:
            all_data.extend(response.json())
        else:
            print(f"  AMR fetch error {response.status_code}: {response.text[:200]}")

        time.sleep(0.5)

    return pd.DataFrame(all_data)


# ─────────────────────────────────────────
# STEP 4: Fetch specialty genes
# ─────────────────────────────────────────

def fetch_genes(genome_ids):
    base_url = "https://www.bv-brc.org/api/sp_gene/"
    all_data = []
    batch_size = 20
    genome_list = list(genome_ids)

    fields = "genome_id,gene"

    for i in range(0, len(genome_list), batch_size):
        batch = genome_list[i:i + batch_size]
        in_values = ",".join(batch)

        rql = f"in(genome_id,({in_values}))&select({fields})&limit(500,0)"
        response = requests.get(base_url + "?" + rql, headers=HEADERS)

        if response.status_code == 200:
            all_data.extend(response.json())
        else:
            print(f"  Gene fetch error {response.status_code}: {response.text[:200]}")

        time.sleep(0.5)

    return pd.DataFrame(all_data)


# ─────────────────────────────────────────
# STEP 5: Fetch genomes
# ─────────────────────────────────────────

df_genomes = fetch_all_genomes(max_records=TEST_MAX_GENOMES)

print(f"\nTotal genomes downloaded  : {len(df_genomes)}")
if "species_taxon_id" in df_genomes.columns:
    print(f"Unique taxon IDs found    : {df_genomes['species_taxon_id'].nunique()}")
print(f"Columns                   : {list(df_genomes.columns)}")


# ─────────────────────────────────────────
# STEP 6: Process only first N taxons
# ─────────────────────────────────────────

if "species_taxon_id" not in df_genomes.columns:
    print("[ERROR] No genomes fetched — cannot continue.")
    exit(1)

all_taxon_ids = df_genomes["species_taxon_id"].unique()[:TEST_MAX_TAXONS]
print(f"\n[TEST] Processing first {TEST_MAX_TAXONS} taxon(s): {list(all_taxon_ids)}")

summary = []

for taxon_id in all_taxon_ids:

    print(f"\n Processing taxon: {taxon_id}")

    df_taxon   = df_genomes[df_genomes["species_taxon_id"] == taxon_id].copy()
    genome_ids = df_taxon["genome_id"].unique()
    if "organism_name" in df_taxon.columns:
        organism = df_taxon["organism_name"].iloc[0]
    elif "genome_name" in df_taxon.columns:
        organism = df_taxon["genome_name"].iloc[0]
    else:
        organism = "Unknown"

    print(f"   Organism       : {organism}")
    print(f"   Total variants : {len(genome_ids)}")

    print(f"   Fetching AMR data...")
    df_amr = fetch_amr(genome_ids)
    print(f"   AMR records    : {len(df_amr)}")

    print(f"   Fetching genes...")
    df_gene = fetch_genes(genome_ids)
    print(f"   Gene records   : {len(df_gene)}")

    # Safe merge: only merge if the right-side DataFrame has data
    if not df_amr.empty and "genome_id" in df_amr.columns:
        merged = pd.merge(df_taxon, df_amr, on="genome_id", how="left")
    else:
        merged = df_taxon.copy()

    if not df_gene.empty and "genome_id" in df_gene.columns:
        merged = pd.merge(merged, df_gene, on="genome_id", how="left", suffixes=("", "_gene"))


    cols_to_drop = [col for col in merged.columns if col.endswith("_gene")]
    merged.drop(columns=cols_to_drop, inplace=True)

    # Keep only the desired output columns
    desired_cols = [
        "species_taxon_id", "variant_number", "genome_id", "genome_name", "strain",
        "antibiotic", "resistant_phenotype",
        "measurement", "measurement_sign", "measurement_value", "measurement_unit",
        "laboratory_typing_method", "laboratory_typing_method_version", "laboratory_typing_platform",
        "vendor", "testing_standard", "testing_standard_year",
        "computational_method", "computational_method_version", "computational_method_performance",
        "evidence", "source", "pmid",
        "gene",
    ]
    merged = merged[[c for c in desired_cols if c in merged.columns]]

    merged = merged.sort_values(by="variant_number").reset_index(drop=True)

    safe_name = organism.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

    file_name = f"taxon_{taxon_id}_{safe_name}.csv"
    file_path = os.path.join(output_folder, file_name)

    merged.to_csv(file_path, index=False)
    print(f"   Saved: {file_name}  ({len(merged)} rows)")
    print(f"   Columns in output: {list(merged.columns)}")

    summary.append({
        "taxon_id"       : taxon_id,
        "organism_name"  : organism,
        "total_variants" : len(genome_ids),
        "total_rows"     : len(merged),
        "amr_records"    : len(df_amr),
        "gene_records"   : len(df_gene),
        "file_name"      : file_name
    })


# ─────────────────────────────────────────
# STEP 7: Save summary
# ─────────────────────────────────────────

df_summary = pd.DataFrame(summary)
summary_path = os.path.join(output_folder, "00_SUMMARY.csv")
df_summary.to_csv(summary_path, index=False)

print(f"\n{'='*50}")
print(f"[TEST] DONE!")
print(f"{'='*50}")
print(f"Taxons processed  : {len(summary)}")
print(f"Output folder     : {output_folder}/")
print(f"\nSummary:")
print(df_summary.to_string(index=False))
