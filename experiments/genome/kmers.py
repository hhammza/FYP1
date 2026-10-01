"""K-mer features from the complete genome assemblies (Track B).

    python experiments/genome/kmers.py            # build the cache (~10-20 min)
    python experiments/genome/kmers.py --limit 5  # quick test

    # genomes somewhere else, gzipped or not, in subfolders (e.g. on Google
    # Drive from notebooks/download_genomes_to_drive.ipynb), saved in parts
    # so a stopped run resumes, then merged with the existing cache:
    python kmers.py --genomes DIR --parts PARTS_DIR \
        --merge kmer6_counts.npz --out kmer6_counts_all.npz
    (notebooks/build_kmers_on_drive.ipynb runs this in Colab)

Reads every Data/genomes_full/<genome_id>.fna once and stores its 6-mer counts
in experiments/cache/kmer6_counts.npz. Shorter k-mers are derived from those
counts (kmer_matrix below), so k = 3, 4, 5 and 6 cost one pass over the 11 GB.

Two details that matter for the numbers:

  * Counting stays inside each contig. An assembly is hundreds of contigs, and
    a k-mer spanning the join between two of them is not real sequence.
  * A k-mer is kept only if all its bases are A, C, G or T; windows touching
    N or any other code are skipped.

Deriving a k-mer count from the 6-mer counts sums over the trailing bases, so
it misses the last (6 - k) k-mers of each contig: a few thousand out of
millions per genome, well below the noise in these features.

The shipped K-mer model read the truncated FASTAs in Data/fasta_output/ (about
17% of an E. coli genome); every Track B run uses these complete assemblies.
"""
import argparse
import glob
import gzip
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(HERE)
sys.path.insert(0, EXPERIMENTS)

K_MAX = 6
N_MAX = 4 ** K_MAX
CACHE = os.path.join(EXPERIMENTS, 'cache', 'kmer6_counts.npz')
BASES = 'ACGT'

# byte -> 0..3 for A C G T (either case), 4 for anything else
_LUT = np.full(256, 4, dtype=np.uint8)
for _i, _c in enumerate(BASES):
    _LUT[ord(_c)] = _i
    _LUT[ord(_c.lower())] = _i


def genomes_dir():
    from lib import data_prep   # only here, so the file also runs on its own (Colab)
    return os.path.join(data_prep.data_root(), 'genomes_full')


def genome_id(path):
    name = os.path.basename(path)
    return name[:-len('.fna.gz')] if name.endswith('.fna.gz') else name[:-len('.fna')]


def genome_files(folder):
    """Every finished assembly under `folder`: .fna or .fna.gz, any depth
    (unfinished downloads end in .part and are left out)."""
    return sorted(glob.glob(os.path.join(folder, '**', '*.fna'), recursive=True)
                  + glob.glob(os.path.join(folder, '**', '*.fna.gz'), recursive=True))


def contigs(path):
    """Yield each contig of a FASTA file as raw bytes."""
    chunks = []
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rb') as fh:
        for line in fh:
            if line.startswith(b'>'):
                if chunks:
                    yield b''.join(chunks)
                chunks = []
            else:
                chunks.append(line.strip())
    if chunks:
        yield b''.join(chunks)


def count_6mers(seq_codes):
    """6-mer counts (4096,) of one contig given as 0..4 codes."""
    n = len(seq_codes) - K_MAX + 1
    if n <= 0:
        return np.zeros(N_MAX, dtype=np.int64)
    codes = seq_codes.astype(np.int64)
    bad = (seq_codes == 4).astype(np.int32)
    # windows containing a non-ACGT base: a moving sum of `bad` over 6 bases
    csum = np.concatenate([[0], np.cumsum(bad)])
    ok = (csum[K_MAX:] - csum[:-K_MAX]) == 0
    idx = np.zeros(n, dtype=np.int64)
    for j in range(K_MAX):
        idx = idx * 4 + np.minimum(codes[j:j + n], 3)
    return np.bincount(idx[ok], minlength=N_MAX)


def genome_features(path):
    """(genome_id, 6-mer counts, length in ACGT bases, GC fraction)."""
    gid = genome_id(path)
    counts = np.zeros(N_MAX, dtype=np.int64)
    acgt = gc = 0
    for raw in contigs(path):
        codes = _LUT[np.frombuffer(raw, dtype=np.uint8)]
        counts += count_6mers(codes)
        acgt += int((codes < 4).sum())
        gc += int(((codes == 1) | (codes == 2)).sum())
    return gid, counts.astype(np.uint32), acgt, (gc / acgt if acgt else np.nan)


def build(limit=None, workers=4):
    paths = sorted(glob.glob(os.path.join(genomes_dir(), '*.fna')))
    if limit:
        paths = paths[:limit]
    if not paths:
        raise FileNotFoundError(f'no .fna files in {genomes_dir()}; see experiments/genome/README.md')
    print(f'[kmers] {len(paths):,} genomes from {genomes_dir()}')
    t0 = time.time()
    ids, counts, lengths, gcs = [], [], [], []
    with Pool(workers) as pool:
        for i, (gid, c, n, gc) in enumerate(pool.imap(genome_features, paths, chunksize=4), 1):
            ids.append(gid)
            counts.append(c)
            lengths.append(n)
            gcs.append(gc)
            if i % 250 == 0:
                print(f'[kmers] {i:,}/{len(paths):,}  {time.time() - t0:.0f}s')
    out = CACHE if not limit else CACHE.replace('.npz', f'_limit{limit}.npz')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, genome_id=np.array(ids, dtype=str), counts=np.stack(counts),
                        length=np.array(lengths, dtype=np.int64), gc=np.array(gcs))
    print(f'[kmers] wrote {os.path.relpath(out, os.path.dirname(EXPERIMENTS))} '
          f'in {time.time() - t0:.0f}s')
    return out


