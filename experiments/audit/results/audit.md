# BV-BRC AMR export: data audit

Export downloaded 2026-09-28 19:44 to 2026-09-28 20:19 UTC from `https://www.bv-brc.org/api/genome_amr/` (36 files in `Data/amr_full/`). Every number below comes from `experiments/audit/audit_bvbrc.py`; machine-readable copy in `audit.json`.

## 1. The export

| | Lab | Computational | All |
| --- | --- | --- | --- |
| Records | 1,285,111 | 16,300,395 | 17,585,506 |
| With a usable phenotype | 704,909 (54.9%) | 8,217,718 (50.4%) | 8,922,627 (50.7%) |
| No phenotype, but a measurement | 580,200 | 8,082,677 | |

Lab records without a phenotype are measurements (mostly MICs) that BV-BRC never turned into a resistant or susceptible call; cleaning drops them, although a breakpoint table could label them.

**Where the computational labels come from:**

| Method | Rows with a label | Rows without |
| --- | --- | --- |
| MIC XGBoost Model | 0 | 8,082,677 |
| SIR XGBoost Model | 7,218,911 | 0 |
| AdaBoost Classifier | 998,807 | 0 |

## 2. The April export was incomplete

The first download (April 2026, `scripts/bvbrc_download/download_amr_csv.py`) paged each taxon by offset and stopped at 500,000 rows. Its own log:

| Status in the April log | Taxa |
| --- | --- |
| no_data | 22,175 |
| done | 3,655 |
| error | 597 |
| partial | 1 |

Rows kept in April: 2,986,755 of 17,585,506 (17.0%). Taxa stopped at the 500,000-row cap: 573.

| Taxon | April | Complete export |
| --- | --- | --- |
| 562 *Escherichia coli* | 0 (error) | 7,219,003 |
| 573 *Klebsiella pneumoniae* | 500,000 (done) | 1,814,185 |
| 28901 *Salmonella enterica* | 0 (error) | 960,834 |
| 1280 *Staphylococcus aureus* | 0 (error) | 527,038 |

**Effect on the cleaned data** (v5 = April export, v7 = complete export; the cleaning differs only in v7 treating mm values as no MIC):

| | v5 | v7 |
| --- | --- | --- |
| Rows | 1,558,494 | 7,847,110 |
| Genomes | 131,385 | 439,542 |
| Lab rows | 201,042 | 649,944 |
| Lab-tested genomes | 22,475 | 87,325 |
| Antibiotics | 130 | 126 |
| Genera | 40 | 40 |
| Species taxa | 124 | 247 |
| Resistant share, all rows | 36.5% | 28.0% |
| Resistant share, lab rows | 49.5% | 33.7% |
| Rows with an MIC | 6.7% | 2.7% |
| Lab share of rows | 12.9% | 8.3% |

Between the two downloads BV-BRC removed 996 genomes and changed 1,665 labels, so an export must be dated to be reproducible.

## 3. Identifiers

| Genome ID read as a number instead of text | Count |
| --- | --- |
| Genome IDs | 449,320 |
| IDs that collide with another ID | 32,744 |
| Genomes lost by merging | 16,531 |
| IDs ending in 0 after the dot (lose it as a number) | 43,596 |

Example collision: 195.304 and 195.3040.

## 4. Taxonomy

| | Count |
| --- | --- |
| Taxon IDs in the export | 13,042 |
| of which species rank | 442 |
| of which strain, serotype or other sub-species rank | 12,597 |
| Species they belong to | 449 |
| Rows filed under a species-rank ID | 15,673,212 of 17,585,246 (89.1%) |
| *E. coli*: taxon IDs | 2,423 |
| *E. coli*: rows under 562 itself, and under all its IDs | 7,219,003 of 7,466,275 |

Most taxon IDs are strains or serotypes, but most rows are filed under a species ID. The April export looked the other way round (3,224 of its 3,655 taxa were strains, and *E. coli* 562 never appeared) only because its species-level downloads failed (section 2).

## 5. Antibiotic names

