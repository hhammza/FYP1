# Cleaned data: v5 vs v6

v5: the April export (`Data/amr_output/`). v6: the complete export (`Data/amr_full/`, 2026-09-29). Same cleaning code; only the raw export differs.

Built by `experiments/audit/compare_clean_versions.py`.

## Overall

| | v5 | v6 | Change |
| --- | --- | --- | --- |
| Rows | 1,558,494 | 7,847,110 | x5.04 |
| Genomes | 131,385 | 439,542 | x3.35 |
| Lab rows | 201,042 | 649,944 | x3.23 |
| Lab-tested genomes | 22,475 | 87,325 | x3.89 |
| Antibiotics | 130 | 126 | x0.97 |
| Genera | 40 | 40 | x1.00 |
| Species taxa | 124 | 247 | x1.99 |
| Resistant share, all rows | 36.5% | 28.0% | -8.4 points |
| Resistant share, lab rows | 49.5% | 33.7% | -15.8 points |
| Rows with an MIC | 6.7% | 2.8% | -3.9 points |
| Lab share of rows | 12.9% | 8.3% | -4.6 points |

## Does the new export contain the old one?

| Check | Count |
| --- | --- |
| v5 genomes also in v6 | 130,389 of 131,385 |
| v5 genomes missing from v6 | 996 |
| v5 genome and drug pairs also in v6 | 1,543,808 of 1,558,494 |
| v5 lab pairs missing from v6 | 0 of 201,042 |
| Pairs whose label changed | 1,665 |
| Pairs that became lab-confirmed | 0 |

## All rows by genus (top 15 in v6)

| Genus | v5 | v6 |
| --- | --- | --- |
| *Escherichia* | 75,182 | 3,562,956 |
| *Salmonella* | 353,228 | 1,083,062 |
| *Mycobacterium* | 4,904 | 979,138 |
| *Klebsiella* | 452,426 | 703,539 |
| *Staphylococcus* | 8,840 | 366,887 |
| *Streptococcus* | 4,856 | 278,820 |
| *Pseudomonas* | 193,216 | 201,192 |
| *Acinetobacter* | 176,816 | 188,090 |
| *Campylobacter* | 89,760 | 172,139 |
| *Shigella* | 78,405 | 127,323 |
| *Neisseria* | 94,462 | 99,167 |
| *Enterococcus* | 2,126 | 56,228 |
| *Clostridioides* | 11,955 | 11,958 |
| *Corynebacterium* | 683 | 5,601 |
| *Enterobacter* | 4,064 | 4,067 |

Genera in v5 but not in v6: *Pasteurella* (556), *Mycobacteroides* (6), *Cutibacterium* (10), *Stenotrophomonas* (41), *Cronobacter* (28), *Bacillus* (6)

## Lab rows by genus (top 15 in v6)

| Genus | v5 | v6 |
| --- | --- | --- |
| *Mycobacterium* | 140 | 130,555 |
| *Salmonella* | 22,332 | 98,212 |
| *Escherichia* | 3 | 89,350 |
| *Streptococcus* | 3,078 | 81,551 |
| *Klebsiella* | 71,188 | 78,708 |
| *Staphylococcus* | 2,968 | 43,124 |
| *Neisseria* | 28,199 | 28,199 |
| *Acinetobacter* | 22,431 | 23,406 |
| *Shigella* | 22,088 | 22,088 |
| *Enterococcus* | 826 | 20,178 |
| *Pseudomonas* | 8,801 | 9,936 |
| *Campylobacter* | 7,734 | 8,121 |
| *Corynebacterium* | 669 | 5,079 |
| *Enterobacter* | 3,869 | 4,067 |
| *Citrobacter* | 1,186 | 1,673 |
