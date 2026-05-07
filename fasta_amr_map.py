"""
map_patric_to_fasta.py
======================
Maps PATRIC/BVBRC CSV files to GenBank FASTA folders using Taxon ID,
then matches individual rows to FASTA files using Genome ID.

Naming conventions detected from your dataset
----------------------------------------------
CSV files  :  amr_taxon_108981_Acinetobacter_schindleri.csv
                              ↑ Taxon ID extracted here

FASTA dirs :  taxon_108981_Acinetobacter_schindleri/
                    ↑ same Taxon ID → exact pairing, no guessing

FASTA files:  108981.12345.fasta   (Genome ID as filename stem)
              108981.67890.fasta
              ...

PATRIC CSV row:
    Taxon ID  = 108981
    Genome ID = 108981.12345   → matched to  108981.12345.fasta

Output (per species)
--------------------
  amr_taxon_108981_Acinetobacter_schindleri_mapped.csv
      → All original PATRIC columns + fasta_path, only matched strains

  amr_taxon_108981_Acinetobacter_schindleri_unmatched.csv
      → Strains present in PATRIC but missing a FASTA file

  mapping_summary.csv
      → Per-species stats: total rows, matched, unmatched, match %

Usage
-----
python map_patric_to_fasta.py \\
    --patric_dir  C:/path/to/patric_csvs \\
    --fasta_dir   C:/path/to/genbank_fasta \\
    --output_dir  C:/path/to/output

Optional flags
--------------
  --recursive     Search inside FASTA subfolders recursively
  --dry_run       Print pairing and stats without writing any files

Requirements
------------
  pip install pandas tqdm
"""

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

# ── optional progress bar ─────────────────────────────────────────────────────
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    def tqdm(it, **kw):
        return it

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

FASTA_EXTS = {".fasta", ".fa", ".fna", ".ffn", ".faa"}

# regex to pull the taxon ID from filenames like:
#   amr_taxon_108981_Acinetobacter_schindleri.csv
#   taxon_108981_Acinetobacter_schindleri/
TAXON_RE = re.compile(r"taxon[_\-](\d+)", re.IGNORECASE)


# =============================================================================
# Helpers
# =============================================================================

def extract_taxon_id(name: str) -> str | None:
    """Pull the numeric Taxon ID out of a filename or folder name."""
    m = TAXON_RE.search(name)
    return m.group(1) if m else None


def build_fasta_index(fasta_dir: Path, recursive: bool) -> dict[str, Path]:
    """
    Index every FASTA file in `fasta_dir` by its stem (lower-cased).

    For a file  108981.12345.fasta  the following keys are stored:
        "108981.12345"     ← exact Genome ID match  (primary)
        "108981_12345"     ← slug variant            (fallback)
        "12345"            ← numeric suffix only     (last resort)
    """
    index: dict[str, Path] = {}
    pattern = "**/*" if recursive else "*"

    count = 0
    for p in fasta_dir.glob(pattern):
        if not (p.is_file() and p.suffix.lower() in FASTA_EXTS):
            continue

        stem = p.stem.lower()                          # e.g. "108981.12345"
        index[stem] = p                                # exact

        slug = stem.replace(".", "_").replace("-", "_")
        index[slug] = p                                # slugified

        # also store just the numeric suffix after the first dot
        parts = stem.split(".")
        if len(parts) >= 2 and parts[-1].isdigit():
            index.setdefault(parts[-1], p)

        count += 1

    log.info("    Indexed %d FASTA file(s)", count)
    return index


def match_genome(genome_id: str, index: dict[str, Path]) -> str | None:
    """
    Try to find the FASTA file for a given Genome ID.

    Levels tried
    ------------
    1. Exact lower-case stem          "108981.12345"
    2. Slug (dots → underscores)      "108981_12345"
    3. Numeric suffix only            "12345"
    4. Genome ID appears inside key   substring scan
    """
    gid = str(genome_id).strip().lower()

    # L1 exact
    if gid in index:
        return str(index[gid])

    # L2 slug
    slug = gid.replace(".", "_").replace("-", "_")
    if slug in index:
        return str(index[slug])

    # L3 numeric suffix (part after the last dot)
    suffix = gid.split(".")[-1]
    if len(suffix) > 3 and suffix in index:
        return str(index[suffix])

    # L4 substring scan (handles zero-padded or reformatted IDs)
    for key, path in index.items():
        if gid in key or slug in key:
            return str(path)

    return None


