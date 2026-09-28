# Gene matrix summary

Written by `build_gene_matrix.py`; regenerate it with the matrix. AMRFinderPlus 4.2.7, database 2026-08-07.1. Only Scope = core, Type = AMR elements are counted.

## Genes found

| | Count |
|---|---|
| Genomes searched | 24,926 |
| Genomes with at least one gene or mutation | 22,949 (92.1%) |
| Genomes with none (searched, nothing found) | 1,977 (7.9%) |
| Different genes and mutations (matrix columns) | 2,733: 1,234 genes, 1,499 point mutations |
| Hits (cells that are 1) | 244,825 of 68,122,758 (0.4%) |

## Genes per genome

Median 9, mean 9.8, maximum 37.

| Genes and mutations | Genomes | Share |
|---|---|---|
| 0 | 1,977 | 7.9% |
| 1 | 1,305 | 5.2% |
| 2 | 1,041 | 4.2% |
| 3 to 5 | 3,428 | 13.8% |
| 6 to 10 | 6,316 | 25.3% |
| 11 to 20 | 9,560 | 38.4% |
| 21 or more | 1,299 | 5.2% |

## Join with the labels

- Every Genome ID in `Data/mapped_output/` has a row: **yes** (2,587 of 2,587).
- Matrix genomes with no rows in `Data/mapped_output/`: 22,339 (1192839.3, 1192839.4, 1192839.5, 1194162.3, 127906.64 ...).

## Drug classes

| Class | Genomes with a gene | Genes and mutations |
|---|---|---|
| Beta-Lactam | 19,959 (80.1%) | 1475 |
| Sulfonamide | 14,494 (58.1%) | 18 |
| Quinolone | 12,911 (51.8%) | 134 |
| Tetracycline | 12,695 (50.9%) | 43 |
| Aminoglycoside | 12,485 (50.1%) | 136 |
| Fosfomycin | 8,844 (35.5%) | 38 |
| Trimethoprim | 7,501 (30.1%) | 48 |
| Phenicol | 6,494 (26.1%) | 28 |
| Nitrofuran/Phenicol/Quinolone/Tetracycline | 6,127 (24.6%) | 73 |
| Macrolide | 5,387 (21.6%) | 30 |
| Beta-Lactam/Macrolide/Tetracycline | 4,502 (18.1%) | 6 |
| Rifamycin | 2,922 (11.7%) | 24 |

## Most common genes and mutations

| Gene | Type | Class | Genomes |
|---|---|---|---|
| `fosA` | gene | Fosfomycin | 7,566 (30.4%) |
| `oqxA` | gene | Nitrofuran/Phenicol/Quinolone/Tetracycline | 6,072 (24.4%) |
| `sul1` | gene | Sulfonamide | 5,843 (23.4%) |
| `aph(6)-Id` | gene | Aminoglycoside | 5,499 (22.1%) |
| `aph(3'')-Ib` | gene | Aminoglycoside | 5,481 (22.0%) |
| `penA_A510V` | point mutation | Beta-Lactam | 5,338 (21.4%) |
| `penA_F504L` | point mutation | Beta-Lactam | 5,338 (21.4%) |
| `folP_R228S` | point mutation | Sulfonamide | 5,227 (21.0%) |
| `sul2` | gene | Sulfonamide | 5,000 (20.1%) |
| `blaTEM-1` | gene | Beta-Lactam | 4,755 (19.1%) |
| `rpsJ_V57M` | point mutation | Tetracycline | 4,637 (18.6%) |
| `penA_D346DD` | point mutation | Beta-Lactam | 4,445 (17.8%) |
| `penA_A516G` | point mutation | Beta-Lactam | 4,290 (17.2%) |
| `parC_S80I` | point mutation | Quinolone | 4,114 (16.5%) |
| `oqxB` | gene | Nitrofuran/Phenicol/Quinolone/Tetracycline | 3,826 (15.3%) |

## Most common genes per genus

