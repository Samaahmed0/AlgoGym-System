# Weakness export sanity check

**Checkpoint (both reports):** `best30epoch1loss/gppkt_kc_best.pt`  
**Ground truth:** solve rate per topic from `interactions_table.csv` (AC count / attempts on problems with that tag)  
**Rows used:** student–KC pairs with **≥3 attempts** (83,784 pairs)

## Old vs Option C infer export

| Metric | Old (last-step mastery) | **Infer (active-step Option C)** |
|--------|-------------------------|----------------------------------|
| Correlation (mastery ↔ solve rate) | 0.22 | **0.55** |
| Weak flags total | 6,088 | 6,512 |
| **Good weak** (flagged weak, solve ≤40%) | 36.7% of weak | **69.8%** of weak |
| **False weak** (flagged weak, solve ≥70%) | 15.0% of weak | **8.0%** of weak |
| Avg solve rate when marked weak | 48.8% | **34.5%** |
| Missed (solve ≤40% but not weak) | 18,581 | 16,267 |

## Verdict

**Option C infer export is better aligned with real performance**, not just “fewer weak topics.”

- Weak topics now match low solve rates much more often (~70% vs ~37%).
- False alarms (weak but ≥70% solve) dropped by about half (15% → 8%).
- Mastery scores track solve rate more closely (correlation 0.55 vs 0.22).

## Recommended v1

- **Checkpoint:** `best30epoch1loss/gppkt_kc_best.pt`
- **Export:** re-run script 09 (Option C) → canonical `mastery_report.csv` + `weakness_summary.csv`
- **Do not use:** `option_c/weakness_summary.csv` (10-epoch model) or new Kaggle run until training metric is fixed

Full JSON: `sanity_eval.json`  
Script: `Ai/gppkt/scripts/10_sanity_eval_weakness.py`
