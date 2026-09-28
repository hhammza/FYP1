"""
Download BV-BRC AMR data — real-time streaming write to CSV with resume support.

Features:
  • Every API batch is flushed to disk immediately (real-time write)
  • Interrupted runs resume from the exact batch they stopped at
  • Multiple taxons download in parallel
  • Live progress bar updated every second
  • .progress.json tracks every taxon: records, unique genomes, status, timing
  • _summary block inside .progress.json gives global totals at a glance

Output folder layout:
  amr_output/
    amr_taxon_562_Escherichia_coli.csv
    amr_taxon_1280_Staphylococcus_aureus.csv
    amr_taxon_470.csv.tmp                    ← in-progress (resumed on next run)
    .progress.json                           ← full tracking + resume state
    00_SUMMARY.csv                           ← CSV version of the summary

.progress.json structure:
  {
    "_summary": {
      "session_started":        "2026-04-11T14:00:00",
      "last_updated":           "2026-04-11T14:32:01",
      "total_taxons_discovered": 347,
      "total_taxons_done":       300,
      "total_taxons_partial":    10,
      "total_taxons_error":       2,
      "total_taxons_no_data":    35,
      "total_amr_records":    98000,
      "total_unique_genomes": 45000
    },
    "562": {
      "taxon_id":    562,
      "organism":    "Escherichia coli",
      "status":      "done",
      "amr_records": 45231,
      "genomes":     12400,
      "offset":      45231,
      "batches":     91,
      "file":        "amr_taxon_562_Escherichia_coli.csv",
      "tmp_file":    "",
      "started":     "2026-04-11T14:00:05",
      "finished":    "2026-04-11T14:05:30",
      "elapsed_s":   325.4,
      "updated":     "2026-04-11T14:05:30"
    },
    ...
  }

Usage:
  python download_amr_csv.py                          # all bacterial taxons, 4 workers
  python download_amr_csv.py --workers 8              # more parallelism
  python download_amr_csv.py --taxon 562 1280 470     # specific taxons only
  python download_amr_csv.py --out my_folder          # custom output folder
  python download_amr_csv.py --taxon-lineage 1239     # Firmicutes lineage
  python download_amr_csv.py --fresh                  # ignore saved state, start over
"""

import argparse
import csv
import json
import os
import threading
import time
import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime

import requests

# ── Column mapping ───────────────────────────────────────────────────────────

API_FIELDS = (
    "taxon_id,"
    "genome_id,genome_name,"
    "antibiotic,resistant_phenotype,"
    "measurement,measurement_sign,measurement_value,measurement_unit,"
    "laboratory_typing_method,laboratory_typing_method_version,laboratory_typing_platform,"
    "vendor,testing_standard,testing_standard_year,"
    "computational_method,computational_method_version,computational_method_performance,"
    "evidence,source,pmid"
)

COLUMN_RENAME = {
    "taxon_id":                          "Taxon ID",
    "genome_id":                         "Genome ID",
    "genome_name":                       "Genome Name",
    "antibiotic":                        "Antibiotic",
    "resistant_phenotype":               "Resistant Phenotype",
    "measurement":                       "Measurement",
    "measurement_sign":                  "Measurement Sign",
    "measurement_value":                 "Measurement Value",
    "measurement_unit":                  "Measurement Unit",
    "laboratory_typing_method":          "Laboratory Typing Method",
    "laboratory_typing_method_version":  "Laboratory Typing Method Version",
    "laboratory_typing_platform":        "Laboratory Typing Platform",
    "vendor":                            "Vendor",
    "testing_standard":                  "Testing Standard",
    "testing_standard_year":             "Testing Standard Year",
    "computational_method":              "Computational Method",
    "computational_method_version":      "Computational Method Version",
    "computational_method_performance":  "Computational Method Performance",
    "evidence":                          "Evidence",
    "source":                            "Source",
    "pmid":                              "PubMed",
}

FINAL_COLUMNS = list(COLUMN_RENAME.values())

AMR_URL    = "https://www.bv-brc.org/api/genome_amr/"
GENOME_URL = "https://www.bv-brc.org/api/genome/"
HEADERS    = {"Accept": "application/json"}

# Keep BASE_URL as alias so nothing else breaks
BASE_URL = AMR_URL


# ── Progress / tracking store (.progress.json) ───────────────────────────────

