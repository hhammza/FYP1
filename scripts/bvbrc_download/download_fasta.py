"""
Download FASTA files from BV-BRC for every genome found in AMR CSV output.

Sources for genome IDs (pick one):
  1. --amr-folder amr_output   (default) reads Genome ID column from all
                                amr_taxon_*.csv files produced by download_amr_csv.py
  2. --taxon 562 1280 …        fetches genome IDs live from BV-BRC genome API

Output layout:
  fasta_output/
    taxon_562_Escherichia_coli/
      562.144628.fasta
      562.5295.fasta
      …
    taxon_1280_Staphylococcus_aureus/
      1280.46922.fasta
      …
    .fasta_progress.json    ← full tracking + resume state
    00_FASTA_SUMMARY.csv    ← one row per taxon

.fasta_progress.json structure:
  {
    "_summary": {
      "session_started":   "2026-04-11T14:00:00",
      "last_updated":      "2026-04-11T14:32:01",
      "total_taxons":      347,
      "total_genomes":     45000,
      "downloaded":        43000,
      "failed":              500,
      "skipped":            1500,
      "total_bytes":    9000000000
    },
    "562": {
      "taxon_id":     562,
      "organism":     "Escherichia coli",
      "folder":       "taxon_562_Escherichia_coli",
      "total_genomes":12400,
      "downloaded":   12000,
      "failed":          50,
      "skipped":        350,
      "total_bytes": 5000000000,
      "status":       "done",
      "started":      "2026-04-11T14:00:05",
      "finished":     "2026-04-11T14:45:00",
      "elapsed_s":    2695.0,
      "updated":      "2026-04-11T14:45:00"
    }
  }

Usage:
  python download_fasta.py                              # read from amr_output/
  python download_fasta.py --amr-folder my_amr_data    # custom AMR folder
  python download_fasta.py --taxon 562 1280            # fetch genome IDs live
  python download_fasta.py --out fasta_output          # custom output folder
  python download_fasta.py --workers 8                 # parallel downloads
  python download_fasta.py --fresh                     # ignore saved state
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
from pathlib import Path

import requests

# ── API constants ────────────────────────────────────────────────────────────

FASTA_URL    = "https://www.bv-brc.org/api/genome_sequence/"
GENOME_URL   = "https://www.bv-brc.org/api/genome/"
HEADERS_JSON = {"Accept": "application/json"}
HEADERS_FASTA= {"Accept": "application/dna+fasta"}

CHUNK_SIZE   = 1024 * 64   # 64 KB streaming chunks


# ── JSON progress store ──────────────────────────────────────────────────────

class FastaProgressStore:
    """
    Thread-safe JSON file tracking every taxon and global download stats.
    Updated atomically after every genome download.
    """

    def __init__(self, path: str, session_start: str):
        self._path  = path
        self._lock  = threading.Lock()
        self._data: dict = {}
        self._load(session_start)

    def _load(self, session_start: str):
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as fh:
                    self._data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._data = {}

        if "_summary" not in self._data:
            self._data["_summary"] = {
                "session_started": session_start,
                "last_updated":    session_start,
                "total_taxons":    0,
                "total_genomes":   0,
                "downloaded":      0,
                "failed":          0,
                "skipped":         0,
                "total_bytes":     0,
            }

    def _save(self):
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
        os.replace(tmp, self._path)

    def _rebuild_summary(self):
        """Recount global totals from all taxon entries. Called under lock."""
        total_t = total_g = dl = fail = skip = total_b = 0
        for key, val in self._data.items():
            if key == "_summary":
                continue
            total_t += 1
            total_g += val.get("total_genomes", 0)
            dl      += val.get("downloaded", 0)
            fail    += val.get("failed", 0)
            skip    += val.get("skipped", 0)
            total_b += val.get("total_bytes", 0)

        s = self._data["_summary"]
        s["last_updated"]  = datetime.now().isoformat(timespec="seconds")
        s["total_taxons"]  = total_t
        s["total_genomes"] = total_g
        s["downloaded"]    = dl
        s["failed"]        = fail
        s["skipped"]       = skip
        s["total_bytes"]   = total_b

    # ── Public API ───────────────────────────────────────────────────────────

    def register_taxon(self, taxon_id: int, organism: str, folder: str,
                       total_genomes: int, started: str):
        with self._lock:
            key = str(taxon_id)
            existing = self._data.get(key, {})
            self._data[key] = {
                "taxon_id":     taxon_id,
                "organism":     organism,
                "folder":       folder,
                "total_genomes":total_genomes,
                "downloaded":   existing.get("downloaded", 0),
                "failed":       existing.get("failed", 0),
                "skipped":      existing.get("skipped", 0),
                "total_bytes":  existing.get("total_bytes", 0),
                "status":       "partial",
                "started":      existing.get("started", started),
                "finished":     "",
                "elapsed_s":    existing.get("elapsed_s", 0),
                "updated":      started,
            }
            self._rebuild_summary()
            self._save()

    def record_genome(self, taxon_id: int, result: str, bytes_written: int = 0):
        """
        result: "downloaded" | "failed" | "skipped"
        Called after each genome, thread-safe.
        """
        with self._lock:
            key   = str(taxon_id)
            entry = self._data.get(key, {})
            entry[result]        = entry.get(result, 0) + 1
            entry["total_bytes"] = entry.get("total_bytes", 0) + bytes_written
            entry["updated"]     = datetime.now().isoformat(timespec="seconds")
            self._data[key]      = entry
            self._rebuild_summary()
            self._save()

    def finish_taxon(self, taxon_id: int, elapsed: float):
        with self._lock:
            key   = str(taxon_id)
            entry = self._data.get(key, {})
            now   = datetime.now().isoformat(timespec="seconds")
            entry["status"]    = "done"
            entry["finished"]  = now
            entry["elapsed_s"] = elapsed
            entry["updated"]   = now
            self._data[key]    = entry
            self._rebuild_summary()
            self._save()

    def get_taxon_counts(self, taxon_id: int) -> dict:
        with self._lock:
            return dict(self._data.get(str(taxon_id), {}))

    def all_done_ids(self) -> set[int]:
        with self._lock:
            return {int(k) for k, v in self._data.items()
                    if k != "_summary" and v.get("status") == "done"}

    def get_summary(self) -> dict:
        with self._lock:
            return dict(self._data.get("_summary", {}))

    def summary_rows(self) -> list[dict]:
        with self._lock:
            rows = []
            for key, v in self._data.items():
                if key == "_summary":
                    continue
                rows.append({
                    "Taxon ID":       v.get("taxon_id", int(key)),
                    "Organism":       v.get("organism", ""),
                    "Folder":         v.get("folder", ""),
                    "Total Genomes":  v.get("total_genomes", 0),
                    "Downloaded":     v.get("downloaded", 0),
                    "Failed":         v.get("failed", 0),
                    "Skipped":        v.get("skipped", 0),
                    "Total Bytes":    v.get("total_bytes", 0),
                    "Status":         v.get("status", ""),
                    "Started":        v.get("started", ""),
                    "Finished":       v.get("finished", ""),
                    "Elapsed (s)":    v.get("elapsed_s", 0),
                })
            return sorted(rows, key=lambda r: r["Taxon ID"])


# ── Global in-memory tracker (live progress bar) ─────────────────────────────

@dataclass
class Tracker:
    total_genomes:   int = 0
    downloaded:      int = 0
    failed:          int = 0
    skipped:         int = 0
    total_bytes:     int = 0
    taxons_done:     int = 0
    taxons_total:    int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    # active[genome_id] = taxon_id
    _active: dict         = field(default_factory=dict, repr=False)

    def start_genome(self, genome_id: str, taxon_id: int):
        with self._lock:
            self._active[genome_id] = taxon_id

    def finish_genome(self, genome_id: str, result: str, nb: int = 0):
        with self._lock:
            self._active.pop(genome_id, None)
            if result == "downloaded": self.downloaded  += 1; self.total_bytes += nb
            elif result == "failed":   self.failed      += 1
            elif result == "skipped":  self.skipped     += 1

    def finish_taxon(self):
        with self._lock:
            self.taxons_done += 1

    def snapshot(self) -> dict:
        with self._lock:
            return dict(
                total_genomes = self.total_genomes,
                downloaded    = self.downloaded,
                failed        = self.failed,
                skipped       = self.skipped,
                total_bytes   = self.total_bytes,
                taxons_done   = self.taxons_done,
                taxons_total  = self.taxons_total,
                active_count  = len(self._active),
                active_sample = list(self._active.keys())[:5],
            )


TRACKER = Tracker()
_print_lock = threading.Lock()

def log(msg: str):
    with _print_lock:
        print(msg, flush=True)

def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


# ── Live progress bar ────────────────────────────────────────────────────────

_stop_progress = threading.Event()

def _progress_loop(refresh: float = 1.0):
    while not _stop_progress.is_set():
        s    = TRACKER.snapshot()
        done = s["downloaded"] + s["failed"] + s["skipped"]
        pct  = (done / s["total_genomes"] * 100) if s["total_genomes"] else 0
        sample = ", ".join(s["active_sample"])
        if s["active_count"] > 5:
            sample += f" +{s['active_count']-5}"

        line = (
            f"\r[{datetime.now().strftime('%H:%M:%S')}]  "
            f"Genomes {done:,}/{s['total_genomes']:,} ({pct:.1f}%)  "
            f"✓{s['downloaded']:,} ✗{s['failed']:,} ↷{s['skipped']:,}  |  "
            f"{_fmt_bytes(s['total_bytes'])}  |  "
            f"Taxons {s['taxons_done']}/{s['taxons_total']}  |  "
            f"[ {sample} ]          "
        )
        with _print_lock:
            print(line, end="", flush=True)
        time.sleep(refresh)
    print()

def start_progress_bar() -> threading.Thread:
    t = threading.Thread(target=_progress_loop, daemon=True)
    t.start()
    return t


# ── Read genome IDs from AMR CSV files ──────────────────────────────────────

def load_genomes_from_amr_folder(amr_folder: str) -> dict[int, dict]:
    """
    Returns {taxon_id: {"organism": str, "genome_ids": [str, ...]}}
    by reading all amr_taxon_*.csv files.
    """
    folder = Path(amr_folder)
    csv_files = sorted(folder.glob("amr_taxon_*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No amr_taxon_*.csv files found in '{amr_folder}'. "
            "Run download_amr_csv.py first, or use --taxon to specify taxons directly."
        )

    log(f"[Source] Reading genome IDs from {len(csv_files)} AMR CSV file(s) in '{amr_folder}' …")
    taxons: dict[int, dict] = {}

    for csv_path in csv_files:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                tid_raw = row.get("Taxon ID", "").strip()
                gid_raw = row.get("Genome ID", "").strip()
                org_raw = row.get("Genome Name", "").strip()
                if not tid_raw or not gid_raw:
                    continue
                try:
                    tid = int(float(tid_raw))
                except ValueError:
                    continue

                if tid not in taxons:
                    parts = org_raw.split()
                    organism = " ".join(parts[:2]) if len(parts) >= 2 else org_raw
                    taxons[tid] = {"organism": organism, "genome_ids": set()}

                taxons[tid]["genome_ids"].add(gid_raw)

    # Convert sets → sorted lists
    for tid in taxons:
        taxons[tid]["genome_ids"] = sorted(taxons[tid]["genome_ids"])

    total = sum(len(v["genome_ids"]) for v in taxons.values())
    log(f"[Source] {len(taxons):,} taxons, {total:,} unique genomes loaded.\n")
    return taxons


# ── Fetch genome IDs from BV-BRC API ────────────────────────────────────────

def fetch_genomes_for_taxon(taxon_id: int, batch_size: int = 500) -> tuple[str, list[str]]:
    """Returns (organism_name, [genome_id, ...]) by querying the genome API."""
    all_data, start, organism = [], 0, ""

    while True:
        rql = (
            f"eq(taxon_id,{taxon_id})"
            f"&select(genome_id,genome_name)"
            f"&limit({batch_size},{start})"
        )
        try:
            resp = requests.get(GENOME_URL + "?" + rql, headers=HEADERS_JSON, timeout=30)
        except requests.RequestException as exc:
            log(f"  [{taxon_id}] Genome list error: {exc}")
            break

        if resp.status_code != 200:
            log(f"  [{taxon_id}] HTTP {resp.status_code} fetching genome list")
            break

        batch = resp.json()
        if not batch:
            break

        all_data.extend(batch)
        if not organism and batch:
            gname = batch[0].get("genome_name", "")
            parts = gname.split()
            organism = " ".join(parts[:2]) if len(parts) >= 2 else gname

        start += batch_size
        time.sleep(0.3)

    genome_ids = sorted({r["genome_id"] for r in all_data if r.get("genome_id")})
    return organism, genome_ids


# ── Download one FASTA file, streaming directly to disk ─────────────────────

def download_genome_fasta(
    genome_id:    str,
    dest_path:    str,
    max_retries:  int = 3,
) -> tuple[str, int]:
    """
    Stream-download FASTA for genome_id → dest_path.
    Returns ("downloaded"|"failed"|"skipped", bytes_written).
    """
    # Skip if already complete (non-empty file on disk)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return "skipped", os.path.getsize(dest_path)

    url = f"{FASTA_URL}?eq(genome_id,{genome_id})&http_accept=application/dna+fasta"
    tmp_path = dest_path + ".tmp"

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS_FASTA,
                                stream=True, timeout=60)
            if resp.status_code != 200:
                log(f"\n  [{genome_id}] HTTP {resp.status_code} (attempt {attempt})")
                time.sleep(2 ** attempt)
                continue

            bytes_written = 0
            with open(tmp_path, "w", encoding="utf-8") as fh:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE, decode_unicode=True):
                    if chunk:
                        fh.write(chunk)
                        bytes_written += len(chunk.encode("utf-8"))
                fh.flush()
                os.fsync(fh.fileno())

            if bytes_written > 0:
                os.replace(tmp_path, dest_path)   # atomic rename
                return "downloaded", bytes_written
            else:
                # Empty response — no FASTA available
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                return "failed", 0

        except requests.RequestException as exc:
            log(f"\n  [{genome_id}] Network error (attempt {attempt}): {exc}")
            time.sleep(2 ** attempt)

    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    return "failed", 0


# ── Process one taxon: submit all genome downloads to the shared pool ─────────

def process_taxon(
    taxon_id:     int,
    organism:     str,
    genome_ids:   list[str],
    output_folder:str,
    store:        FastaProgressStore,
    pool:         concurrent.futures.ThreadPoolExecutor,
) -> list[concurrent.futures.Future]:
    """
    Create taxon folder, register in store, submit one Future per genome.
    Returns list of futures (caller collects results).
    """
    safe_org    = "".join(c for c in organism.replace(" ", "_")
                          if c.isalnum() or c == "_")
    folder_name = f"taxon_{taxon_id}_{safe_org}" if safe_org else f"taxon_{taxon_id}"
    taxon_folder= os.path.join(output_folder, folder_name)
    os.makedirs(taxon_folder, exist_ok=True)

    started = datetime.now().isoformat(timespec="seconds")
    store.register_taxon(taxon_id, organism, folder_name, len(genome_ids), started)

    futures = []
    for gid in genome_ids:
        dest = os.path.join(taxon_folder, f"{gid}.fasta")
        fut  = pool.submit(_genome_task, gid, taxon_id, dest, store)
        futures.append(fut)

    return futures


def _genome_task(
    genome_id:    str,
    taxon_id:     int,
    dest_path:    str,
    store:        FastaProgressStore,
) -> tuple[str, str, int]:
    """Worker: download one genome, update store + tracker. Returns (genome_id, result, bytes)."""
    TRACKER.start_genome(genome_id, taxon_id)
    result, nb = download_genome_fasta(genome_id, dest_path)
    store.record_genome(taxon_id, result, nb)
    TRACKER.finish_genome(genome_id, result, nb)
    return genome_id, result, nb


# ── Summary CSV ──────────────────────────────────────────────────────────────

def write_summary_csv(store: FastaProgressStore, output_folder: str):
    rows = store.summary_rows()
    if not rows:
        return
    path = os.path.join(output_folder, "00_FASTA_SUMMARY.csv")
    fields = ["Taxon ID", "Organism", "Folder", "Total Genomes",
              "Downloaded", "Failed", "Skipped", "Total Bytes",
              "Status", "Started", "Finished", "Elapsed (s)"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    log(f"\n  Summary CSV → {path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download FASTA files from BV-BRC — parallel, real-time write, resumable"
    )

    src = parser.add_mutually_exclusive_group()
    src.add_argument("--amr-folder", type=str, default="amr_output",
                     help="Folder with amr_taxon_*.csv files (default: amr_output)")
    src.add_argument("--taxon", type=int, nargs="+",
                     help="Taxon IDs — fetch genome list live from BV-BRC")

    parser.add_argument("--out",     type=str, default="fasta_output",
                        help="Output folder (default: fasta_output)")
    parser.add_argument("--workers", type=int, default=8,
                        help="Parallel download threads (default: 8)")
    parser.add_argument("--fresh",   action="store_true",
                        help="Ignore saved state (still skips existing .fasta files)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    state_path    = os.path.join(args.out, ".fasta_progress.json")
    session_start = datetime.now().isoformat(timespec="seconds")

    if args.fresh and os.path.exists(state_path):
        os.remove(state_path)
        log("[--fresh] Cleared saved JSON state (existing .fasta files are still skipped).")

    store = FastaProgressStore(state_path, session_start)

    print(f"\nOutput folder : {args.out}/")
    print(f"State file    : {state_path}")
    print(f"Workers       : {args.workers}")
    print(f"Session start : {session_start}\n")

    # ── Load genome IDs ──────────────────────────────────────────────────────
    if args.taxon:
        taxons: dict[int, dict] = {}
        log(f"[Source] Fetching genome lists from BV-BRC for {len(args.taxon)} taxon(s) …")
        for tid in args.taxon:
            organism, genome_ids = fetch_genomes_for_taxon(tid)
            taxons[tid] = {"organism": organism, "genome_ids": genome_ids}
            log(f"  Taxon {tid} ({organism}): {len(genome_ids):,} genomes")
    else:
        try:
            taxons = load_genomes_from_amr_folder(args.amr_folder)
        except FileNotFoundError as exc:
            print(f"\n[ERROR] {exc}")
            return

    # ── Skip fully-done taxons ───────────────────────────────────────────────
    done_ids    = store.all_done_ids()
    pending     = {tid: v for tid, v in taxons.items() if tid not in done_ids}
    skipped_t   = len(taxons) - len(pending)

    total_genomes = sum(len(v["genome_ids"]) for v in pending.values())
    TRACKER.total_genomes = total_genomes
    TRACKER.taxons_total  = len(pending)

    if skipped_t:
        log(f"[Resume] {skipped_t:,} taxon(s) already complete — skipping.")
    if not pending:
        log("All taxons already complete. Use --fresh to reset JSON state.")
        write_summary_csv(store, args.out)
        return

    log(f"[Phase 2] Downloading FASTA for {len(pending):,} taxon(s), "
        f"{total_genomes:,} genomes with {args.workers} workers …\n")

    progress_thread = start_progress_bar()
    run_start = time.time()

    # ── Single flat thread pool — all genome downloads share workers ──────────
    taxon_times: dict[int, float] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:

        # Submit all genomes for all taxons at once
        all_futures: dict[concurrent.futures.Future, int] = {}
        for tid, info in pending.items():
            taxon_times[tid] = time.time()
            futs = process_taxon(
                tid, info["organism"], info["genome_ids"],
                args.out, store, pool
            )
            for f in futs:
                all_futures[f] = tid

        # Collect results as they finish
        taxon_done_count: dict[int, int] = {tid: 0 for tid in pending}
        taxon_total_count: dict[int, int] = {
            tid: len(info["genome_ids"]) for tid, info in pending.items()
        }

        for future in concurrent.futures.as_completed(all_futures):
            tid = all_futures[future]
            try:
                future.result()
            except Exception as exc:
                gid = "unknown"
                log(f"\n  [UNHANDLED] taxon {tid} genome {gid}: {exc}")
                store.record_genome(tid, "failed")
                TRACKER.finish_genome(gid, "failed")

            taxon_done_count[tid] += 1

            # When all genomes for this taxon are done, finalise it
            if taxon_done_count[tid] == taxon_total_count[tid]:
                elapsed = round(time.time() - taxon_times[tid], 1)
                store.finish_taxon(tid, elapsed)
                TRACKER.finish_taxon()
                tc = store.get_taxon_counts(tid)
                log(
                    f"\n  ✓ Taxon {tid} ({pending[tid]['organism']}): "
                    f"{tc.get('downloaded',0):,} downloaded, "
                    f"{tc.get('failed',0):,} failed, "
                    f"{tc.get('skipped',0):,} skipped, "
                    f"{_fmt_bytes(tc.get('total_bytes',0))}  [{elapsed}s]"
                )

    _stop_progress.set()
    progress_thread.join()

    write_summary_csv(store, args.out)

    elapsed_total = round(time.time() - run_start, 1)
    js = store.get_summary()

    print(f"\n{'='*65}")
    print(f"ALL DONE  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")
    print(f"  Total taxons          : {js.get('total_taxons', 0):,}")
    print(f"  Total genomes         : {js.get('total_genomes', 0):,}")
    print(f"  Downloaded            : {js.get('downloaded', 0):,}")
    print(f"  Failed                : {js.get('failed', 0):,}")
    print(f"  Skipped (existed)     : {js.get('skipped', 0):,}")
    print(f"  Total data written    : {_fmt_bytes(js.get('total_bytes', 0))}")
    print(f"  Wall-clock time       : {elapsed_total}s")
    print(f"  Output folder         : {args.out}/")
    print(f"  JSON tracker          : {state_path}")


if __name__ == "__main__":
    main()
