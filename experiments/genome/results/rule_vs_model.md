# Gene-lookup rules vs the genes model (lab rows)

Same genomes, split and lab test rows for all three: the lab-tested genome set, cleaning v7, plasmid-only records excluded, grouped by genome (seed 42). The rules learn nothing; they read AMRFinderPlus output the way a lab would. Built by `experiments/genome/rule_vs_model.py`.

40,356 lab test rows, 4,481 genomes, 101 antibiotics, 49.7% resistant.

## Overall

| | AUC | Very major error | Major error |
| --- | --- | --- | --- |
| class rule | 0.711 | 5.2% | 52.6% |
| key rule | 0.598 | 78.3% | 2.1% |
| genes model | 0.979 | 7.9% | 6.7% |

Genes model minus class rule: AUC +0.268 [+0.261 to +0.274], paired bootstrap over genomes (1000 resamples; share of resamples with no gain 0.000). The key rule's overall AUC is low by construction: drugs without a named determinant all score 0, so compare it per drug below.

Very major error: resistant called susceptible. Major error: susceptible called resistant. Thresholds: 0.5 for the model, presence for the rules.

## By antibiotic (at least 100 lab test rows and 10 of each class)

| Antibiotic | Rows | Resistant | Class rule | Key rule | Genes model |
| --- | --- | --- | --- | --- | --- |
| ciprofloxacin | 2,989 | 49% | 0.819 | 0.695 | 0.990 |
| ceftriaxone | 2,456 | 36% | 0.585 | 0.719 | 0.998 |
| gentamicin | 2,233 | 40% | 0.678 | 0.823 | 0.970 |
| tetracycline | 2,084 | 51% | 0.662 | 0.872 | 0.945 |
| ampicillin | 1,801 | 77% | 0.960 | - | 0.993 |
| azithromycin | 1,793 | 21% | 0.699 | - | 0.983 |
| meropenem | 1,736 | 37% | 0.564 | 0.756 | 0.969 |
| ceftazidime | 1,472 | 65% | 0.574 | - | 0.973 |
| trimethoprim/sulfamethoxazole | 1,416 | 61% | 0.878 | - | 0.976 |
| amikacin | 1,351 | 34% | 0.613 | - | 0.938 |
| tobramycin | 1,133 | 60% | 0.681 | - | 0.955 |
| cefoxitin | 1,101 | 53% | 0.661 | 0.501 | 0.955 |
| levofloxacin | 972 | 70% | 0.683 | 0.599 | 0.981 |
| imipenem | 963 | 46% | 0.511 | 0.749 | 0.955 |
| aztreonam | 865 | 79% | 0.516 | - | 0.931 |
| piperacillin/tazobactam | 850 | 73% | 0.530 | - | 0.927 |
| cefotaxime | 832 | 63% | 0.731 | 0.652 | 0.989 |
| spectinomycin | 823 | 11% | 0.978 | - | 0.988 |
| penicillin | 814 | 51% | 0.579 | - | 0.929 |
| cefepime | 801 | 61% | 0.537 | - | 0.939 |
| cefazolin | 741 | 87% | 0.513 | - | 0.987 |
| chloramphenicol | 740 | 30% | 0.914 | 0.874 | 0.984 |
| nalidixic acid | 731 | 36% | 0.977 | 0.821 | 0.991 |
| ampicillin/sulbactam | 677 | 78% | 0.501 | - | 0.956 |
| trimethoprim | 562 | 61% | 0.792 | 0.962 | 0.984 |
| amoxicillin/clavulanic acid | 545 | 63% | 0.801 | - | 0.989 |
| colistin | 539 | 17% | 0.664 | 0.592 | 0.935 |
| cefixime | 529 | 7% | 0.513 | - | 0.937 |
| ertapenem | 495 | 67% | 0.668 | - | 0.967 |
| nitrofurantoin | 492 | 81% | 0.539 | - | 0.969 |
| streptomycin | 487 | 59% | 0.900 | - | 0.964 |
| cefuroxime | 481 | 90% | 0.647 | - | 0.992 |
| erythromycin | 415 | 52% | 0.851 | - | 0.993 |
| tigecycline | 404 | 26% | 0.560 | - | 0.787 |
| clindamycin | 333 | 27% | 0.839 | - | 0.962 |
| kanamycin | 177 | 44% | 0.603 | - | 0.926 |
| telithromycin | 176 | 6% | 0.955 | - | 0.997 |
| florfenicol | 175 | 6% | 0.597 | - | 1.000 |
| ceftiofur | 165 | 22% | 0.950 | - | 1.000 |
| sulfisoxazole | 138 | 21% | 0.983 | - | 0.978 |
| ticarcillin/clavulanic acid | 133 | 65% | 0.553 | - | 0.934 |
| ceftazidime/avibactam | 124 | 39% | 0.553 | - | 0.932 |
| doripenem | 122 | 57% | 0.509 | - | 0.958 |
| polymyxin b | 115 | 34% | 0.608 | - | 0.821 |
| rifampicin | 114 | 63% | 0.599 | - | 0.963 |
| moxifloxacin | 107 | 60% | 0.732 | - | 0.982 |

Genes model above the class rule on 45 of 46 drugs; above the key rule on 13 of the 13 drugs that have a named determinant. "-": no named determinant for that drug in `genes.py`.

## Context: the same lab rows without genes

Hamza's LightGBM runs on the same genomes and split with no gene columns (cleaning v6; v7 has the same rows and labels and changes only MIC values, which these runs do not use).

| Run | Inputs | Lab AUC [95% CI] |
| --- | --- | --- |
| B6L_base_drug_v6 | antibiotic only | 0.715 [0.708 to 0.720] |
| B6L_nogenes_v6 | antibiotic, drug class, genus | 0.834 [0.828 to 0.841] |
| B6L_base_taxonomy_v6 | antibiotic, genus, species | 0.849 [0.842 to 0.855] |
| B6L_genes_v7 | the genes model: antibiotic, drug class, genus, genes | 0.979 [0.977 to 0.981] |

## Limits

- The class rule counts every gene of the drug's AMRFinderPlus class, so any beta-lactamase counts against carbapenems and cephalosporins. A rule using AMRFinderPlus subclasses (or ResFinder's phenotype table) is the fairer opponent and is the next run.
- The key rule covers 16 drugs (`genes.py` KEY_DETERMINANTS).
- The model also sees antibiotic, drug class and genus, so part of its lead is intrinsic resistance by genus, which the context table above measures.
- One split (seed 42), grouped by genome, not by lineage.
