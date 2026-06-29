
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import (  # noqa: E402
    ARTIFACTS_DIR,
    CATALOG_PARQUET,
    FEATURE_SCHEMA_JSON,
    MASTERY_REPORT,
    PROBLEMS_CSV,
    RANKER_PKL,
    SUBMISSIONS_CSV,
    TOP_K,
    WEAKNESS_SUMMARY,
)
from recommender.catalog import load_catalog, ProblemCatalog  # noqa: E402
from recommender.io import recommendations_to_dict, write_json  # noqa: E402
from recommender.pipeline import recommend_for_student  # noqa: E402
from recommender.ranking import RankerModel  # noqa: E402
from recommender.user_state import load_user_state  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    p = argparse.ArgumentParser(description="Top-K problem recommendations")
    p.add_argument("--student-id", required=True)
    p.add_argument("--top-k", type=int, default=TOP_K)
    p.add_argument("--problems", type=Path, default=PROBLEMS_CSV)
    p.add_argument("--mastery", type=Path, default=MASTERY_REPORT)
    p.add_argument("--weakness", type=Path, default=WEAKNESS_SUMMARY)
    p.add_argument("--submissions", type=Path, default=SUBMISSIONS_CSV)
    p.add_argument("--catalog", type=Path, default=CATALOG_PARQUET)
    p.add_argument("--ranker", type=Path, default=RANKER_PKL)
    p.add_argument("--schema", type=Path, default=FEATURE_SCHEMA_JSON)
    p.add_argument("--out", type=Path, default=ARTIFACTS_DIR / "recommendation.json")
    args = p.parse_args()

    if args.catalog.exists():
        catalog = ProblemCatalog.from_parquet(args.catalog)
    else:
        catalog = load_catalog(args.problems)

    user_store = load_user_state(args.mastery, args.weakness if args.weakness.exists() else None)

    ranker = None
    if user_store.has_student(args.student_id):
        if not args.ranker.exists():
            raise SystemExit(f"Ranker not found: {args.ranker} (required for known students)")
        ranker = RankerModel.load(args.ranker, args.schema if args.schema.exists() else None)

    recs, meta = recommend_for_student(
        args.student_id,
        catalog,
        user_store,
        ranker,
        args.submissions,
        top_k=args.top_k,
    )

    payload = recommendations_to_dict(args.student_id, recs, meta)
    write_json(args.out, payload)
    print(f"Wrote {args.out}  mode={meta.get('mode')}  n_recs={len(recs)}")


if __name__ == "__main__":
    main()
