import requests
import pandas as pd
import os
import time

# ─────────────────────────────────────────
# STEP 1: Create folders
# ─────────────────────────────────────────

base_folder = "bacteria_fasta"
os.makedirs(base_folder, exist_ok=True)
print(f"Base folder created: {base_folder}/")


# ─────────────────────────────────────────
# STEP 2: Fetch all genomes with taxon info
# ─────────────────────────────────────────

def fetch_all_genomes(max_records=5000):
    url = "https://www.bv-brc.org/api/genome/"
    all_data = []
    batch_size = 500
    start = 0

    print("\nDownloading genome list...")

    while len(all_data) < max_records:
        params = {
            "q"           : "taxon_lineage_ids:2",
            "rows"        : batch_size,
            "start"       : start,
            "fl"          : "genome_id,genome_name,organism_name,taxon_id,strain",
            "http_accept" : "application/json"
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
        print(f"  {len(all_data)} genomes found...")
        start += batch_size
        time.sleep(1)

    df = pd.DataFrame(all_data)
    df["species_taxon_id"] = df["genome_id"].astype(str).str.split(".").str[0]
    return df


# ─────────────────────────────────────────
# STEP 3: Download FASTA for one genome
# ─────────────────────────────────────────

def download_fasta(genome_id):
    """
    Downloads FASTA sequence for a single genome_id
    BV-BRC FASTA URL format:
    https://www.bv-brc.org/api/genome_sequence/?eq(genome_id,562.1234)&http_accept=application/dna+fasta
    """

    url = "https://www.bv-brc.org/api/genome_sequence/"

    params = {
        "eq(genome_id,"  : f"{genome_id})",
        "http_accept"    : "application/dna+fasta"
    }

    # Direct URL approach works better for FASTA
    fasta_url = (
        f"https://www.bv-brc.org/api/genome_sequence/"
        f"?eq(genome_id,{genome_id})&http_accept=application/dna+fasta"
    )

    response = requests.get(fasta_url)

    if response.status_code == 200 and len(response.text) > 10:
        return response.text
    else:
        return None


# ─────────────────────────────────────────
# STEP 4: Download FASTA files per taxon
# ─────────────────────────────────────────

def download_fasta_for_taxon(taxon_id, genome_ids, organism_name):

    # Clean organism name for folder
    safe_name = organism_name.replace(" ", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

    # Create folder for this taxon
    # Example: bacteria_fasta/taxon_562_Escherichia_coli/
    taxon_folder = os.path.join(base_folder, f"taxon_{taxon_id}_{safe_name}")
    os.makedirs(taxon_folder, exist_ok=True)

    success = 0
    failed  = 0
    skipped = 0

    for genome_id in genome_ids:

        # File path for this genome
        fasta_file = os.path.join(taxon_folder, f"{genome_id}.fasta")

        # Skip if already downloaded
        if os.path.exists(fasta_file):
            skipped += 1
            continue

        # Download FASTA
        fasta_data = download_fasta(genome_id)

        if fasta_data:
            with open(fasta_file, "w") as f:
                f.write(fasta_data)
            success += 1
            print(f"    Downloaded: {genome_id}.fasta")
        else:
            failed += 1
            print(f"    Failed    : {genome_id}")

        time.sleep(0.5)  # be polite to server

    return success, failed, skipped


# ─────────────────────────────────────────
# STEP 5: Merge all variants into ONE fasta
#         per taxon (optional but useful)
# ─────────────────────────────────────────

def merge_fasta_for_taxon(taxon_id, organism_name):

    safe_name = organism_name.replace(" ", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

    taxon_folder  = os.path.join(base_folder, f"taxon_{taxon_id}_{safe_name}")
    merged_file   = os.path.join(taxon_folder, f"taxon_{taxon_id}_ALL_VARIANTS.fasta")

    fasta_files = [
        f for f in os.listdir(taxon_folder)
        if f.endswith(".fasta") and "ALL_VARIANTS" not in f
    ]

    if not fasta_files:
        return

    print(f"  Merging {len(fasta_files)} FASTA files for {organism_name}...")

    with open(merged_file, "w") as outfile:
        for fasta_file in fasta_files:
            file_path = os.path.join(taxon_folder, fasta_file)
            with open(file_path, "r") as infile:
                outfile.write(infile.read())
                outfile.write("\n")

    print(f"  Merged file saved: taxon_{taxon_id}_ALL_VARIANTS.fasta")


# ─────────────────────────────────────────
# STEP 6: Run everything
# ─────────────────────────────────────────

# 1. Get all genomes
df_genomes = fetch_all_genomes(max_records=5000)

print(f"\nTotal genomes     : {len(df_genomes)}")
print(f"Unique taxon IDs  : {df_genomes['species_taxon_id'].nunique()}")

# 2. Group by taxon and download FASTA files
all_taxon_ids = df_genomes["species_taxon_id"].unique()

summary = []

for taxon_id in all_taxon_ids:

    df_taxon      = df_genomes[df_genomes["species_taxon_id"] == taxon_id]
    genome_ids    = df_taxon["genome_id"].unique()
    organism_name = df_taxon["organism_name"].iloc[0] if "organism_name" in df_taxon.columns else "Unknown"

    print(f"\nTaxon: {taxon_id} | {organism_name} | {len(genome_ids)} variants")

    # Download individual FASTA files
    success, failed, skipped = download_fasta_for_taxon(
        taxon_id,
        genome_ids,
        organism_name
    )

    # Merge all into one big FASTA file for this taxon
    merge_fasta_for_taxon(taxon_id, organism_name)

    summary.append({
        "taxon_id"       : taxon_id,
        "organism_name"  : organism_name,
        "total_variants" : len(genome_ids),
        "downloaded"     : success,
        "failed"         : failed,
        "skipped"        : skipped
    })


# ─────────────────────────────────────────
# STEP 7: Save summary
# ─────────────────────────────────────────

df_summary = pd.DataFrame(summary)
df_summary.to_csv(
    os.path.join(base_folder, "00_FASTA_SUMMARY.csv"),
    index=False
)

print(f"\n{'='*50}")
print(f"ALL DONE!")
print(f"{'='*50}")
print(df_summary.to_string(index=False))