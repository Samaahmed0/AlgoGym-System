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
    EVAL_REPORT_JSON,
    FEATURE_SCHEMA_JSON,
    MASTERY_REPORT,
    PROBLEMS_CSV,
    RANKER_PKL,
    SUBMISSIONS_CSV,
    TOP_K,
    WEAKNESS_SUMMARY,
)
from recommender.catalog import load_catalog, ProblemCatalog  # noqa: E402
from recommender.eval import run_offline_eval  # noqa: E402
from recommender.io import write_eval_report  # noqa: E402
from recommender.ranking import RankerModel  # noqa: E402
from recommender.user_state import load_user_state  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Offline recommender evaluation")
    p.add_argument("--problems", type=Path, default=PROBLEMS_CSV)
    p.add_argument("--catalog", type=Path, default=CATALOG_PARQUET)
    p.add_argument("--mastery", type=Path, default=MASTERY_REPORT)
    p.add_argument("--weakness", type=Path, default=WEAKNESS_SUMMARY)
    p.add_argument("--submissions", type=Path, default=SUBMISSIONS_CSV)
    p.add_argument("--ranker", type=Path, default=RANKER_PKL)
    p.add_argument("--schema", type=Path, default=FEATURE_SCHEMA_JSON)
    p.add_argument("--out", type=Path, default=EVAL_REPORT_JSON)
    p.add_argument("--top-k", type=int, default=TOP_K)
    args = p.parse_args()

    if args.catalog.exists():
        catalog = ProblemCatalog.from_parquet(args.catalog)
    else:
        catalog = load_catalog(args.problems)

    user_store = load_user_state(args.mastery, args.weakness if args.weakness.exists() else None)
    ranker = RankerModel.load(args.ranker, args.schema) if args.ranker.exists() else None

    report = run_offline_eval(
        catalog,
        user_store,
        ranker,
        args.submissions,
        top_k=args.top_k,
    )
    write_eval_report(args.out, report)

    print(f"Wrote {args.out}")
    for method, stats in report.get("methods", {}).items():
        print(
            f"  {method}: counterfactual_gain={stats.get('avg_counterfactual_gain', stats.get('avg_gain_per_rec', 0)):.4f}  "
            f"behavioral_gain={stats.get('avg_behavioral_gain', 0):.6f}  "
            f"weak_hit={stats['avg_weak_kc_hit_rate']:.4f}  n={stats['n_eval_points']}"
        )


if __name__ == "__main__":
    main()
