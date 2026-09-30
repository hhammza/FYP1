# Were our BV-BRC data problems already reported?

Checked 2026-09-30 by Ali, for Paper A in `progress/RESEARCH_PLAN.md`: before we call a finding new, we look for BV-BRC (or anyone) reporting it first. Searched BV-BRC's documentation, its API documentation, the BV-BRC GitHub organisation and the literature.

## The closest prior work

**VanOeffelen M, Nguyen M, Aytan-Aktug D, Brettin T, Dietrich EM, Kenyon RW, Machi D, Mao C, Olson R, Pusch GD, Shukla M, Stevens R, Vonstein V, Warren AS, Wattam AR, Yoo H, Davis JJ (2021).** A genomic data resource for predicting antimicrobial resistance from laboratory-derived antimicrobial susceptibility phenotypes. *Briefings in Bioinformatics* 22(6), bbab313. https://doi.org/10.1093/bib/bbab313. Code and filtered tables: https://github.com/BV-BRC/AMRMetadataReview_2021

This is BV-BRC's own description of the same AMR metadata, as of November 2020: 67,817 genomes, 38 genera, 88 species, 128 compounds, 324,134 MIC records and 356,206 SIR calls from about 218 sources. What it covers and what it does not:

| Topic | In VanOeffelen 2021? | So for us |
| --- | --- | --- |
| Sampling bias (few *E. coli* with AST, *M. tuberculosis* geography, outbreak clusters, few anaerobes) | Yes | Cite it; not a new finding |
| Zone diameters (mm) stored alongside MICs | Mentioned as present | Cite it; our finding is that 8,380 lab rows carry mm in the MIC value field, which a pipeline reading `measurement_value` as an MIC gets wrong (fixed in cleaning v7) |
| Original wording of calls kept ("reduced susceptibility", "non-susceptible") | Yes | Cite it for why our phenotype map has to be explicit |
| Antibiotic name variants (196 raw names to 126) | No | New |
| Laboratory vs computational labels (16.3 M of 17.6 M rows predicted; 90.4% agreement; daptomycin 95.4% vs 10.9% resistant) | No: the paper treats all phenotypes as laboratory data | New, and the main ML point: a genome model scored on predicted labels partly re-learns BV-BRC's own predictor |
| Records with a measurement but no call (580,200 lab records) | No | New |
| Conflicting lab calls for one genome and drug (4,313 pairs) | No | New |
| Species vs strain taxon IDs (89% of rows under species-rank IDs) | No | New |
| Genome ID read as a number (16,531 genomes merge, 32,744 IDs collide) | No | New for BV-BRC; see the precedent below |
| Records removed or relabelled between downloads (996 genomes gone, 1,665 labels changed) | No | New; argues for versioned snapshots |
| A quarter of lab-tested genomes have the year only in `collection_date` (31,577 of 123,503) | No | New |

## Other sources checked

- **BV-BRC AMR documentation** ([AMR phenotypes](https://www.bv-brc.org/docs/quick_references/organisms_taxon/amr_phenotypes.html), [AMR data protocol](https://www.bv-brc.org/docs/data_protocols/antimicrobial_resistance.html), [data overview](https://www.bv-brc.org/docs/system_documentation/data.html)). It says the phenotypes are "not fully curated" and marks predicted records with the typing method "Computational Prediction" and the classifier as platform. It gives no warning against training on them. The pages sit behind a browser check, so they were read through search results; quote them from a browser before the paper.
- **BV-BRC API documentation** ([API docs](https://www.bv-brc.org/api/doc/), [Data API source](https://github.com/BV-BRC/BV-BRC-API)). It documents cursor paging (`cursor(*)` with the `X-Cursor-Mark` header) as the way to read large result sets. So the April export's truncation came from how our first script paged (a growing offset, stopping at 500,000 rows per taxon), not from a BV-BRC fault. Paper A should say "a naive offset download silently loses whole species" and not blame the API.
- **Genome ID type.** The API schema types `genome_id` as a string ("511145.183"). Nothing warns that spreadsheet or pandas defaults turn it into a number. The closest precedent is gene symbols turned into dates by Excel: Ziemann M, Eren Y, El-Osta A (2016), Gene name errors are widespread in the scientific literature, *Genome Biology* 17, 177, https://doi.org/10.1186/s13059-016-1044-7. Cite it as the same kind of error.
- **Earlier BV-BRC AMR work** (for background, none reports our issues): Davis JJ et al. (2016), Antimicrobial resistance prediction in PATRIC and RAST, *Scientific Reports* 6, 27930, https://doi.org/10.1038/srep27930; Antonopoulos DA et al. (2019), PATRIC as a unique resource for studying antimicrobial resistance, *Briefings in Bioinformatics* 20(4), 1094 to 1102, https://doi.org/10.1093/bib/bbx083; Olson RD et al. (2023), Introducing the Bacterial and Viral Bioinformatics Resource Center (BV-BRC), *Nucleic Acids Research* 51(D1), D678 to D689, https://doi.org/10.1093/nar/gkac1003.

## BV-BRC GitHub issues

Searched 2026-09-30 across the BV-BRC organisation for "genome_amr", "antibiotic", "genome_id", "measurement", "collection_year", "taxon_id", "AMR phenotype", "resistant_phenotype", "float" and "duplicate". None of the hits reports any of our problems, so none of them has an open or closed issue. One hit matters for other reasons:

- [BV-BRC-API #204](https://github.com/BV-BRC/BV-BRC-API/issues/204), "Clarify reuse terms for laboratory-method genome_amr API rows" (opened 2026-09-01, no reply yet). Another group asks whether lab-method rows may be downloaded, normalised and redistributed, and under which licence. The repository's MIT licence covers the API code, not the data. **For us:** until BV-BRC answers, publish the cleaning code and the retrieval date, not the cleaned table, or ask BV-BRC ourselves.
- The same issue names [CultureBotAI/AntibioticMech](https://github.com/CultureBotAI/AntibioticMech), a CC BY 4.0 knowledge base of antibiotic chemical structures (ChEBI, CARD ARO, PubChem, one record per structure). Read 2026-09-30: it does not yet use BV-BRC AMR rows and normalises drug structures, not phenotype rows, units, taxa or evidence types; no paper. The issue shows they plan to add BV-BRC lab rows, so check it again before submission.

## Not checked yet

- **BV-BRC help desk.** Most user reports go to help@bv-brc.org, not GitHub. Before submission, email them our list and ask whether any of it is known; their answer also serves as the acknowledgement we cite.
- **VanOeffelen 2021 full text.** The table above comes from the article page; read the PDF once to confirm nothing on names, taxon IDs or computational labels sits in the supplement.

## What this means for Paper A

The data problems nobody has reported are the antibiotic names, lab vs computational labels, measurements without calls, conflicting calls, taxon ID rank, the Genome ID type, changes between downloads and years hidden in `collection_date`. Sampling bias and the presence of zone diameters are known: cite VanOeffelen 2021 and build on them. The truncated download is our own method's failure, useful as a warning, not as a BV-BRC defect.
