# Gene matrix summary

Written by `build_gene_matrix.py`; regenerate it with the matrix. AMRFinderPlus 4.2.7, database 2026-08-07.1. Only Scope = core, Type = AMR elements are counted.

## Genes found

| | Count |
|---|---|
| Genomes searched | 2,587 |
| Genomes with at least one gene or mutation | 1,673 (64.7%) |
| Genomes with none (searched, nothing found) | 914 (35.3%) |
| Different genes and mutations (matrix columns) | 536: 309 genes, 227 point mutations |
| Hits (cells that are 1) | 12,942 of 1,386,632 (0.9%) |

## Genes per genome

Median 2, mean 5.0, maximum 30.

| Genes and mutations | Genomes | Share |
|---|---|---|
| 0 | 914 | 35.3% |
| 1 | 374 | 14.5% |
| 2 | 147 | 5.7% |
| 3 to 5 | 280 | 10.8% |
| 6 to 10 | 380 | 14.7% |
| 11 to 20 | 405 | 15.7% |
| 21 or more | 87 | 3.4% |

## Join with the labels

- Every Genome ID in `Data/mapped_output/` has a row: **yes** (2,567 of 2,567).
- Matrix genomes with no rows in `Data/mapped_output/`: 20 (1055537.30, 1055537.40, 1055537.50, 1055537.60, 108619.170 ...).

## Drug classes

| Class | Genomes with a gene | Genes and mutations |
|---|---|---|
| Beta-Lactam | 1,060 (41.0%) | 192 |
| Aminoglycoside | 1,015 (39.2%) | 61 |
| Tetracycline | 706 (27.3%) | 13 |
| Quinolone | 690 (26.7%) | 54 |
| Fosfomycin | 634 (24.5%) | 23 |
| Sulfonamide | 502 (19.4%) | 9 |
| Trimethoprim | 375 (14.5%) | 18 |
| Macrolide/Streptogramin | 285 (11.0%) | 4 |
| Phenicol | 267 (10.3%) | 18 |
| Lincosamide/Macrolide | 200 (7.7%) | 2 |
| Macrolide | 195 (7.5%) | 11 |
| Bleomycin | 181 (7.0%) | 2 |

## Most common genes and mutations

| Gene | Type | Class | Genomes |
|---|---|---|---|
| `aph(6)-Id` | gene | Aminoglycoside | 376 (14.5%) |
| `aph(3'')-Ib` | gene | Aminoglycoside | 367 (14.2%) |
| `tet(A)` | gene | Tetracycline | 354 (13.7%) |
| `sul2` | gene | Sulfonamide | 344 (13.3%) |
| `blaTEM-1` | gene | Beta-Lactam | 314 (12.1%) |
| `sul1` | gene | Sulfonamide | 285 (11.0%) |
| `fosA7` | gene | Fosfomycin | 240 (9.3%) |
| `fosB` | gene | Fosfomycin | 208 (8.0%) |
| `mecA` | gene | Beta-Lactam | 206 (8.0%) |
| `blaI` | gene | Beta-Lactam | 203 (7.8%) |
| `mecR1` | gene | Beta-Lactam | 200 (7.7%) |
| `aac(6')-I` | gene | Aminoglycoside | 197 (7.6%) |
| `blaR1` | gene | Beta-Lactam | 195 (7.5%) |
| `msr(C)` | gene | Macrolide/Streptogramin | 194 (7.5%) |
| `gyrA_S83L` | point mutation | Quinolone | 193 (7.5%) |

## Most common genes per genus

| Genus | Genomes | With a gene | Median | Most common (share of the genus) |
|---|---|---|---|---|
| *Escherichia* | 987 | 55.8% | 1 | `blaTEM-1` 22%, `aph(6)-Id` 21%, `aph(3'')-Ib` 21%, `sul2` 20%, `gyrA_S83L` 20% |
| *Salmonella* | 913 | 52.5% | 1 | `fosA7` 26%, `tet(A)` 22%, `aph(3'')-Ib` 14%, `aph(6)-Id` 14%, `floR` 13% |
| *Staphylococcus* | 227 | 100.0% | 14 | `fosB` 92%, `mecA` 91%, `blaI` 89%, `mecR1` 88%, `blaR1` 86% |
| *Enterococcus* | 202 | 98.0% | 17 | `aac(6')-I` 98%, `msr(C)` 96%, `pbp5_N496K` 91%, `liaR_E75K` 72%, `vanZ-A` 66% |
| *Klebsiella* | 78 | 89.7% | 9.5 | `oqxA` 67%, `sul1` 62%, `oqxB` 62%, `aph(3')-Ia` 47%, `blaTEM-1` 40% |
| *Streptococcus* | 53 | 58.5% | 1 | `pbp2b_T446A` 34%, `pbp2b` 34%, `msr(D)` 32%, `pbp2b_E476G` 32%, `mef(A)` 32% |
| *Acinetobacter* | 48 | 91.7% | 10.5 | `ant(3'')-IIa` 73%, `gyrA_S81L` 71%, `tet(B)` 52%, `parC_S84L` 52%, `aph(6)-Id` 48% |
| *Pseudomonas* | 37 | 100.0% | 8 | `fosA` 100%, `catB7` 100%, `aph(3')-IIb` 97%, `nalC_G71E` 92%, `nalC_S209R` 81% |
| *Mycobacterium* | 22 | 100.0% | 3 | `erm(37)` 100%, `blaC` 100%, `aac(2')-Ic` 100% |
| *Campylobacter* | 8 | 100.0% | 1.5 | `blaOXA-193` 75%, `gyrA_T86I` 25%, `cmeB` 25%, `blaOXA-61_G-57T` 12%, `blaOXA-460` 12% |
| *Enterobacter* | 5 | 80.0% | 4 | `oqxB` 80%, `oqxA` 80%, `fosA` 60%, `blaACT` 40%, `blaACT-115` 20% |
| *Shigella* | 4 | 50.0% | 0.5 | `catA1` 25%, `rpsL_K43R` 25%, `tet(B)` 25%, `aadA1` 25%, `sul1` 25% |
| *Corynebacterium* | 2 | 0.0% | 0 | none found |
| *Clostridioides* | 1 | 0.0% | 0 | none found |