class ProgressStore:
    """
    Thread-safe JSON file that tracks every taxon's scraping state.

    Top-level keys:
      "_summary"  — global totals, updated after every batch
      "<taxon_id>" — per-taxon detail record
    """

    def __init__(self, path: str, session_start: str):
        self._path  = path
        self._lock  = threading.Lock()
        self._data: dict = {}
        self._load(session_start)

    # ── Init ─────────────────────────────────────────────────────────────────

    def _load(self, session_start: str):
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as fh:
                    self._data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._data = {}

        # Ensure _summary block exists
        if "_summary" not in self._data:
            self._data["_summary"] = {
                "session_started":         session_start,
                "last_updated":            session_start,
                "total_taxons_discovered": 0,
                "total_taxons_done":       0,
                "total_taxons_partial":    0,
                "total_taxons_error":      0,
                "total_taxons_no_data":    0,
                "total_amr_records":       0,
                "total_unique_genomes":    0,
            }

    # ── Atomic save ──────────────────────────────────────────────────────────

    def _save(self):
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
        os.replace(tmp, self._path)

    # ── Summary helpers ──────────────────────────────────────────────────────

    def _rebuild_summary(self):
        """Recount totals from all taxon entries. Called under lock."""
        done = partial = error = no_data = 0
        total_records = total_genomes = 0

        for key, val in self._data.items():
            if key == "_summary":
                continue
            st = val.get("status", "")
            if   st == "done":     done     += 1
            elif st == "partial":  partial  += 1
            elif st == "error":    error    += 1
            elif st == "no_data":  no_data  += 1
            total_records += val.get("amr_records", 0)
            total_genomes += val.get("genomes",     0)

        s = self._data["_summary"]
        s["last_updated"]           = datetime.now().isoformat(timespec="seconds")
        s["total_taxons_done"]      = done
        s["total_taxons_partial"]   = partial
        s["total_taxons_error"]     = error
        s["total_taxons_no_data"]   = no_data
        s["total_amr_records"]      = total_records
        s["total_unique_genomes"]   = total_genomes

    def set_total_taxons(self, n: int):
        with self._lock:
            self._data["_summary"]["total_taxons_discovered"] = n
            self._save()

    # ── Per-taxon operations ─────────────────────────────────────────────────

    def get(self, taxon_id: int) -> dict | None:
        with self._lock:
            return self._data.get(str(taxon_id))

    def init_taxon(self, taxon_id: int, started: str):
        """Register a taxon as started (only if not already present)."""
        with self._lock:
            key = str(taxon_id)
            if key not in self._data:
                self._data[key] = {
                    "taxon_id":    taxon_id,
                    "organism":    "",
                    "status":      "partial",
                    "amr_records": 0,
                    "genomes":     0,
                    "offset":      0,
                    "batches":     0,
                    "file":        "",
                    "tmp_file":    "",
                    "started":     started,
                    "finished":    "",
                    "elapsed_s":   0,
                    "updated":     started,
                }
            else:
                # Resuming — just mark as partial again
                self._data[key]["status"]  = "partial"
                self._data[key]["updated"] = started
            self._rebuild_summary()
            self._save()

    def update_batch(self, taxon_id: int, amr_records: int, genomes: int,
                     offset: int, batches: int, organism: str, tmp_file: str):
        """Called after every flushed batch."""
        with self._lock:
            key   = str(taxon_id)
            entry = self._data.get(key, {})
            entry["amr_records"] = amr_records
            entry["genomes"]     = genomes
            entry["offset"]      = offset
            entry["batches"]     = batches
            entry["organism"]    = organism
            entry["tmp_file"]    = tmp_file
            entry["status"]      = "partial"
            entry["updated"]     = datetime.now().isoformat(timespec="seconds")
            self._data[key]      = entry
            self._rebuild_summary()
            self._save()

    def finish_taxon(self, taxon_id: int, status: str, amr_records: int,
                     genomes: int, offset: int, batches: int,
                     organism: str, file_name: str, elapsed: float):
        with self._lock:
            key   = str(taxon_id)
            entry = self._data.get(key, {})
            now   = datetime.now().isoformat(timespec="seconds")
            entry.update({
                "status":      status,
                "amr_records": amr_records,
                "genomes":     genomes,
                "offset":      offset,
                "batches":     batches,
                "organism":    organism,
                "file":        file_name if status in ("done", "ok") else entry.get("file", ""),
                "tmp_file":    "" if status in ("done", "ok", "no_data") else entry.get("tmp_file", ""),
                "finished":    now if status in ("done", "ok", "no_data") else "",
                "elapsed_s":   elapsed,
                "updated":     now,
            })
            self._data[key] = entry
            self._rebuild_summary()
            self._save()

    # ── Queries ──────────────────────────────────────────────────────────────

    def all_done_ids(self) -> set[int]:
        with self._lock:
            return {int(k) for k, v in self._data.items()
                    if k != "_summary" and v.get("status") == "done"}

    def summary_rows(self) -> list[dict]:
        with self._lock:
            rows = []
            for key, v in self._data.items():
                if key == "_summary":
                    continue
                rows.append({
                    "Taxon ID":       v.get("taxon_id", int(key)),
                    "Organism Name":  v.get("organism", ""),
                    "AMR Records":    v.get("amr_records", 0),
                    "Unique Genomes": v.get("genomes", 0),
                    "Batches":        v.get("batches", 0),
                    "File":           v.get("file", ""),
                    "Status":         v.get("status", ""),
                    "Started":        v.get("started", ""),
                    "Finished":       v.get("finished", ""),
                    "Elapsed (s)":    v.get("elapsed_s", 0),
                })
            return sorted(rows, key=lambda r: r["Taxon ID"])

    def get_summary(self) -> dict:
        with self._lock:
            return dict(self._data.get("_summary", {}))


