
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_GPPKT = _SCRIPTS.parent
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import DEFAULT_INTERACTIONS, DEFAULT_PROBLEMS  # noqa: E402
from kc_strings import split_kc_names_field  # noqa: E402


def load_problem_kcs(problems_path: Path) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    with problems_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pi = int((row.get("problem_idx") or "0").strip() or 0)
            out[pi] = split_kc_names_field(row.get("kc_names") or "")
    return out


def build_solve_rates(interactions_path: Path, problem_kcs: dict[int, list[str]]) -> dict[tuple[str, str], tuple[int, int, float]]:
    """(student_id, kc) -> (n_ok, n_total, rate)."""
    ok: dict[tuple[str, str], int] = defaultdict(int)
    tot: dict[tuple[str, str], int] = defaultdict(int)
    with interactions_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = (row.get("student_id") or "").strip()
            if not sid:
                continue
            pi = int((row.get("problem_idx") or "0").strip() or 0)
            y = int(float(row.get("r") or 0))
            for kc in problem_kcs.get(pi) or []:
                key = (sid, kc)
                tot[key] += 1
                ok[key] += y
    return {k: (ok[k], tot[k], ok[k] / tot[k] if tot[k] else 0.0) for k, _ in tot.items()}


def load_mastery_report(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "student_id": row["student_id"],
                    "kc_name": row["kc_name"],
                    "mastery": float(row["mastery"]),
                    "n_attempts": int(row["n_attempts"]),
                    "is_weak": int(row["is_weak"]),
                    "rank": int(row["rank"]) if (row.get("rank") or "").strip() else None,
                }
            )
    return rows


