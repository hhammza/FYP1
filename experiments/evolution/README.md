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

## 2. Literature calibration (`calibrate.py`)

```bash
.venv/bin/python experiments/evolution/calibrate.py      # seconds
```

Fits the timeline's curve, with the midpoint as a free parameter, to two kinds of published data, kept apart because they measure different things. The data and their sources are in `Data/evolution_curves/` (`sources.csv` lists each file with its DOI, licence and whether it is used).

| Data | What it measures | Curves |
| --- | --- | --- |
| Maltas, Huynh & Wood 2025, PLOS Biology (doi:10.1371/journal.pbio.3002970), S1 Data sheet Fig1B | how resistant one lab population of *E. faecalis* becomes to the drug it evolves in (log2 IC50 fold change), days 0 to 8, 4 replicates | 5 drugs: ciprofloxacin, ceftriaxone, doxycycline, daptomycin, linezolid |
| ECDC Surveillance Atlas, EARS-Net | share of invasive *K. pneumoniae* isolates resistant to carbapenems, per country, 2005 to 2024 | 10 countries where resistance rose |

Outputs in `results/`:

| File | What it holds |
| --- | --- |
| `calibration.csv` | one row per curve: plateau, slope, midpoint with 95% CIs, rise time, RMSE, R², and for surveillance whether the plateau is reached |
| `calibration_summary.md` | the tables and what they mean for the timeline |
| `figures/calibration_lab.png` | replicates, means and fitted curve per drug |
| `figures/calibration_surveillance.png` | yearly data and fitted curve per country, with the timeline's imipenem peak |
| `backend/trained_models/timeline_calibration.json` | the `calibration` object `/api/timeline/` returns and `/timeline` shows (formats §4) |

Findings (numbers in `results/calibration_summary.md`):

1. **The logistic shape fits both kinds of data:** 15 curves, median R² 0.91.
2. **Lab resistance rises within days.** Ciprofloxacin, ceftriaxone and daptomycin rise mostly before the first measurement (day 2), so their midpoint rests on two time points; doxycycline jumps between days 2 and 4; linezolid rises gradually over the week.
3. **In hospitals the plateau depends on the setting.** Where carbapenem resistance in *K. pneumoniae* has levelled off it did so at 7% to 66% depending on the country (Greece 66%, close to the timeline's hand-set imipenem peak of 65%; Italy 29%), after a rise of a few years. Cyprus, Bulgaria and Romania are still rising, so their plateau is extrapolated and not counted.
4. **For the timeline:** the data can set the peak, which varies far more between settings than the ±30% of the sensitivity analysis. The time scale cannot be carried over (lab days, hospital years, timeline weeks), so the timeline's weeks stay an illustration, which the page should say, and its midpoint should be a per-drug value rather than 0.45 x the weeks asked.

ECDC data: "Dataset provided by ECDC based on data provided by public health authorities, scientific institutes or health care providers in the relevant reporting countries and/or by WHO" (CC BY 4.0); the fitted curves are our adaptation.

Not used yet: Maltas & Wood 2019 (mostly endpoints), Zlamal et al. 2021 (check whether its data sets hold resistance over time), and further ECDC series (*E. coli* fluoroquinolones, MRSA), which `calibrate.py` can take once exported.

## 3. RL environment (`rl_env.py`, T3.1c)

```bash
.venv/bin/python experiments/evolution/rl_env.py          # seconds
```

A Gymnasium environment for choosing one drug a week. The drug given moves one week along its timeline curve (k = 2.5 x speed, ceiling `peak`); drugs not given lose resistance by a weekly fitness cost. The state is the resistant share per drug plus the share of the horizon gone; the reward is minus the resistant share of the drug given, minus the week's total rise in resistance. A week's treatment fails when the drug given is at 50% or more. Episodes always run the full horizon (104 weeks): ending them at failure would pay the agent to fail fast.

`results/rl_baselines.md` scores the policies the agent has to beat (always one drug, cycling every week or every 4 weeks, and greedy: the drug with the lowest resistance now) over 100 seeded episodes, for fitness costs of 0%, 2% and 5% a week, since the real cost is not known. With no cost every mixed policy gets about 36 effective weeks; with 2%, cycling every week gets the most effective weeks (57) and greedy the lowest burden; with 5%, greedy never fails.

Simplifications: three drugs from different classes (ciprofloxacin, gentamicin, imipenem), no cross-resistance, hand-set curves and an illustrative time scale. The policy is learned on a simulation, not on patient data.