# ── Global in-memory tracker (for the live progress bar) ────────────────────

@dataclass
class Tracker:
    total_taxons:    int = 0
    taxons_skipped:  int = 0
    taxons_started:  int = 0
    taxons_done:     int = 0
    taxons_resumed:  int = 0
    taxons_error:    int = 0
    taxons_no_data:  int = 0
    new_records:     int = 0   # records added this session only
    new_genomes:     int = 0   # genomes seen this session
    batches_written: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _active: dict         = field(default_factory=dict, repr=False)
    # _active[taxon_id] = {"records": N, "genomes": N}

    def skip(self, n: int = 1):
        with self._lock:
            self.taxons_skipped += n
            self.taxons_done    += n

    def start(self, taxon_id: int, resumed: bool = False):
        with self._lock:
            self.taxons_started += 1
            if resumed:
                self.taxons_resumed += 1
            self._active[taxon_id] = {"records": 0, "genomes": 0}

    def add_batch(self, taxon_id: int, records: int, new_genomes: int):
        with self._lock:
            a = self._active.get(taxon_id, {"records": 0, "genomes": 0})
            a["records"] += records
            a["genomes"] += new_genomes
            self._active[taxon_id] = a
            self.new_records     += records
            self.new_genomes     += new_genomes
            self.batches_written += 1

    def finish(self, taxon_id: int, status: str):
        with self._lock:
            self.taxons_done += 1
            if status == "error":   self.taxons_error   += 1
            if status == "no_data": self.taxons_no_data += 1
            self._active.pop(taxon_id, None)

    def snapshot(self) -> dict:
        with self._lock:
            active_summary = {
                tid: f"{v['records']:,}rec/{v['genomes']:,}gen"
                for tid, v in self._active.items()
            }
            return dict(
                total_taxons    = self.total_taxons,
                taxons_skipped  = self.taxons_skipped,
                taxons_started  = self.taxons_started,
                taxons_done     = self.taxons_done,
                taxons_resumed  = self.taxons_resumed,
                taxons_error    = self.taxons_error,
                taxons_no_data  = self.taxons_no_data,
                new_records     = self.new_records,
                new_genomes     = self.new_genomes,
                batches_written = self.batches_written,
                active          = active_summary,
            )


TRACKER = Tracker()
_print_lock = threading.Lock()

def log(msg: str):
    with _print_lock:
        print(msg, flush=True)


# ── Live progress bar ────────────────────────────────────────────────────────

_stop_progress = threading.Event()

def _progress_loop(refresh: float = 1.0):
    while not _stop_progress.is_set():
        s = TRACKER.snapshot()
        active_items = list(s["active"].items())
        active_str   = "  ".join(f"{tid}({info})" for tid, info in active_items[:4])
        if len(active_items) > 4:
            active_str += f"  +{len(active_items)-4} more"

        line = (
            f"\r[{datetime.now().strftime('%H:%M:%S')}]  "
            f"Taxons {s['taxons_done']}/{s['total_taxons']}  "
            f"skip={s['taxons_skipped']} resume={s['taxons_resumed']} err={s['taxons_error']}  |  "
            f"+{s['new_records']:,} records  +{s['new_genomes']:,} genomes  "
            f"{s['batches_written']} batches  |  "
            f"[ {active_str} ]          "
        )
        with _print_lock:
            print(line, end="", flush=True)
        time.sleep(refresh)
    print()

