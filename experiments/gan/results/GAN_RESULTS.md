# GAN experiment (A13): CTGAN training rows for rare drugs and organisms

Built by `experiments/gan/ctgan_augment.py`. Base model A6 (lab-confirmed rows, the forecaster's features, split by genome). CTGAN was fitted on A6's **training** rows of rare antibiotics or genera (under 1,000 training rows each: 62 antibiotics, 21 genera; 21,030 rows, 21,030 used to fit, 60 epochs). 21,030 synthetic rows were added to A13's training side; the test set is real and identical to A6's.

## Quality of the synthetic rows

- Detection test: a classifier separating real from synthetic rows reaches AUC **0.9999** (0.5 = indistinguishable, 1.0 = obvious fakes).
- MIC distribution, Kolmogorov-Smirnov distance: 0.2916.
- Category distributions, total variation distance per column: Antibiotic 0.415, drug_class 0.2614, genus 0.3705, species 0.3975, taxon 0.4364, mic_sign 0.3325, has_mic 0.2778, target 0.0302.
- 17% of sampled rows kept: the rest paired a drug with another drug's class or a species with another genus.

## Effect on the model (same real test rows)

| Test rows | Rows (genomes) | AUC A13 (with GAN rows) | AUC A6 (without) | Difference | Genome bootstrap 95% CI | DeLong p |
|---|---|---|---|---|---|---|
| all test rows | 129,992 (17,542) | 0.9222 | 0.9227 | -0.0005 | [-0.0007, -0.0002] | < 0.0001 |
| rare antibiotics or genera | 5,083 (2,530) | 0.9323 | 0.9402 | -0.0080 | [-0.0115, -0.0048] | < 0.0001 |