| Genus | Genomes | With a gene | Median | Most common (share of the genus) |
|---|---|---|---|---|
| *Klebsiella* | 6,213 | 99.8% | 16 | `fosA` 93%, `oqxA` 91%, `oqxB` 55%, `parC_S80I` 54%, `sul1` 43% |
| *Neisseria* | 5,823 | 98.6% | 10 | `penA_A510V` 92%, `penA_F504L` 92%, `folP_R228S` 90%, `rpsJ_V57M` 80%, `penA_D346DD` 76% |
| *Salmonella* | 2,600 | 65.1% | 1 | `sul1` 24%, `tet(A)` 19%, `floR` 16%, `fosA7` 16%, `aph(6)-Id` 16% |
| *Shigella* | 2,383 | 97.3% | 9 | `dfrA1` 78%, `sat2` 78%, `sul2` 69%, `aph(6)-Id` 67%, `aph(3'')-Ib` 66% |
| *Acinetobacter* | 1,598 | 98.6% | 12 | `ant(3'')-IIa` 96%, `gyrA_S81L` 86%, `parC_S84L` 74%, `sul1` 54%, `aph(6)-Id` 54% |
| *Pseudomonas* | 1,428 | 100.0% | 10 | `fosA` 99%, `aph(3')-IIb` 99%, `catB7` 98%, `nalC_G71E` 94%, `nalC_S209R` 68% |
| *Escherichia* | 987 | 55.8% | 1 | `blaTEM-1` 22%, `aph(6)-Id` 21%, `aph(3'')-Ib` 21%, `sul2` 20%, `gyrA_S83L` 20% |
| *Campylobacter* | 868 | 96.9% | 2 | `tet(O)` 71%, `blaOXA-193` 67%, `gyrA_T86I` 25%, `aph(3')-IIIa` 24%, `blaOXA-61_G-57T` 20% |
| *Streptococcus* | 649 | 52.4% | 1 | `tet(M)` 27%, `erm(A)` 17%, `mef(A)` 16%, `pbp2b` 16%, `pbp2b_E476G` 16% |
| *Staphylococcus* | 540 | 99.4% | 11 | `blaI` 89%, `blaR1` 78%, `mecA` 74%, `fosB` 74%, `blaZ` 61% |
| *Enterobacter* | 447 | 98.4% | 13 | `oqxB` 94%, `oqxA` 94%, `fosA` 85%, `blaTEM-1` 47%, `aph(6)-Id` 42% |
| *Clostridioides* | 375 | 99.5% | 4 | `blaAHM` 98%, `blaCDD` 89%, `mreE_V497L` 45%, `gyrA_T82I` 44%, `PnimB_G` 41% |
| *Enterococcus* | 342 | 98.8% | 13 | `tet(M)` 68%, `erm(B)` 67%, `vanZ-A` 62%, `vanY-A` 61%, `vanR-A` 61% |
| *Citrobacter* | 115 | 100.0% | 14 | `gyrA_T83I` 67%, `sul1` 66%, `blaTEM-1` 52%, `mph(A)` 43%, `mrx(A)` 43% |
| *Corynebacterium* | 97 | 95.9% | 7 | `pbp2m` 90%, `erm(X)` 90%, `aac(3)-XI` 90%, `sul1` 66%, `tet(W)` 61% |
| *Vibrio* | 92 | 100.0% | 10 | `almF` 100%, `almE` 100%, `almG` 100%, `varG` 82%, `catB9` 71% |
| *Haemophilus* | 88 | 40.9% | 0 | `folP_G189C` 19%, `ftsI_D350N` 18%, `blaTEM-1` 14%, `rpoB_A1131T` 12%, `ftsI_N526K` 12% |
| *Burkholderia* | 66 | 98.5% | 2 | `blaPEN-bcc` 83%, `penR_V151E` 80%, `blaPEN-A` 6%, `tet(64)` 5%, `blaPEN-B` 5% |
| *Helicobacter* | 53 | 60.4% | 1 | `gyrA_N87K` 23%, `gyrA_D91N` 19%, `gyrA_D91G` 9%, `gyrA_D91Y` 9%, `pbp1a_S543R` 8% |
| *Serratia* | 34 | 82.4% | 3 | `aac(6')` 65%, `blaSRT` 53%, `tet(41)` 38%, `blaSME-4` 24%, `blaSRT-2` 18% |
| *Mycobacterium* | 33 | 100.0% | 3 | `blaC` 100%, `erm(37)` 100%, `aac(2')-Ic` 100% |
| *Proteus* | 25 | 96.0% | 20 | `tet(J)` 96%, `sul1` 88%, `catA4` 88%, `dfrA1` 84%, `aadA1` 76% |
| *Aliarcobacter* | 22 | 63.6% | 1 | `blaOXA` 50%, `blaOXA-464` 9%, `blaOXA-491` 5% |
| *Stutzerimonas* | 19 | 73.7% | 8 | `tmexC` 63%, `sul1` 63%, `aadA1` 58%, `toprJ1` 47%, `cmlA5` 42% |
| *Morganella* | 8 | 100.0% | 21 | `sul1` 88%, `mrx(A)` 75%, `dfrA17` 75%, `catA2` 75%, `mph(A)` 75% |
| *Mycolicibacterium* | 7 | 100.0% | 3 | `blaC` 100%, `erm(37)` 100%, `aac(2')-Ic` 100% |
| *Providencia* | 3 | 100.0% | 5 | `blaNDM-1` 67%, `tet(B)` 67%, `catA3` 67%, `sul1` 67%, `aadA36` 67% |
| *Listeria* | 2 | 100.0% | 2 | `vga(G)` 100%, `fosX` 100% |
| *unknown* | 2 | 100.0% | 8 | `blaC` 50%, `blaVIM-1` 50%, `aph(6)-Id` 50%, `aph(3'')-Ib` 50%, `blaACT` 50% |
| *Achromobacter* | 1 | 100.0% | 1 | `blaOXA-114w` 100% |
| *Mycolicibacillus* | 1 | 100.0% | 3 | `blaC` 100%, `erm(37)` 100%, `aac(2')-Ic` 100% |
| *Yersinia* | 1 | 0.0% | 0 | none found |
| *Kluyvera* | 1 | 100.0% | 7 | `aac(6')-Ib'` 100%, `aadA1` 100%, `blaOXA` 100%, `qnrB19` 100%, `blaKPC-3` 100% |
| *Aeromonas* | 1 | 100.0% | 10 | `blaOXA-956` 100%, `aac(6')-Ia` 100%, `cmlA5` 100%, `ant(2'')-Ia` 100%, `cphA` 100% |
| *Leclercia* | 1 | 100.0% | 2 | `fosA8` 100%, `blaOXA-48` 100% |
| *Desulfovibrio* | 1 | 0.0% | 0 | none found |