def start_progress_bar(refresh: float = 1.0) -> threading.Thread:
    t = threading.Thread(target=_progress_loop, args=(refresh,), daemon=True)
    t.start()
    return t


# ── Phase 1: Discover taxon IDs ──────────────────────────────────────────────

def get_all_taxon_ids(taxon_lineage: int = 2, batch_size: int = 5000) -> list[int]:
    """
    Discover every distinct taxon_id that has AMR data.

    Strategy:
      1. Query the genome/ endpoint (which has taxon_lineage_ids) using Solr params
         to get all genome_ids + taxon_ids under the given lineage.
         The genome/ endpoint reliably supports taxon_lineage_ids filtering.
      2. Collect unique taxon_ids from the result.
    """
    log(f"\n[Phase 1] Discovering taxon IDs under lineage {taxon_lineage} …")
    seen: set[int] = set()
    start = 0

    while True:
        # genome/ supports taxon_lineage_ids; genome_amr/ does not — use genome/ here
        rql = (
            f"eq(taxon_lineage_ids,{taxon_lineage})"
            f"&select(taxon_id)"
            f"&limit({batch_size},{start})"
        )
        try:
            resp = requests.get(GENOME_URL + "?" + rql, headers=HEADERS, timeout=60)
        except requests.RequestException as exc:
            log(f"  Network error during discovery: {exc}")
            break

        if resp.status_code != 200:
            log(f"  HTTP {resp.status_code} during discovery: {resp.text[:200]}")
            break

        batch = resp.json()
        if not batch:
            break

        for record in batch:
            tid = record.get("taxon_id")
            if tid is not None:
                seen.add(int(tid))

        start += batch_size
        log(f"  … {start:,} genomes scanned, {len(seen):,} unique taxons found")
        time.sleep(0.3)

    taxon_ids = sorted(seen)
    log(f"[Phase 1] Done — {len(taxon_ids):,} taxons found.\n")
    return taxon_ids


# ── Phase 2: Stream one taxon → write each batch immediately ─────────────────

def _api_get_with_retry(rql: str, taxon_id: int, max_retries: int = 3):
    """
    Fetch a page of genome_amr records via RQL query string.
    Retries up to max_retries times with exponential back-off.
    """
    url = AMR_URL + "?" + rql
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            log(f"\n  [{taxon_id}] HTTP {resp.status_code} (attempt {attempt}): {resp.text[:150]}")
        except requests.RequestException as exc:
            log(f"\n  [{taxon_id}] Network error (attempt {attempt}): {exc}")
        time.sleep(2 ** attempt)
    return None


def _row_to_csv_values(record: dict) -> list:
    renamed = {COLUMN_RENAME.get(k, k): v for k, v in record.items()}
    return [renamed.get(col, "") for col in FINAL_COLUMNS]


def _safe_name(text: str) -> str:
    return "".join(c for c in text.replace(" ", "_") if c.isalnum() or c == "_")