# =============================================================================
# Core processing
# =============================================================================

def pair_csv_to_fasta(
    csv_files: list[Path],
    fasta_root: Path,
) -> dict[Path, Path | None]:
    """
    Match every CSV file to a FASTA subfolder via Taxon ID.
    Returns {csv_path: fasta_folder | None}.
    """
    # build Taxon ID → folder map from FASTA root
    taxon_to_folder: dict[str, Path] = {}
    for d in sorted(fasta_root.iterdir()):
        if d.is_dir():
            tid = extract_taxon_id(d.name)
            if tid:
                taxon_to_folder[tid] = d

    log.info("Found %d FASTA folder(s) with recognisable Taxon IDs", len(taxon_to_folder))

    pairs: dict[Path, Path | None] = {}
    for csv in csv_files:
        tid = extract_taxon_id(csv.stem)
        if tid and tid in taxon_to_folder:
            pairs[csv] = taxon_to_folder[tid]
            log.info(
                "  PAIRED   %-55s  →  %s",
                csv.name, taxon_to_folder[tid].name,
            )
        else:
            pairs[csv] = None
            if tid:
                log.warning(
                    "  NO FASTA FOLDER for Taxon ID %s  (CSV: %s)", tid, csv.name
                )
            else:
                log.warning(
                    "  Cannot extract Taxon ID from filename: %s", csv.name
                )
    return pairs


def process_pair(
    csv_path:   Path,
    fasta_dir:  Path,
    output_dir: Path,
    recursive:  bool,
    dry_run:    bool,
) -> dict:
    """Load CSV → index FASTA → match rows → write outputs → return stats."""

    log.info("")
    log.info("─" * 62)
    log.info("CSV   : %s", csv_path.name)
    log.info("FASTA : %s", fasta_dir.name)
    log.info("─" * 62)

    # ── load CSV ──────────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as exc:
        log.error("Cannot read CSV: %s", exc)
        return {"csv": csv_path.name, "error": str(exc)}

    total_rows = len(df)
    log.info("  Loaded %d rows", total_rows)

    for col in ("Genome ID", "Genome Name"):
        if col not in df.columns:
            msg = f"Column '{col}' not found in {csv_path.name}"
            log.error("  %s", msg)
            return {"csv": csv_path.name, "error": msg}

    # ── index FASTA files ─────────────────────────────────────────────────────
    fasta_index = build_fasta_index(fasta_dir, recursive)

    if not fasta_index:
        log.warning("  No FASTA files found in %s — skipping.", fasta_dir)
        return {
            "csv": csv_path.name, "fasta_dir": fasta_dir.name,
            "total_rows": total_rows, "matched": 0,
            "unmatched": total_rows, "match_%": 0.0,
        }

    # ── match each row ────────────────────────────────────────────────────────
    fasta_paths = []
    for _, row in tqdm(
        df.iterrows(), total=total_rows,
        desc=f"  {csv_path.stem[:45]}", unit="row",
        leave=True, disable=not HAS_TQDM,
    ):
        gid = str(row.get("Genome ID", "")).strip()
        fasta_paths.append(match_genome(gid, fasta_index))

    df = df.copy()
    df["fasta_path"] = fasta_paths

    matched_df   = df[df["fasta_path"].notna()]
    unmatched_df = df[df["fasta_path"].isna()]

    n_matched   = len(matched_df)
    n_unmatched = len(unmatched_df)
    pct = 100 * n_matched / total_rows if total_rows else 0.0

    log.info("  Matched %d / %d  (%.1f%%)", n_matched, total_rows, pct)

    # ── write files ───────────────────────────────────────────────────────────
    stem = csv_path.stem
    out_matched   = output_dir / f"{stem}_mapped.csv"
    out_unmatched = output_dir / f"{stem}_unmatched.csv"

    if not dry_run:
        matched_df.to_csv(out_matched, index=False)
        log.info("  Saved  -> %s", out_matched.name)

        if n_unmatched > 0:
            unmatched_df.to_csv(out_unmatched, index=False)
            log.info("  Saved  -> %s  (%d rows)", out_unmatched.name, n_unmatched)
    else:
        log.info("  [DRY RUN] Would write %s", out_matched.name)

    return {
        "csv":        csv_path.name,
        "fasta_dir":  fasta_dir.name,
        "total_rows": total_rows,
        "matched":    n_matched,
        "unmatched":  n_unmatched,
        "match_%":    round(pct, 1),
        "output":     str(out_matched) if not dry_run else "(dry run)",
    }


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    p = argparse.ArgumentParser(
        description="Map PATRIC CSV files to GenBank FASTA files via Taxon ID.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--patric_dir", required=True,
        help="Folder with PATRIC .csv files (e.g. amr_taxon_108981_*.csv).",
    )
    p.add_argument(
        "--fasta_dir", required=True,
        help="Root folder with FASTA subfolders (e.g. taxon_108981_*/).",
    )
    p.add_argument(
        "--output_dir", required=True,
        help="Output folder (created automatically if missing).",
    )
    p.add_argument(
        "--recursive", action="store_true",
        help="Search FASTA subfolders recursively.",
    )
    p.add_argument(
        "--dry_run", action="store_true",
        help="Show pairing and match statistics without writing any files.",
    )
    return p.parse_args()


