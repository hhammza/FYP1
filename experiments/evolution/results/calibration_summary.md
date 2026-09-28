# Timeline calibration against published curves

Written by `calibrate.py`. The timeline's logistic curve fitted to published resistance data; parameters with 95% confidence intervals. Rise time = how long the curve takes from 10% to 90% of its rise (ln 81 / k), which compares shapes across time units.

## Summary

- **15 curves fitted**: 5 lab (days) and 10 surveillance (years). Median R² 0.91; the logistic shape fits both kinds of data.
- **Lab:** resistance to the selecting drug rises within days; rise times 0.5 to 6.6 days. Ciprofloxacin, ceftriaxone, daptomycin rise mostly before day 2, the first measurement, so their midpoint rests on day 0 and day 2 alone; doxycycline jumps between two measurements; linezolid rises gradually over the week.
- **Surveillance:** in the 7 countries where carbapenem-resistant *K. pneumoniae* has levelled off, it did so at 7% to 66% (median 21%), rising over a median 3.5 years. In 3 more (Cyprus, Bulgaria, Romania) it is still rising in the last year, so their plateau is extrapolated and left out of these figures. The timeline's hand-set imipenem peak is 65%.
- **For the timeline:** the peak is the parameter the data can set, and it varies by setting (country) far more than the ±30% the sensitivity analysis tried. The time scale cannot be carried over: lab curves run in days and surveillance in years, while the timeline shows weeks. So the timeline's weeks remain an illustration, which the page should say, and its midpoint should be a per-drug value rather than 0.45 x the weeks asked (see `sensitivity_summary.md`).

## Lab curves (Maltas, Huynh & Wood 2025)

*E. faecalis* V583, 4 replicate populations per drug, resistance to the drug each was evolved in, log2 IC50 fold change over the ancestor. r0 fixed at 0 (the ancestor).

| Drug | Points | Plateau (log2) | k per day | Midpoint (day) | Rise 10 to 90% (days) | RMSE (log2) | R² | Timeline profile |
|---|---|---|---|---|---|---|---|---|
| ciprofloxacin | 20 | 4.48 ± 0.30 | 3.61 ± 22.73 | 1.66 ± 2.16 | 1.2 | 0.48 | 0.93 | ciprofloxacin: rise 9.8 weeks, peak 92% |
| ceftriaxone | 20 | 5.72 ± 0.31 | 4.33 ± 39.57 | 1.55 ± 4.09 | 1.0 | 0.51 | 0.95 | cefotaxime: rise 11.0 weeks, peak 85% |
| doxycycline | 20 | 2.08 ± 0.21 | 8.33 ± 604234.40 | 2.10 ± 7556.00 | 0.5 | 0.28 | 0.91 | tetracycline: rise 8.8 weeks, peak 90% |
| daptomycin | 20 | 4.16 ± 0.35 | 4.94 ± 309.19 | 1.69 ± 19.13 | 0.9 | 0.56 | 0.89 | none |
| linezolid | 20 | 4.32 ± 2.02 | 0.67 ± 0.69 | 4.23 ± 2.23 | 6.6 | 1.00 | 0.68 | none |

## Surveillance curves (ECDC EARS-Net)

Carbapenem-resistant *K. pneumoniae*, share of invasive isolates, per country. Fitted where a country has at least 12 years and resistance rose by at least 10% points. Compare with the timeline's imipenem profile: peak 65%, rise 22.0 weeks.

| Country | Years | Start | Plateau | Plateau reached? | k per year | Midpoint (year) | Rise 10 to 90% (years) | RMSE (points) | R² |
|---|---|---|---|---|---|---|---|---|---|
| Cyprus | 19 | 9% | 100% ± 373% | no, still rising (extrapolated) | 0.36 ± 0.53 | 2025.0 | 12.2 | 4.9 | 0.84 |
| Bulgaria | 20 | 0% | 83% ± 21% | no, still rising (extrapolated) | 0.44 ± 0.13 | 2021.0 | 10.0 | 2.5 | 0.99 |
| Greece | 20 | 29% | 66% ± 3% | yes | 0.69 ± 0.60 | 2009.1 | 6.4 | 4.7 | 0.87 |
| Romania | 15 | 0% | 62% ± 41% | no, still rising (extrapolated) | 0.25 ± 0.34 | 2016.8 | 17.9 | 5.6 | 0.89 |
| Italy | 19 | 1% | 29% ± 2% | yes | 2.90 ± 3.42 | 2010.0 | 1.5 | 2.8 | 0.94 |
| Croatia | 19 | 0% | 29% ± 3% | yes | 1.73 ± 0.87 | 2019.4 | 2.5 | 2.0 | 0.97 |
| Poland | 17 | 0% | 21% ± 6% | yes | 0.58 ± 0.36 | 2019.4 | 7.6 | 1.7 | 0.94 |
| Slovakia | 14 | 3% | 14% ± 2% | yes | 1.60 ± 1.69 | 2019.9 | 2.8 | 1.5 | 0.90 |
| Portugal | 18 | 1% | 12% ± 1% | yes | 1.13 ± 0.41 | 2016.2 | 3.9 | 0.7 | 0.98 |
| Malta | 19 | 0% | 7% ± 2% | yes | 1.27 ± 3.01 | 2011.5 | 3.5 | 2.7 | 0.57 |

## Caveats

- Lab data measure how resistant one population becomes (IC50), not what share of a population is resistant; the two are not pooled.
- Surveillance percentages mix many strains, hospitals and changes in testing; some countries fall after their peak (Italy), which a logistic curve cannot follow.
- Neither source is in weeks. The fits calibrate the curve's shape and plateau, not the timing the timeline shows.

ECDC data: "Dataset provided by ECDC based on data provided by public health authorities, scientific institutes or health care providers in the relevant reporting countries and/or by WHO" (CC BY 4.0); the fitted curves are our adaptation.