def eval_report(
    label: str,
    rows: list[dict],
    solve_rates: dict[tuple[str, str], tuple[int, int, float]],
    min_attempts: int = 3,
) -> dict:
    joined: list[dict] = []
    for r in rows:
        key = (r["student_id"], r["kc_name"])
        if key not in solve_rates:
            continue
        n_ok, n_tot, rate = solve_rates[key]
        if n_tot < min_attempts:
            continue
        joined.append({**r, "n_ok": n_ok, "n_tot": n_tot, "solve_rate": rate})

    if not joined:
        return {"label": label, "n_rows": 0}

    weak = [j for j in joined if j["is_weak"] == 1]
    not_weak = [j for j in joined if j["is_weak"] == 0]

    def mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else float("nan")

    false_weak = [j for j in weak if j["solve_rate"] >= 0.7]
    good_weak = [j for j in weak if j["solve_rate"] <= 0.4]
    missed = [j for j in not_weak if j["solve_rate"] <= 0.4 and j["n_tot"] >= min_attempts]

    # correlation mastery vs solve_rate
    m_list = [j["mastery"] for j in joined]
    s_list = [j["solve_rate"] for j in joined]
    n = len(joined)
    mean_m, mean_s = mean(m_list), mean(s_list)
    cov = sum((m - mean_m) * (s - mean_s) for m, s in zip(m_list, s_list)) / n
    var_m = sum((m - mean_m) ** 2 for m in m_list) / n
    var_s = sum((s - mean_s) ** 2 for s in s_list) / n
    corr = cov / (var_m**0.5 * var_s**0.5) if var_m > 0 and var_s > 0 else float("nan")

    buckets = [(0.0, 0.35), (0.35, 0.4), (0.4, 0.5), (0.5, 0.65), (0.65, 1.01)]
    bucket_stats = []
    for lo, hi in buckets:
        sub = [j for j in joined if lo <= j["mastery"] < hi]
        if sub:
            bucket_stats.append(
                {
                    "mastery_lo": lo,
                    "mastery_hi": hi,
                    "n": len(sub),
                    "avg_solve_rate": round(mean([j["solve_rate"] for j in sub]), 4),
                }
            )

    examples_false = sorted(false_weak, key=lambda j: (-j["solve_rate"], -j["n_tot"]))[:8]
    examples_good = sorted(good_weak, key=lambda j: (j["solve_rate"], -j["n_tot"]))[:8]

    return {
        "label": label,
        "n_rows_min_attempts": len(joined),
        "n_weak_flags": len(weak),
        "n_students_with_weak": len({j["student_id"] for j in weak}),
        "avg_mastery_weak": round(mean([j["mastery"] for j in weak]), 4) if weak else None,
        "avg_mastery_not_weak": round(mean([j["mastery"] for j in not_weak]), 4) if not_weak else None,
        "avg_solve_rate_weak": round(mean([j["solve_rate"] for j in weak]), 4) if weak else None,
        "avg_solve_rate_not_weak": round(mean([j["solve_rate"] for j in not_weak]), 4) if not_weak else None,
        "corr_mastery_vs_solve_rate": round(corr, 4),
        "weak_with_solve_rate_lte_0.4": len(good_weak),
        "weak_with_solve_rate_gte_0.7": len(false_weak),
        "pct_false_weak": round(100.0 * len(false_weak) / len(weak), 2) if weak else 0.0,
        "pct_good_weak": round(100.0 * len(good_weak) / len(weak), 2) if weak else 0.0,
        "not_weak_but_solve_lte_0.4": len(missed),
        "mastery_buckets": bucket_stats,
        "examples_false_weak": [
            {
                "student_id": j["student_id"],
                "kc": j["kc_name"],
                "mastery": round(j["mastery"], 4),
                "solve": f"{j['n_ok']}/{j['n_tot']}={j['solve_rate']:.0%}",
            }
            for j in examples_false
        ],
        "examples_good_weak": [
            {
                "student_id": j["student_id"],
                "kc": j["kc_name"],
                "mastery": round(j["mastery"], 4),
                "solve": f"{j['n_ok']}/{j['n_tot']}={j['solve_rate']:.0%}",
            }
            for j in examples_good
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Sanity-check mastery reports vs solve rates")
    p.add_argument("--interactions", type=Path, default=DEFAULT_INTERACTIONS)
    p.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS)
    p.add_argument(
        "--old-report",
        type=Path,
        default=_GPPKT / "data_new" / "best30epoch1loss" / "mastery_report.csv",
        help="Old export (last-step mastery)",
    )
    p.add_argument(
        "--infer-report",
        type=Path,
        default=_GPPKT / "data_new" / "option_c" / "mastery_report_infer_only.csv",
        help="Option C export (active-step mastery)",
    )
    p.add_argument("--out", type=Path, default=_GPPKT / "data_new" / "option_c" / "sanity_eval.json")
    p.add_argument("--min-attempts", type=int, default=3)
    args = p.parse_args()

    problem_kcs = load_problem_kcs(args.problems)
    solve_rates = build_solve_rates(args.interactions, problem_kcs)

    results = {
        "min_attempts": args.min_attempts,
        "old": eval_report("old_last_step", load_mastery_report(args.old_report), solve_rates, args.min_attempts),
        "infer_option_c": eval_report(
            "infer_active_step", load_mastery_report(args.infer_report), solve_rates, args.min_attempts
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    for key in ("old", "infer_option_c"):
        r = results[key]
        print(f"\n=== {r['label']} ===")
        print(f"  rows (n>={args.min_attempts}): {r['n_rows_min_attempts']}")
        print(f"  weak flags: {r['n_weak_flags']}  students with weak: {r['n_students_with_weak']}")
        print(f"  corr(mastery, solve_rate): {r['corr_mastery_vs_solve_rate']}")
        print(f"  weak: avg mastery {r['avg_mastery_weak']}  avg solve {r['avg_solve_rate_weak']}")
        print(f"  not weak: avg mastery {r['avg_mastery_not_weak']}  avg solve {r['avg_solve_rate_not_weak']}")
        print(f"  good weak (solve<=40%): {r['weak_with_solve_rate_lte_0.4']} ({r['pct_good_weak']}%)")
        print(f"  false weak (solve>=70%): {r['weak_with_solve_rate_gte_0.7']} ({r['pct_false_weak']}%)")
        print(f"  missed weak (not weak but solve<=40%): {r['not_weak_but_solve_lte_0.4']}")

    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
