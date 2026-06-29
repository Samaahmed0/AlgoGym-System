import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent 
DATA = ROOT / "data_new"

MASTERY_REPORT = DATA / "mastery_report.csv"
INTERACTIONS   = DATA / "interactions_table.csv"
PROBLEMS       = DATA / "problems_table.csv"


for p in [MASTERY_REPORT, INTERACTIONS, PROBLEMS]:
    if not p.exists():
        print(f"ERROR: missing {p}")
        print("Run script 09 first: python Ai/gppkt/scripts/09_weakness_detection.py")
        sys.exit(1)

print("All files found. Running evaluation...\n")


prob_kc: dict[int, list[str]] = {}
with open(PROBLEMS, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        pi  = int(row.get("problem_idx") or 0)
        raw = (row.get("kc_names") or "").strip()
        kcs = [k.strip() for k in raw.split(";") if k.strip()]
        prob_kc[pi] = kcs

print(f"Loaded {len(prob_kc)} problems with KC tags.")

actual: dict[tuple[str,str], dict] = defaultdict(lambda: {"correct": 0, "total": 0})

with open(INTERACTIONS, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sid = (row.get("student_id") or "").strip()
        if not sid:
            continue
        try:
            pi = int(row.get("problem_idx") or 0)
            r  = int(float(row.get("r") or row.get("r_t") or 0))
        except ValueError:
            continue
        for kc in prob_kc.get(pi, []):
            actual[(sid, kc)]["total"]   += 1
            actual[(sid, kc)]["correct"] += r

print(f"Computed actual success rates for {len(actual)} (student, KC) pairs.")


mastery: dict[tuple[str,str], dict] = {}
with open(MASTERY_REPORT, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sid = (row.get("student_id") or "").strip()
        kc  = (row.get("kc_name")    or "").strip()
        if not sid or not kc:
            continue
        mastery[(sid, kc)] = {
            "mastery":    float(row.get("mastery")    or 0),
            "n_attempts": int(float(row.get("n_attempts") or 0)),
        }

print(f"Loaded {len(mastery)} mastery predictions.")

compare = []
for (sid, kc), act in actual.items():
    if act["total"] < 3:
        continue
    if (sid, kc) not in mastery:
        continue
    m = mastery[(sid, kc)]
    if m["n_attempts"] < 3:
        continue
    compare.append({
        "student_id":          sid,
        "kc_name":             kc,
        "mastery":             m["mastery"],
        "actual_success_rate": act["correct"] / act["total"],
    })

print(f"\nEvaluation pairs (>= 3 attempts): {len(compare)}\n")

if len(compare) < 10:
    print("Not enough pairs to evaluate. Check your data.")
    sys.exit(1)


mastery_vals = np.array([r["mastery"]             for r in compare])
actual_vals  = np.array([r["actual_success_rate"] for r in compare])

def spearman(a, b):
    n    = len(a)
    ra   = np.argsort(np.argsort(a))
    rb   = np.argsort(np.argsort(b))
    d2   = ((ra - rb) ** 2).sum()
    return 1 - 6 * d2 / (n * (n * n - 1))

corr = spearman(mastery_vals, actual_vals)
print(f"Spearman correlation (mastery vs real KC success rate): {corr:.4f}")
print("  0.0 = no relationship, 1.0 = perfect ranking\n")

try:
    from sklearn.metrics import roc_auc_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("sklearn not found — skipping AUC. pip install scikit-learn to enable.\n")

# group by KC
from collections import defaultdict as dd
by_kc: dict[str, list] = dd(list)
for r in compare:
    by_kc[r["kc_name"]].append(r)

kc_aucs = []
if HAS_SKLEARN:
    for kc, rows in by_kc.items():
        if len(rows) < 10:
            continue
        weak_true = np.array([1 if r["actual_success_rate"] < 0.5 else 0 for r in rows])
        if weak_true.sum() == 0 or weak_true.sum() == len(weak_true):
            continue  # all same class, skip
        pred_score = np.array([1 - r["mastery"] for r in rows])  # low mastery = weak
        kc_aucs.append(roc_auc_score(weak_true, pred_score))

    if kc_aucs:
        print(f"Per-KC weakness detection AUC:")
        print(f"  Mean:   {np.mean(kc_aucs):.4f}")
        print(f"  Median: {np.median(kc_aucs):.4f}")
        print(f"  KCs evaluated: {len(kc_aucs)}\n")
    else:
        print("No KCs had enough data for AUC.\n")

by_student: dict[str, list] = dd(list)
for r in compare:
    by_student[r["student_id"]].append(r)

TOP_N = 5
WEAK_ACTUAL_THRESH = 0.5
precisions: list[float] = []
for sid, rows in by_student.items():
    if len(rows) < TOP_N:
        continue
    ranked = sorted(rows, key=lambda x: x["mastery"])
    top = ranked[:TOP_N]
    hits = sum(1 for r in top if r["actual_success_rate"] < WEAK_ACTUAL_THRESH)
    precisions.append(hits / TOP_N)

if precisions:
    print(f"Precision@{TOP_N} (lowest-mastery KCs vs actual success < {WEAK_ACTUAL_THRESH}):")
    print(f"  Students evaluated: {len(precisions)}")
    print(f"  Mean:   {np.mean(precisions):.4f}")
    print(f"  Median: {np.median(precisions):.4f}")
else:
    print(f"Not enough students with >={TOP_N} KC pairs for Precision@{TOP_N}.")

print("\nMastery vs actual success rate (all evaluation pairs):")
for lo, hi, label in [
    (0.0, 0.4, "low mastery (<0.4)"),
    (0.4, 0.6, "mid mastery (0.4-0.6)"),
    (0.6, 1.01, "high mastery (>=0.6)"),
]:
    sub = [r for r in compare if lo <= r["mastery"] < hi]
    if sub:
        avg = np.mean([r["actual_success_rate"] for r in sub])
        print(f"  {label:22s}  n={len(sub):6d}  avg actual success: {avg:.4f}")

print("\nDone.")