def stream_taxon_to_csv(
    taxon_id:      int,
    output_folder: str,
    store:         ProgressStore,
    batch_size:    int = 500,
    max_records:   int = 500_000,
) -> None:
    """Stream-download one taxon, writing each batch to disk immediately."""

    t_start  = datetime.now()
    t_start_s = time.time()

    # ── Check for partial resume state ───────────────────────────────────────
    saved        = store.get(taxon_id) or {}
    prior_offset = saved.get("offset", 0)
    prior_rows   = saved.get("amr_records", 0)
    prior_genomes= saved.get("genomes", 0)
    prior_batches= saved.get("batches", 0)
    organism     = saved.get("organism", "")
    tmp_file_name= saved.get("tmp_file", "")
    resumed      = prior_offset > 0

    TRACKER.start(taxon_id, resumed=resumed)

    tmp_path  = (
        os.path.join(output_folder, tmp_file_name)
        if tmp_file_name and os.path.exists(os.path.join(output_folder, tmp_file_name))
        else os.path.join(output_folder, f"amr_taxon_{taxon_id}.csv.tmp")
    )
    file_mode = "a" if resumed and os.path.exists(tmp_path) else "w"

    # Register in store
    store.init_taxon(taxon_id, t_start.isoformat(timespec="seconds"))

    if resumed:
        log(f"\n  ↩ Resuming taxon {taxon_id} — offset {prior_offset:,}, "
            f"{prior_rows:,} rows, {prior_genomes:,} genomes already saved")
    else:
        log(f"\n  → Starting taxon {taxon_id}")

    # Running counters (total = prior + new)
    offset       = prior_offset
    total_rows   = prior_rows
    total_genomes= prior_genomes
    total_batches= prior_batches
    genome_ids: set[str] = set()  # unique genome IDs seen THIS session only
    status       = "ok"

    try:
        with open(tmp_path, file_mode, newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, quoting=csv.QUOTE_NONNUMERIC)
            if file_mode == "w":
                writer.writerow(FINAL_COLUMNS)
                fh.flush()

            while total_rows < max_records:
                remaining = max_records - total_rows
                count     = min(batch_size, remaining)

                rql = (
                    f"eq(taxon_id,{taxon_id})"
                    f"&select({API_FIELDS})"
                    f"&limit({count},{offset})"
                )

                batch = _api_get_with_retry(rql, taxon_id)

                if batch is None:
                    status = "error"
                    break
                if not batch:
                    break   # exhausted all records for this taxon

                # Grab organism name from first populated record
                if not organism:
                    for rec in batch:
                        gname = rec.get("genome_name", "")
                        if gname:
                            parts = gname.split()
                            organism = " ".join(parts[:2]) if len(parts) >= 2 else parts[0]
                            break

                # Write rows and collect genome IDs
                new_genome_count = 0
                for record in batch:
                    writer.writerow(_row_to_csv_values(record))
                    gid = record.get("genome_id", "")
                    if gid and gid not in genome_ids:
                        genome_ids.add(gid)
                        new_genome_count += 1

                # Flush to disk — survives crash
                fh.flush()
                os.fsync(fh.fileno())

                n              = len(batch)
                total_rows    += n
                total_genomes += new_genome_count
                total_batches += 1
                offset        += count

                TRACKER.add_batch(taxon_id, n, new_genome_count)

                # Update JSON tracker after every successful flush
                store.update_batch(
                    taxon_id    = taxon_id,
                    amr_records = total_rows,
                    genomes     = total_genomes,
                    offset      = offset,
                    batches     = total_batches,
                    organism    = organism,
                    tmp_file    = os.path.basename(tmp_path),
                )

                time.sleep(0.4)

    except Exception as exc:
        log(f"\n  [{taxon_id}] Write error: {exc}")
        status = "error"

    # ── Finalise file ────────────────────────────────────────────────────────
    if total_rows == 0 and status == "ok":
        status = "no_data"

    elapsed = round(time.time() - t_start_s, 1)
    file_name = ""

    if status == "ok":
        safe_org  = ("_" + _safe_name(organism)) if organism else ""
        file_name = f"amr_taxon_{taxon_id}{safe_org}.csv"
        if os.path.exists(tmp_path):
            os.replace(tmp_path, os.path.join(output_folder, file_name))
        log(f"\n  ✓ Taxon {taxon_id} ({organism or 'unknown'}): "
            f"{total_rows:,} AMR records, {total_genomes:,} genomes → {file_name}  [{elapsed}s]")

    elif status == "no_data":
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        log(f"\n  – Taxon {taxon_id}: no AMR data  [{elapsed}s]")

    else:   # error — keep .tmp for next resume
        log(f"\n  ✗ Taxon {taxon_id}: error — {total_rows:,} rows saved, "
            f"will resume from offset {offset:,}  [{elapsed}s]")

    # Normalise internal "ok" → "done" for the JSON store
    json_status = "done" if status == "ok" else status

    store.finish_taxon(
        taxon_id    = taxon_id,
        status      = json_status,
        amr_records = total_rows,
        genomes     = total_genomes,
        offset      = offset,
        batches     = total_batches,
        organism    = organism,
        file_name   = file_name,
        elapsed     = elapsed,
    )
    TRACKER.finish(taxon_id, status)


# ── Summary CSV ──────────────────────────────────────────────────────────────