| | Count |
| --- | --- |
| Distinct names (lower-cased) | 196 |
| Distinct names on rows with a phenotype | 156 |
| After the alias map | 126 |
| Names renamed (spelling variants) | 31 (1,234,613 rows, 683,730 with a phenotype) |
| Names dropped (not a drug) | 10 (45,167 rows) |

Renamed, for example: amipicillin_sulbactam, amoxicillin_clavulanat, ampicillin_clavulanic_acid, cefalexin, cefalothin, cefalotin, cefepime_taniborbactam, cefotaxime/clavulanic acidâ. Dropped, for example: aminogycosides, beta-lactam, carbapenem, cephalosporin, extended spectrum beta lactamase, fluoroquinolones, instrument, macrolides.

## 6. Measurements and testing standards (rows with a phenotype)

| | Count |
| --- | --- |
| Lab rows with a measurement | 239,859 of 704,909 (34.0%) |
| Computational rows with a measurement | 0 of 8,217,718 (0.0%) |
| Lab rows with unit "(none)" | 468,637 |
| Lab rows with unit "mg/L" | 227,892 |
| Lab rows with unit "mm" | 8,380 |
| Lab rows with no testing standard | 232,793 |
| Lab rows with no testing standard year | 390,746 |

Testing standards as written (lab rows): "CLSI" 250,190, "(none)" 232,793, "EUCAST" 123,234, "clsi" 31,879, "Australian Gonococcal Surveillance Programme (AGSP)" 12,918, "WHO: Guidelines for Surveillance of Drug Resistance in Tuberculosis" 10,805, "eucast" 9,521, "clsi_non-meningitis" 6,743.

Rows measured in mm are disk-diffusion zone diameters, not MICs; the cleaning (`data_prep.clean`) currently reads their number as an MIC.

## 7. Duplicates, conflicts and computational vs lab labels

| | Count |
| --- | --- |
| Rows with a phenotype | 8,922,627 |
| Genome and drug pairs | 7,891,714 |
| Rows removed by one-row-per-pair | 1,030,913 |
| Lab pairs tested more than once | 41,389 |
| Lab pairs with conflicting results | 4,313 |
| Pairs with both a lab and a computational label | 463,429 |
| Computational label agrees with the lab | 418,746 (90.4%) |
| Computational says susceptible, lab says resistant | 25,888 |
| Computational says resistant, lab says susceptible | 18,795 |

Pairs whose lab results conflict with each other, or whose computational results do, are left out of the agreement count.

## 8. The cleaned data (v7) by genus, drug class and drug

| Genus | Rows | Genomes | Resistant | Lab rows | Lab resistant |
| --- | --- | --- | --- | --- | --- |
| *Escherichia* | 3,562,956 | 114,614 | 24.8% | 89,350 | 24.8% |
| *Salmonella* | 1,083,062 | 53,552 | 15.1% | 98,212 | 19.7% |
| *Mycobacterium* | 979,138 | 46,606 | 21.9% | 130,555 | 27.3% |
| *Klebsiella* | 703,539 | 40,374 | 47.3% | 78,708 | 64.7% |
| *Staphylococcus* | 366,887 | 30,162 | 44.1% | 43,124 | 29.4% |
| *Streptococcus* | 278,820 | 33,251 | 23.8% | 81,551 | 26.1% |
| *Pseudomonas* | 201,192 | 16,385 | 35.6% | 9,936 | 48.5% |
| *Acinetobacter* | 188,090 | 16,265 | 72.1% | 23,406 | 80.6% |
| *Campylobacter* | 172,139 | 45,641 | 31.9% | 8,121 | 20.0% |
| *Shigella* | 127,323 | 12,323 | 46.1% | 22,088 | 44.9% |
| *Neisseria* | 99,167 | 15,002 | 23.6% | 28,199 | 18.7% |
| *Enterococcus* | 56,228 | 9,247 | 39.0% | 20,178 | 46.3% |
| *Clostridioides* | 11,958 | 3,939 | 32.3% | 427 | 41.2% |
| *Corynebacterium* | 5,601 | 862 | 24.8% | 5,079 | 18.6% |
| *Enterobacter* | 4,067 | 468 | 71.7% | 4,067 | 71.7% |