def save(path, ids, counts, lengths, gcs):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + '.tmp.npz'
    np.savez_compressed(tmp, genome_id=np.array(ids, dtype=str), counts=np.stack(counts),
                        length=np.array(lengths, dtype=np.int64), gc=np.array(gcs))
    os.replace(tmp, path)       # a part exists only once it is complete


def build_parts(folder, parts, part_size=2000, workers=4):
    """Count every genome under `folder` not yet in a part file in `parts`,
    `part_size` genomes per part. Run again to resume or to add genomes that
    arrived since (a download still in progress)."""
    os.makedirs(parts, exist_ok=True)
    done = set()
    existing = sorted(glob.glob(os.path.join(parts, 'part_*.npz')))
    for f in existing:
        done |= set(np.load(f)['genome_id'].astype(str))
    paths = [p for p in genome_files(folder) if genome_id(p) not in done]
    print(f'[kmers] {len(done):,} genomes already in {len(existing)} parts, {len(paths):,} to count')
    t0, n_part = time.time(), len(existing)
    with Pool(workers) as pool:
        for start in range(0, len(paths), part_size):
            batch = paths[start:start + part_size]
            rows = list(pool.imap(genome_features, batch, chunksize=4))
            n_part += 1
            out = os.path.join(parts, f'part_{n_part:04d}.npz')
            save(out, *zip(*rows))
            n = start + len(batch)
            rate = n / (time.time() - t0)
            print(f'[kmers] {n:,}/{len(paths):,} counted, {os.path.basename(out)} saved, '
                  f'about {(len(paths) - n) / rate / 60:.0f} min left')


def merge(parts, out, existing=None):
    """One cache from the parts (and an existing cache): the format
    load_counts() reads. A genome in more than one file is kept once."""
    files = ([existing] if existing else []) + sorted(glob.glob(os.path.join(parts, 'part_*.npz')))
    ids, counts, lengths, gcs, seen = [], [], [], [], set()
    for f in files:
        z = np.load(f)
        keep = [i for i, g in enumerate(z['genome_id'].astype(str)) if g not in seen]
        seen |= set(z['genome_id'].astype(str)[keep])
        ids += list(z['genome_id'].astype(str)[keep])
        counts.append(z['counts'][keep])
        lengths.append(z['length'][keep])
        gcs.append(z['gc'][keep])
    save(out, ids, list(np.concatenate(counts)), np.concatenate(lengths), np.concatenate(gcs))
    print(f'[kmers] {len(ids):,} genomes from {len(files)} files written to {out}')


def load_counts(path=CACHE):
    if not os.path.exists(path):
        raise FileNotFoundError(f'{path} missing: run python experiments/genome/kmers.py')
    z = np.load(path, allow_pickle=False)
    return z['genome_id'].astype(str), z['counts'], z['length'], z['gc']


def kmer_names(k):
    names = ['']
    for _ in range(k):
        names = [n + b for n in names for b in BASES]
    return names


def kmer_matrix(counts6, k=4, canonical=False):
    """(n_genomes, 4**k) k-mer frequencies from 6-mer counts, plus column names.

    Frequencies (counts / total) make genomes of different lengths comparable,
    which is what the shipped model used.

    canonical=True would merge each k-mer with its reverse complement (AAAC
    with GTTT): a contig's strand is arbitrary, so the two are the same
    sequence read from either end. Not implemented yet; see the TODO.
    """
    if not 1 <= k <= K_MAX:
        raise ValueError(f'k must be 1..{K_MAX}')
    c = counts6.reshape((-1,) + (4,) * K_MAX).sum(axis=tuple(range(1 + k, 1 + K_MAX)))
    c = c.reshape(len(counts6), 4 ** k).astype(np.float64)
    names = [f'k{k}_{n}' for n in kmer_names(k)]
    if canonical:
        # TODO(Hamza, B3): merge each k-mer with its reverse complement.
        # 1. complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        # 2. rc(s) = ''.join(complement[b] for b in reversed(s))
        # 3. keep one column per pair {s, rc(s)} (the alphabetically smaller),
        #    summing the two columns' counts; palindromes (s == rc(s)) stay as is
        # k=4 goes from 256 columns to 136. Then add "canonical": true to a
        # config and compare with B1 on the same split.
        raise NotImplementedError('canonical k-mers: see the TODO in kmer_matrix()')
    total = c.sum(axis=1, keepdims=True)
    freq = np.divide(c, total, out=np.zeros_like(c), where=total > 0)
    return freq.astype(np.float32), names


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Build the 6-mer count cache')
    ap.add_argument('--limit', type=int, help='only the first N genomes (test)')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--genomes', help='folder of .fna / .fna.gz files, any depth (with --parts)')
    ap.add_argument('--parts', help='folder for resumable part files; counts --genomes into it')
    ap.add_argument('--part-size', type=int, default=2000)
    ap.add_argument('--merge', help='an existing cache to merge the parts with')
    ap.add_argument('--out', help='merged cache to write from --parts (and --merge)')
    args = ap.parse_args()
    if args.parts:
        if args.genomes:
            build_parts(args.genomes, args.parts, args.part_size, args.workers)
        if args.out:
            merge(args.parts, args.out, args.merge)
    else:
        build(args.limit, args.workers)
