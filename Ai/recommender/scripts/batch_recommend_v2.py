from __future__ import annotations

import argparse
import csv
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
    SUBMISSIONS_FALLBACK,
    TOP_K,
    WEAKNESS_SUMMARY,
)
from recommender.catalog import ProblemCatalog, load_catalog  
from recommender.io import recommendations_to_dict, write_json  
from recommender.features2 import load_prefix_users_by_student  
from recommender.pipeline_v2 import recommend_for_student  
from recommender.ranking3 import RankerModel 
from recommender.user_state import load_user_state  


def load_solved_by_user(submissions_path: Path) -> dict[str, set[str]]:
    solved: dict[str, set[str]] = {}
    with submissions_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("verdict") or "").strip() != "ACCEPTED":
                continue
            uid = (row.get("user_id") or row.get("student_id") or "").strip()
            pid = (row.get("problem_id") or "").strip()
            if uid and pid:
                solved.setdefault(uid, set()).add(pid)
    return solved


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch Top-K recommendations (pipeline_v2).")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--student-id", help="Single user id (e.g. users.id UUID)")
    g.add_argument("--all", action="store_true", help="All students in mastery report")
    g.add_argument(
        "--student-ids-file",
        type=Path,
        help="Text file with one student_id per line",
    )

    p.add_argument("--top-k", type=int, default=TOP_K)
    p.add_argument("--problems", type=Path, default=PROBLEMS_CSV)
    p.add_argument("--catalog", type=Path, default=CATALOG_PARQUET)
    p.add_argument("--mastery", type=Path, default=MASTERY_REPORT)
    p.add_argument("--weakness", type=Path, default=WEAKNESS_SUMMARY)
    p.add_argument("--submissions", type=Path, default=None)
    p.add_argument("--ranker", type=Path, default=RANKER_PKL)
    p.add_argument("--schema", type=Path, default=FEATURE_SCHEMA_JSON)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=ARTIFACTS_DIR / "recommendations_batch",
        help="Per-user JSON output directory",
    )
    p.add_argument(
        "--combined-out",
        type=Path,
        default=ARTIFACTS_DIR / "recommendations_all.json",
        help="Combined JSON for all users",
    )
    p.add_argument("--no-combined", action="store_true")
    p.add_argument(
        "--weak-first",
        action="store_true",
        default=None,
        help="Force weak-first (default: config WEAK_FIRST=True)",
    )
    p.add_argument(
        "--no-weak-first",
        action="store_true",
        help="Disable weak-first filter",
    )
    return p.parse_args()


def resolve_submissions(path: Path | None) -> Path:
    if path and path.exists():
        return path
    if SUBMISSIONS_CSV.exists():
        return SUBMISSIONS_CSV
    if SUBMISSIONS_FALLBACK.exists():
        return SUBMISSIONS_FALLBACK
    raise SystemExit(f"No submissions file found: {path or SUBMISSIONS_CSV}")


def list_student_ids(mastery_path: Path) -> list[str]:
    seen: set[str] = set()
    ids: list[str] = []
    with mastery_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = (row.get("student_id") or "").strip()
            if sid and sid not in seen:
                seen.add(sid)
                ids.append(sid)
    return sorted(ids)


def resolve_student_ids(args: argparse.Namespace, mastery_path: Path) -> list[str]:
    if args.student_id:
        return [args.student_id.strip()]
    if args.student_ids_file:
        lines = args.student_ids_file.read_text(encoding="utf-8").splitlines()
        return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
    return list_student_ids(mastery_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    submissions = resolve_submissions(args.submissions)
    weakness_path = args.weakness if args.weakness.exists() else None

    if not args.ranker.exists():
        raise SystemExit(f"Ranker not found: {args.ranker}")
    if not args.mastery.exists():
        raise SystemExit(f"Mastery report not found: {args.mastery}")

    student_ids = resolve_student_ids(args, args.mastery)
    if not student_ids:
        raise SystemExit("No student ids to process.")

    if args.catalog.exists():
        catalog = ProblemCatalog.from_parquet(args.catalog)
    else:
        catalog = load_catalog(args.problems)

    user_store = load_user_state(args.mastery, weakness_path)
    ranker = RankerModel.load(args.ranker, args.schema if args.schema.exists() else None)

    weak_first = False if args.no_weak_first else args.weak_first

    preload = len(student_ids) > 1
    solved_by_user: dict[str, set[str]] = {}
    prefix_by_user: dict = {}
    if preload:
        logging.info("preloading submissions (one pass)...")
        solved_by_user = load_solved_by_user(submissions)
        prefix_by_user = load_prefix_users_by_student(catalog, submissions)
        logging.info("preloaded %d users from submissions", len(prefix_by_user))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    combined: dict[str, dict] = {}
    ok, skip = 0, 0

    logging.info("ranker features: %d", len(ranker.feature_columns))
    logging.info("submissions: %s", submissions)
    logging.info("students: %d", len(student_ids))

    for sid in student_ids:
        needs_ranker = user_store.has_student(sid)
        if needs_ranker and ranker is None:
            logging.warning("skip %s: no ranker", sid)
            skip += 1
            continue

        recs, meta = recommend_for_student(
            sid,
            catalog,
            user_store,
            ranker if needs_ranker else None,
            submissions,
            top_k=args.top_k,
            weak_first=weak_first,
            solved_ids=solved_by_user.get(sid, set()) if preload else None,
            prefix_user=prefix_by_user.get(sid) if preload else None,
        )

        payload = recommendations_to_dict(sid, recs, meta)
        out_path = args.out_dir / f"{sid}.json"
        write_json(out_path, payload)
        combined[sid] = payload

        logging.info(
            "wrote %s  mode=%s  n_recs=%d",
            out_path.name,
            meta.get("mode"),
            len(recs),
        )
        ok += 1

    if not args.no_combined:
        write_json(args.combined_out, {"students": combined, "count": ok})
        logging.info("combined: %s", args.combined_out)

    logging.info("done: %d users written, %d skipped", ok, skip)


if __name__ == "__main__":
    main()
