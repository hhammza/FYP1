# Collection year and country coverage

Genome records from the BV-BRC genome API for every Genome ID in the complete AMR export (`Data/amr_full/`), fetched 2026-11-14 by `scripts/bvbrc_download/download_genome_meta.py`. Year is `collection_year`, or else the year written in `collection_date`. Lab-tested here means at least one laboratory record in the raw export, including records with a measurement but no call, so the count is above the cleaned table's lab-tested genomes. Join `Data/genome_meta/genome_meta.csv` on Genome ID (as text) for the cleaned set.

## Coverage

| | All genomes | Lab-tested genomes |
| --- | --- | --- |
| Genomes | 449,320 | 123,503 |
| Found in the genome API | 449,286 (100.0%) | 123,483 (100.0%) |
| With a year | 367,240 (81.7%) | 100,357 (81.3%) |
|   year from collection_year | 321,831 (71.6%) | 68,784 (55.7%) |
|   year from collection_date only | 45,409 (10.1%) | 31,573 (25.6%) |
| With a country | 387,088 (86.1%) | 104,330 (84.5%) |
| With a host | 238,651 (53.1%) | 60,289 (48.8%) |
| With a year and a country | 355,197 (79.1%) | 99,296 (80.4%) |

## Lab-tested genomes by collection year

| Years | Genomes | Share |
| --- | --- | --- |
| before 2000 | 3,934 | 3.9% |
| 2000 to 2004 | 7,757 | 7.7% |
| 2005 to 2009 | 25,250 | 25.2% |
| 2010 to 2012 | 17,120 | 17.1% |
| 2013 to 2015 | 23,721 | 23.6% |
| 2016 to 2017 | 11,850 | 11.8% |
| 2018 to 2019 | 8,513 | 8.5% |
| 2020 to 2021 | 2,012 | 2.0% |
| 2022 to 2023 | 200 | 0.2% |
| 2024 on | 0 | 0.0% |

Median year 2012. A temporal split needs enough lab-tested genomes on both sides of the cut-off; the table shows where that holds.

## Lab-tested genomes by country (top 15)

| Country | Genomes |
| --- | --- |
| USA | 22,195 |
| United Kingdom | 14,154 |
| Australia | 8,123 |
| Canada | 5,866 |
| South Africa | 5,836 |
| Japan | 4,826 |
| Thailand | 4,290 |
| Norway | 4,209 |
| China | 3,295 |
| India | 3,052 |
| Germany | 2,411 |
| Russia | 1,906 |
| Peru | 1,531 |
| Israel | 1,383 |
| Italy | 1,373 |
