from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import (  # noqa: E402
    ARTIFACTS_DIR,
    CATALOG_PARQUET,
    EVAL_FORWARD_WINDOW,
    EVAL_REPORT_JSON,
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
from recommender.catalog import load_catalog, ProblemCatalog  # noqa: E402
from recommender.eval_v2 import run_offline_eval_v2  # noqa: E402
from recommender.io import write_eval_report  # noqa: E402
from recommender.ranking3 import RankerModel  # noqa: E402
from recommender.user_state import load_user_state  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Offline v2 recommender evaluation")
    p.add_argument("--problems", type=Path, default=PROBLEMS_CSV)
    p.add_argument("--catalog", type=Path, default=CATALOG_PARQUET)
    p.add_argument("--mastery", type=Path, default=MASTERY_REPORT)
    p.add_argument("--weakness", type=Path, default=WEAKNESS_SUMMARY)
    p.add_argument("--submissions", type=Path, default=None)
    p.add_argument("--ranker", type=Path, default=RANKER_PKL)
    p.add_argument("--schema", type=Path, default=FEATURE_SCHEMA_JSON)
    p.add_argument("--out", type=Path, default=ARTIFACTS_DIR / "eval_report_v2.json")
    p.add_argument("--top-k", type=int, default=TOP_K)
    p.add_argument("--max-students", type=int, default=300)
    p.add_argument("--stride", type=int, default=20)
    p.add_argument("--forward-window", type=int, default=EVAL_FORWARD_WINDOW)
    args = p.parse_args()

    submissions = args.submissions or SUBMISSIONS_CSV
    if not submissions.exists():
        submissions = SUBMISSIONS_FALLBACK

    if args.catalog.exists():
        catalog = ProblemCatalog.from_parquet(args.catalog)
    else:
        catalog = load_catalog(args.problems)

    if not args.ranker.exists():
        raise SystemExit(f"Ranker not found: {args.ranker}")

    user_store = load_user_state(args.mastery, args.weakness if args.weakness.exists() else None)
    ranker = RankerModel.load(args.ranker, args.schema if args.schema.exists() else None)

    report = run_offline_eval_v2(
        catalog,
        user_store,
        ranker,
        submissions,
        top_k=args.top_k,
        max_students=args.max_students if args.max_students > 0 else EVAL_STUDENT_SAMPLE,
        stride=args.stride,
        forward_window=args.forward_window,
    )
    write_eval_report(args.out, report)

    print(f"Wrote {args.out}")
    for method, stats in report.get("methods", {}).items():
        print(
            f"  {method}: counterfactual_gain={stats.get('avg_counterfactual_gain', 0):.4f}  "
            f"weak_hit={stats['avg_weak_kc_hit_rate']:.4f}  n={stats['n_eval_points']}"
        )


if __name__ == "__main__":
    main()