| Drug class | Rows | Genomes | Resistant | Lab rows | Lab resistant |
| --- | --- | --- | --- | --- | --- |
| beta_lactam | 2,543,083 | 336,544 | 27.2% | 171,168 | 43.3% |
| fluoroquinolone | 1,109,746 | 392,017 | 29.3% | 62,150 | 38.9% |
| aminoglycoside | 1,050,925 | 343,603 | 25.4% | 89,563 | 27.1% |
| sulfonamide | 702,819 | 300,325 | 35.5% | 44,662 | 42.9% |
| carbapenem | 544,596 | 199,937 | 18.3% | 34,109 | 26.3% |
| tetracycline | 487,772 | 356,605 | 43.8% | 42,155 | 36.8% |
| antitubercular | 466,695 | 46,606 | 24.1% | 71,919 | 25.5% |
| macrolide | 223,423 | 157,417 | 24.9% | 36,186 | 25.6% |
| phenicol | 212,592 | 212,525 | 17.8% | 22,824 | 15.0% |
| monobactam | 170,907 | 170,907 | 28.4% | 5,829 | 68.4% |
| rifamycin | 96,413 | 49,987 | 31.3% | 28,789 | 29.7% |
| lincosamide | 71,124 | 71,124 | 26.9% | 7,046 | 33.8% |
| oxazolidinone | 59,355 | 59,355 | 4.7% | 7,396 | 4.2% |
| lipopeptide | 28,844 | 28,844 | 95.4% | 1,484 | 10.9% |
| fusidane | 27,936 | 27,936 | 10.6% | 2,604 | 15.7% |

Largest gaps between the resistant share of all rows (mostly computational) and of lab rows: lipopeptide 95.4% vs 10.9%, monobactam 28.4% vs 68.4%, beta_lactam 27.2% vs 43.3%.

| Antibiotic | Rows | Genomes | Resistant | Lab rows | Lab resistant |
| --- | --- | --- | --- | --- | --- |
| ciprofloxacin | 384,651 | 384,651 | 30.3% | 33,809 | 39.0% |
| tetracycline | 355,282 | 355,282 | 39.5% | 31,491 | 43.3% |
| gentamicin | 293,955 | 293,955 | 21.5% | 29,704 | 24.3% |
| trimethoprim/sulfamethoxazole | 286,261 | 286,261 | 37.7% | 31,097 | 47.9% |
| cefoxitin | 243,797 | 243,797 | 20.9% | 11,060 | 47.2% |
| levofloxacin | 236,292 | 236,292 | 33.3% | 9,566 | 56.3% |
| streptomycin | 230,492 | 230,492 | 46.8% | 17,218 | 36.5% |
| nalidixic acid | 220,550 | 220,550 | 31.2% | 8,080 | 33.5% |
| chloramphenicol | 211,557 | 211,557 | 17.9% | 21,789 | 15.4% |
| ceftriaxone | 194,143 | 194,143 | 21.5% | 18,030 | 30.4% |
| meropenem | 193,397 | 193,397 | 19.6% | 19,661 | 18.2% |
| tobramycin | 192,918 | 192,918 | 26.4% | 7,778 | 52.6% |
| ampicillin | 189,448 | 189,448 | 41.5% | 24,243 | 60.7% |
| cefotaxime | 187,933 | 187,933 | 22.3% | 16,811 | 29.3% |
| imipenem | 187,230 | 187,230 | 21.2% | 7,953 | 33.7% |
| trimethoprim | 184,322 | 184,322 | 35.2% | 7,768 | 33.5% |
| amoxicillin/clavulanic acid | 179,036 | 179,036 | 22.5% | 10,525 | 37.4% |
| cefepime | 172,509 | 172,509 | 24.7% | 7,334 | 41.7% |
| aztreonam | 170,907 | 170,907 | 28.4% | 5,829 | 68.4% |
| piperacillin/tazobactam | 170,713 | 170,713 | 20.6% | 11,026 | 36.0% |
