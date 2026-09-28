# Evolution timeline experiments (T3.1)

Checks on the mutation timeline that `/timeline` serves (`backend/ml_models/mutation_timeline.py`). The timeline is a simulation with hand-set numbers per antibiotic, not a trained model, so these experiments ask how much its answers depend on those numbers and whether they match published data.

Run from the project root with the project's Python:

```bash
.venv/bin/python experiments/evolution/sensitivity.py     # seconds
```

## How the timeline works

The share of resistant bacteria in week *t* follows a logistic curve:

```
R(t) = r0 + (peak - r0) / (1 + exp(-k (t - midpoint)))
```

| Input | Where it comes from |
| --- | --- |
| `speed` | hand-set per drug; slope k = 2.5 x speed |
| `peak` | hand-set per drug; the highest share resistance can reach |
| `r0` | starting share, from the genome's GC content: \|GC - 0.5\| x 0.3, kept between 2% and 15% |
| `midpoint` | 0.45 x the number of weeks the user asks for |

Treatment "fails" in the first week R reaches 50%.

## 1. Sensitivity analysis (`sensitivity.py`)

Scales `speed` and `peak` from 0.7 to 1.3 of their hand-set values, and varies the weeks asked (8, 12, 26, 52) and GC content (0.35, 0.50, 0.65), for all 14 profiles: 8,232 combinations. It calls the backend's own `generate_timeline`, and checks on every combination that the served failure week matches the exact crossing time from the formula.

Outputs in `results/`:

| File | What it holds |
| --- | --- |
| `sensitivity.csv` | every combination: inputs, failure week, exact crossing week, and whether it fails within the chart, after it, or never |
| `sensitivity_summary.md` | the findings and a one-input-at-a-time table per drug |
| `figures/sensitivity_heatmaps.png` | crossing week over speed x peak, one panel per drug |
| `figures/sensitivity_ranges.png` | how far each input moves the crossing week |
| `figures/sensitivity_horizon.png` | crossing week against the weeks asked, for three drugs |

Findings (details and numbers in `results/sensitivity_summary.md`):

1. **The number of weeks asked decides the answer.** Because the midpoint is 0.45 x the weeks asked, asking for 52 weeks instead of 8 makes the same drug fail 2 to 6 times later. A biological answer should not depend on the length of the chart.
2. **`peak` works as a switch.** At or below 50% a drug never fails. Colistin (hand-set peak exactly 0.50) never fails; vancomycin and imipenem stop failing within peak -30%.
3. **`speed` matters much less.** At 8 weeks, speed +-30% moves the crossing by a median of 0.6 weeks.
4. **GC content barely matters,** and 0.35 and 0.65 give the same result, because the starting share uses the distance of GC from 0.5.

So calibration should fit a per-drug midpoint (instead of 0.45 x the weeks asked) and the peak; speed is second.

## 2. Literature calibration (`calibrate.py`, to do)

Fit the same curve, with the midpoint as a free per-drug parameter, to 5 to 10 published resistance curves over time, and report RMSE and the fitted values against the hand-set ones. Curves go in `curves/` (one CSV per curve, `time,value`), with their sources in `curves/sources.csv` (drug, organism, paper, DOI, figure, unit, time unit, points).

Candidate sources: Toprak et al. 2012 morbidostat (Nature Genetics, doi:10.1038/ng.1034), the dynamic collateral-sensitivity paper (PLOS Biology, doi:10.1371/journal.pbio.3002970), and yearly percent-resistant series from ECDC EARS-Net and WHO GLASS. Lab curves are in days and surveillance in years while the app shows weeks, so calibration tests the shape of the curve and the ranking of drugs, not exact weeks.