def write_summary_csv(store: ProgressStore, output_folder: str):
    rows = store.summary_rows()
    if not rows:
        return
    path = os.path.join(output_folder, "00_SUMMARY.csv")
    fieldnames = ["Taxon ID", "Organism Name", "AMR Records", "Unique Genomes",
                  "Batches", "File", "Status", "Started", "Finished", "Elapsed (s)"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log(f"\n  Summary CSV → {path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Stream BV-BRC AMR data to CSV — parallel, real-time write, resumable"
    )
    parser.add_argument("--taxon", type=int, nargs="+", default=None,
                        help="Specific taxon IDs (default: all under --taxon-lineage)")
    parser.add_argument("--taxon-lineage", type=int, default=2,
                        help="Lineage ID for discovery (default: 2 = Bacteria)")
    parser.add_argument("--out",     type=str, default="amr_output")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--batch",   type=int, default=500)
    parser.add_argument("--max-per-taxon", type=int, default=500_000)
    parser.add_argument("--fresh", action="store_true",
                        help="Ignore saved progress and re-download everything")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    state_path    = os.path.join(args.out, ".progress.json")
    session_start = datetime.now().isoformat(timespec="seconds")

    if args.fresh and os.path.exists(state_path):
        os.remove(state_path)
        log("[--fresh] Cleared saved progress.")

    store = ProgressStore(state_path, session_start)

    print(f"\nOutput folder : {args.out}/")
    print(f"State file    : {state_path}")
    print(f"Workers       : {args.workers}")
    print(f"Batch size    : {args.batch}")
    print(f"Session start : {session_start}\n")

    # ── Build taxon list ─────────────────────────────────────────────────────
    if args.taxon:
        all_ids = sorted(set(args.taxon))
        log(f"[User-specified] {len(all_ids)} taxon(s)")
    else:
        all_ids = get_all_taxon_ids(taxon_lineage=args.taxon_lineage)
        if not all_ids:
            print("No taxons found — exiting.")
            return

    store.set_total_taxons(len(all_ids))
    TRACKER.total_taxons = len(all_ids)

    # ── Skip already-finished taxons ─────────────────────────────────────────
    done_ids    = store.all_done_ids()
    pending_ids = [t for t in all_ids if t not in done_ids]
    skipped     = len(all_ids) - len(pending_ids)

    TRACKER.skip(skipped)

    if skipped:
        log(f"[Resume] {skipped:,} taxon(s) already complete — skipping. "
            f"{len(pending_ids):,} remaining.")

    if not pending_ids:
        log("All taxons already complete. Use --fresh to re-download.")
        write_summary_csv(store, args.out)
        _print_json_summary(store)
        return

    log(f"\n[Phase 2] Streaming {len(pending_ids):,} taxon(s) "
        f"with {args.workers} workers …\n")

    progress_thread = start_progress_bar(refresh=1.0)
    run_start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                stream_taxon_to_csv,
                tid, args.out, store, args.batch, args.max_per_taxon
            ): tid
            for tid in pending_ids
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                tid = futures[future]
                log(f"\n  [UNHANDLED] Taxon {tid}: {exc}")
                store.finish_taxon(tid, f"unhandled: {exc}", 0, 0, 0, 0, "", "", 0)
                TRACKER.finish(tid, "error")

    _stop_progress.set()
    progress_thread.join()

    write_summary_csv(store, args.out)
    _print_json_summary(store)

    elapsed_total = round(time.time() - run_start, 1)
    s = TRACKER.snapshot()
    js = store.get_summary()

    print(f"\n{'='*65}")
    print(f"ALL DONE  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")
    print(f"  Total taxons discovered : {js.get('total_taxons_discovered', 0):,}")
    print(f"  Taxons done (all-time)  : {js.get('total_taxons_done', 0):,}")
    print(f"  Taxons partial          : {js.get('total_taxons_partial', 0):,}")
    print(f"  Taxons error            : {js.get('total_taxons_error', 0):,}")
    print(f"  Taxons no AMR data      : {js.get('total_taxons_no_data', 0):,}")
    print(f"  Total AMR records       : {js.get('total_amr_records', 0):,}")
    print(f"  Total unique genomes    : {js.get('total_unique_genomes', 0):,}")
    print(f"  ── This session ──")
    print(f"  New records written     : +{s['new_records']:,}")
    print(f"  New genomes seen        : +{s['new_genomes']:,}")
    print(f"  Batches flushed         : {s['batches_written']:,}")
    print(f"  Wall-clock time         : {elapsed_total}s")
    print(f"  Output folder           : {args.out}/")
    print(f"  JSON tracker            : {state_path}")


def _print_json_summary(store: ProgressStore):
    js = store.get_summary()
    log("\n[Tracker summary]")
    for k, v in js.items():
        log(f"  {k:<35} {v}")


if __name__ == "__main__":
    main()
