# Timeline sensitivity analysis

Written by `sensitivity.py`. Crossing week = the exact time the resistant share reaches 50% (the served timeline reports the next whole week). Base case: the hand-set profile, 8 weeks asked (the `/timeline` default), GC 0.5.

## Findings

1. **The number of weeks asked for decides the answer.** The midpoint is 0.45 x the weeks asked, so asking for 52 weeks instead of 8 moves the crossing 2.1 to 6.3 times later for the same bacterium and drug. A biological quantity should not depend on the length of the chart.
2. **`peak` works as a switch.** At or below 50% the drug never fails. 3 of 14 profiles switch between "fails" and "never fails" within peak +-30%: colistin, imipenem, vancomycin. At the hand-set values, colistin never fails.
3. **`speed` matters less.** Speed +-30% moves the crossing by at most 9.9 weeks (median 0.6) at 8 weeks asked.
4. **GC content sets the starting share (2% to 15%)** and moves the crossing only slightly.

So the parameters worth calibrating are a per-drug midpoint (instead of 0.45 x the weeks asked) and the peak; speed is second.

## One input at a time

| Drug | Base | Speed -30% | Speed +30% | Peak -30% | Peak +30% | GC 0.35 | GC 0.65 | 12 weeks asked | 52 weeks asked |
|---|---|---|---|---|---|---|---|---|---|
| ciprofloxacin | 3.9 | 4.0 | 3.8 | 6.3 | 3.5 | 3.8 | 3.8 | 5.7 | 23.7 |
| ampicillin | 3.7 | 3.8 | 3.7 | 5.5 | 3.5 | 3.6 | 3.6 | 5.5 | 23.5 |
| tetracycline | 4.0 | 4.1 | 3.9 | 6.2 | 3.5 | 3.9 | 3.9 | 5.8 | 23.8 |
| chloramphenicol | 4.2 | 4.5 | 4.1 | 7.4 | 3.5 | 4.1 | 4.1 | 6.0 | 24.0 |
| gentamicin | 5.8 | 6.7 | 5.3 | 13.4 | 3.6 | 5.6 | 5.6 | 7.6 | 25.6 |
| cefotaxime | 4.4 | 4.7 | 4.2 | 7.7 | 3.5 | 4.3 | 4.3 | 6.2 | 24.2 |
| imipenem | 9.4 | 11.9 | 8.1 | never | 5.3 | 9.1 | 9.1 | 11.2 | 29.2 |
| trimethoprim/sulfamethoxazole | 4.1 | 4.3 | 4.0 | 6.6 | 3.5 | 4.0 | 4.0 | 5.9 | 23.9 |
| vancomycin | 18.7 | 25.1 | 15.2 | never | 9.0 | 18.3 | 18.3 | 20.5 | 38.5 |
| colistin | never | never | never | never | 12.9 | never | never | never | never |
| streptomycin | 4.6 | 5.0 | 4.3 | 8.0 | 3.5 | 4.4 | 4.4 | 6.4 | 24.4 |
| erythromycin | 5.1 | 5.8 | 4.8 | 10.3 | 3.5 | 5.0 | 5.0 | 6.9 | 24.9 |
| rifampicin | 5.0 | 5.7 | 4.7 | 10.0 | 3.5 | 4.9 | 4.9 | 6.8 | 24.8 |
| default | 4.9 | 5.4 | 4.6 | 9.1 | 3.5 | 4.7 | 4.7 | 6.7 | 24.7 |

Grid: 8,232 rows (14 profiles x 7 speeds x 7 peaks x 4 horizons x 3 GC values) in `sensitivity.csv`. Every row was checked: the served `generate_timeline` and the exact crossing agree.