def main():
    args = parse_args()

    patric_dir = Path(args.patric_dir).expanduser().resolve()
    fasta_dir  = Path(args.fasta_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    # ── validate ──────────────────────────────────────────────────────────────
    for d, label in [(patric_dir, "--patric_dir"), (fasta_dir, "--fasta_dir")]:
        if not d.is_dir():
            log.error("%s is not a valid directory: %s", label, d)
            sys.exit(1)

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    # ── discover CSV files ────────────────────────────────────────────────────
    csv_files = sorted(patric_dir.glob("*.csv"))
    if not csv_files:
        log.error("No .csv files found in: %s", patric_dir)
        sys.exit(1)
    log.info("Found %d CSV file(s)", len(csv_files))

    # ── pair CSV ↔ FASTA folder via Taxon ID ─────────────────────────────────
    log.info("Pairing CSV files with FASTA folders via Taxon ID …")
    pairs = pair_csv_to_fasta(csv_files, fasta_dir)

    valid_pairs = {k: v for k, v in pairs.items() if v is not None}
    skipped     = len(pairs) - len(valid_pairs)

    if not valid_pairs:
        log.error("No valid pairs found. Check that filenames contain 'taxon_<ID>'.")
        sys.exit(1)

    if skipped:
        log.warning("%d CSV file(s) had no matching FASTA folder and will be skipped.", skipped)

    # ── process each pair ─────────────────────────────────────────────────────
    summaries = []
    for csv_path, fasta_subfolder in valid_pairs.items():
        summary = process_pair(
            csv_path, fasta_subfolder, output_dir,
            args.recursive, args.dry_run,
        )
        summaries.append(summary)

    # ── summary report ────────────────────────────────────────────────────────
    summary_df = pd.DataFrame(summaries)

    if not args.dry_run:
        summary_path = output_dir / "mapping_summary.csv"
        summary_df.to_csv(summary_path, index=False)
    else:
        summary_path = None

    print("\n" + "=" * 64)
    print("  MAPPING SUMMARY" + ("  [DRY RUN]" if args.dry_run else ""))
    print("=" * 64)
    print(summary_df.to_string(index=False))
    print("=" * 64)

    if not args.dry_run:
        total_matched = summary_df["matched"].sum()
        total_rows    = summary_df["total_rows"].sum()
        overall_pct   = 100 * total_matched / total_rows if total_rows else 0
        print(f"\nOverall : {total_matched:,} / {total_rows:,} rows matched  ({overall_pct:.1f}%)")
        print(f"Outputs : {output_dir}")
        print(f"Summary : {summary_path}\n")


if __name__ == "__main__":
    main()
    