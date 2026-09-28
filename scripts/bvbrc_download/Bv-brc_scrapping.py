import requests
import pandas as pd
import os
import time

# ─────────────────────────────────────────
# STEP 1: Create output folder
# ─────────────────────────────────────────

output_folder = "bacteria_by_taxon"
os.makedirs(output_folder, exist_ok=True)
print(f"Output folder created: {output_folder}/")


# ─────────────────────────────────────────
# STEP 2: Fetch all genomes
# ─────────────────────────────────────────

def fetch_all_genomes(max_records=5000):
    url = "https://www.bv-brc.org/api/genome/"
    all_data = []
    batch_size = 500
    start = 0

    print("\nDownloading all genomes...")

    while len(all_data) < max_records:
        params = {
            "q": "taxon_lineage_ids:2",
            "rows": batch_size,
            "start": start,
            "fl": "genome_id,genome_name,organism_name,taxon_id,"
                  "genome_status,genome_length,gc_content,contigs,"
                  "isolation_country,host_name,disease,strain",
            "http_accept": "application/json"
        }

        response = requests.get(
            url,
            headers={"Accept": "application/json"},
            params=params
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        batch = response.json()
        if not batch:
            break

        all_data.extend(batch)
        print(f"  {len(all_data)} genomes downloaded...")
        start += batch_size
        time.sleep(1)

    df = pd.DataFrame(all_data)
    df["species_taxon_id"] = df["genome_id"].astype(str).str.split(".").str[0]
    df["variant_number"]   = df["genome_id"].astype(str).str.split(".").str[1]
    return df


# ─────────────────────────────────────────
# STEP 3: Fetch AMR data for a list of genome IDs
# ─────────────────────────────────────────

def fetch_amr(genome_ids):
    url = "https://www.bv-brc.org/api/genome_amr/"
    all_data = []
    batch_size = 20
    genome_list = list(genome_ids)

    for i in range(0, len(genome_list), batch_size):
        batch = genome_list[i:i + batch_size]
        genome_query = " OR ".join(f'"{g}"' for g in batch)

        params = {
            "q": f"genome_id:({genome_query})",
            "rows": 500,
            "start": 0,
            "fl": "genome_id,antibiotic,resistant_phenotype,"
                  "laboratory_typing_method,measurement,"
                  "measurement_unit,measurement_sign",
            "http_accept": "application/json"
        }

        response = requests.get(
            url,
            headers={"Accept": "application/json"},
            params=params
        )

        if response.status_code == 200:
            all_data.extend(response.json())

        time.sleep(0.5)

    return pd.DataFrame(all_data)


# ─────────────────────────────────────────
# STEP 4: Fetch specialty genes for a list of genome IDs
# ─────────────────────────────────────────

def fetch_genes(genome_ids):
    url = "https://www.bv-brc.org/api/specialty_gene/"
    all_data = []
    batch_size = 20
    genome_list = list(genome_ids)

    for i in range(0, len(genome_list), batch_size):
        batch = genome_list[i:i + batch_size]
        genome_query = " OR ".join(f'"{g}"' for g in batch)

        params = {
            "q": f"genome_id:({genome_query})",
            "rows": 500,
            "start": 0,
            "fl": "genome_id,property,gene,product,function,classification",
            "http_accept": "application/json"
        }

        response = requests.get(
            url,
            headers={"Accept": "application/json"},
            params=params
        )

        if response.status_code == 200:
            all_data.extend(response.json())

        time.sleep(0.5)

    return pd.DataFrame(all_data)


# ─────────────────────────────────────────
# STEP 5: Run — Download all genomes first
# ─────────────────────────────────────────

df_genomes = fetch_all_genomes(max_records=5000)

print(f"\nTotal genomes downloaded  : {len(df_genomes)}")
print(f"Unique taxon IDs found    : {df_genomes['species_taxon_id'].nunique()}")


# ─────────────────────────────────────────
# STEP 6: Group by taxon ID and save each as separate file
# ─────────────────────────────────────────

# Get all unique taxon IDs
all_taxon_ids = df_genomes["species_taxon_id"].unique()

print(f"\nCreating separate file for each taxon...")
print(f"Total taxon files to create: {len(all_taxon_ids)}")

# Summary list to track all files created
summary = []

for taxon_id in all_taxon_ids:

    print(f"\n Processing taxon: {taxon_id}")

    # ── Get all genome variants for this taxon ──
    df_taxon = df_genomes[
        df_genomes["species_taxon_id"] == taxon_id
    ].copy()

    genome_ids = df_taxon["genome_id"].unique()
    organism   = df_taxon["organism_name"].iloc[0] if "organism_name" in df_taxon.columns else "Unknown"

    print(f"   Organism       : {organism}")
    print(f"   Total variants : {len(genome_ids)}")

    # ── Fetch AMR data for this taxon ──
    print(f"   Fetching AMR data...")
    df_amr = fetch_amr(genome_ids)

    # ── Fetch genes for this taxon ──
    print(f"   Fetching genes...")
    df_gene = fetch_genes(genome_ids)

    # ── Merge genome + AMR + genes ──
    merged = pd.merge(df_taxon, df_amr,  on="genome_id", how="left")
    merged = pd.merge(merged,   df_gene, on="genome_id", how="left", suffixes=("", "_gene"))

    # Drop duplicate columns
    cols_to_drop = [col for col in merged.columns if col.endswith("_gene")]
    merged.drop(columns=cols_to_drop, inplace=True)

    # Sort by variant number
    merged = merged.sort_values(by="variant_number").reset_index(drop=True)

    # ── Clean file name ──
    # Remove special characters from organism name for safe file naming
    safe_name = organism.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

    # File name example: taxon_562_Escherichia_coli.csv
    file_name = f"taxon_{taxon_id}_{safe_name}.csv"
    file_path = os.path.join(output_folder, file_name)

    # ── Save CSV ──
    merged.to_csv(file_path, index=False)

    print(f"   Saved: {file_name}  ({len(merged)} rows)")

    # ── Add to summary ──
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
# STEP 7: Save summary file
# ─────────────────────────────────────────

df_summary = pd.DataFrame(summary)
summary_path = os.path.join(output_folder, "00_SUMMARY.csv")
df_summary.to_csv(summary_path, index=False)

print(f"\n{'='*50}")
print(f"ALL DONE!")
print(f"{'='*50}")
print(f"Total taxon files created : {len(summary)}")
print(f"Output folder             : {output_folder}/")
print(f"Summary file              : 00_SUMMARY.csv")
print(f"\nFile list:")
for s in summary:
    print(f"  {s['file_name']}  →  {s['total_variants']} variants,  {s['total_rows']} rows")