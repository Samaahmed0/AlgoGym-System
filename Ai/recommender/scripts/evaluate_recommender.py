from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import (  
    ARTIFACTS_DIR,
    CATALOG_PARQUET,
    EVAL_FORWARD_WINDOW,
    EVAL_STRIDE,
    EVAL_STUDENT_SAMPLE,
    FEATURE_SCHEMA_JSON,
    MASTERY_REPORT,
    PROBLEMS_CSV,
    RANKER_PKL,
    SUBMISSIONS_CSV,
    SUBMISSIONS_FALLBACK,
    TOP_K,
    WEAKNESS_SUMMARY,
)
from recommender.catalog import ProblemCatalog, load_catalog
from recommender.eval_v2 import run_offline_eval_v2 
from recommender.io import write_eval_report  
from recommender.ranking3 import RankerModel  
from recommender.user_state import load_user_state 


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Offline counterfactual evaluation for hybrid recommender (v2/v3 ranker)."
    )
    p.add_argument("--problems", type=Path, default=PROBLEMS_CSV, help="Problem catalog CSV")
    p.add_argument("--catalog", type=Path, default=CATALOG_PARQUET, help="Cached catalog parquet")
    p.add_argument("--mastery", type=Path, default=MASTERY_REPORT, help="GPPKT mastery report CSV")
    p.add_argument("--weakness", type=Path, default=WEAKNESS_SUMMARY, help="GPPKT weakness summary CSV")
    p.add_argument("--submissions", type=Path, default=None, help="Submissions CSV for replay")
    p.add_argument("--ranker", type=Path, default=RANKER_PKL, help="Trained LightGBM ranker.pkl")
    p.add_argument("--schema", type=Path, default=FEATURE_SCHEMA_JSON, help="feature_schema.json")
    p.add_argument(
        "--out",
        type=Path,
        default=ARTIFACTS_DIR / "eval_report_v2.json",
        help="JSON report output path",
    )
    p.add_argument("--top-k", type=int, default=TOP_K, help="Recommendations per checkpoint")
    p.add_argument(
        "--max-students",
        type=int,
        default=300,
        help="Sample size (0 = all students with mastery export; slow)",
    )
    p.add_argument(
        "--stride",
        type=int,
        default=20,
        help="Evaluate every N submissions per student (5 = finer, slower)",
    )
    p.add_argument(
        "--forward-window",
        type=int,
        default=EVAL_FORWARD_WINDOW,
        help="Forward steps for counterfactual gain label",
    )
    p.add_argument("--seed", type=int, default=42, help="RNG seed for student sampling")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    submissions = args.submissions or SUBMISSIONS_CSV
    if not submissions.exists():
        submissions = SUBMISSIONS_FALLBACK
    if not submissions.exists():
        raise SystemExit(f"Submissions file not found: {submissions}")

    if not args.ranker.exists():
        raise SystemExit(f"Ranker not found: {args.ranker}")

    if args.catalog.exists():
        catalog = ProblemCatalog.from_parquet(args.catalog)
    else:
        catalog = load_catalog(args.problems)

    weakness_path = args.weakness if args.weakness.exists() else None
    user_store = load_user_state(args.mastery, weakness_path)
    ranker = RankerModel.load(args.ranker, args.schema if args.schema.exists() else None)

    max_students = args.max_students if args.max_students > 0 else EVAL_STUDENT_SAMPLE

    print("=== AlgoGym recommender offline evaluation ===")
    print(f"  ranker:       {args.ranker}")
    print(f"  features:     {len(ranker.feature_columns)} columns")
    print(f"  submissions:  {submissions}")
    print(f"  students:     {max_students or 'all'}")
    print(f"  stride:       {args.stride}")
    print(f"  top_k:        {args.top_k}")
    print()

    report = run_offline_eval_v2(
        catalog,
        user_store,
        ranker,
        submissions,
        top_k=args.top_k,
        max_students=max_students,
        stride=args.stride,
        forward_window=args.forward_window,
        seed=args.seed,
    )
    write_eval_report(args.out, report)

    print(f"Wrote {args.out}\n")
    print("Results:")
    for method, stats in report.get("methods", {}).items():
        print(
            f"  {method:18s}  "
            f"gain={stats.get('avg_counterfactual_gain', 0):.4f}  "
            f"weak_hit={stats['avg_weak_kc_hit_rate']:.4f}  "
            f"beh_gain={stats.get('avg_behavioral_gain', 0):.6f}  "
            f"n={stats['n_eval_points']}"
        )

    print("\nFull report JSON:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
