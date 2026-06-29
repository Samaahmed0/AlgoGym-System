
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

# Allow running as `python 00_extract_tables.py` from scripts/
_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import (  # noqa: E402
    ALLOWED_VERDICTS,
    B_I_SCALE,
    DATA_DIR,
    DEFAULT_RATING_IMPUTATION,
    MIN_INTERACTIONS_PER_STUDENT,
    RATING_MAX,
    RATING_MIN,
    VERDICT_ACCEPTED,
)
from kc_strings import kc_names_to_semicolon_field, union_tags_concepts_kc_names  # noqa: E402


def _parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _rating_to_b_i(rating_val: float | int, median_fill: float) -> float:
    r = float(rating_val) if rating_val is not None else median_fill
    r_clipped = max(RATING_MIN, min(RATING_MAX, r))
    u = (r_clipped - RATING_MIN) / (RATING_MAX - RATING_MIN)
    return B_I_SCALE * (u - 0.5) * 2


def _read_submissions(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({k: (v or "") for k, v in row.items() if k})
    return rows


def _read_problems(path: Path) -> dict[str, dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            clean = {k: (v or "") for k, v in row.items() if k and k.strip()}
            pid = clean.get("id", "").strip()
            if pid:
                by_id[pid] = clean
    return by_id


def run(
    submissions_path: Path,
    problems_path: Path,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    interactions_out = out_dir / "interactions_table.csv"
    problems_out = out_dir / "problems_table.csv"

    subs = _read_submissions(submissions_path)
    prob_by_id = _read_problems(problems_path)

    # Filter verdicts + join to problems.id
    kept: list[tuple[dict, str]] = []
    for row in subs:
        v = (row.get("verdict") or "").strip()
        if v not in ALLOWED_VERDICTS:
            continue
        pid = (row.get("problem_id") or "").strip()
        if pid not in prob_by_id:
            continue
        kept.append((row, pid))

    if not kept:
        raise SystemExit("No rows after verdict filter and join; check inputs.")

    # Sort by user, then time
    def sort_key(item: tuple[dict, str]) -> tuple[str, datetime]:
        r, _pid = item
        uid = (r.get("user_id") or "").strip()
        ts = (r.get("submitted_at") or "").strip()
        try:
            t = _parse_ts(ts)
        except Exception:
            t = datetime.min
        return (uid, t)

    kept.sort(key=sort_key)

    # Count per student
    from collections import Counter

    user_counts: Counter[str] = Counter()
    for row, _pid in kept:
        user_counts[(row.get("user_id") or "").strip()] += 1

    eligible_users = {u for u, c in user_counts.items() if c >= MIN_INTERACTIONS_PER_STUDENT}

    filtered = [(r, p) for r, p in kept if (r.get("user_id") or "").strip() in eligible_users]
    if not filtered:
        raise SystemExit(
            f"No students with >={MIN_INTERACTIONS_PER_STUDENT} interactions after filtering."
        )

    filtered.sort(key=sort_key)

    # Stable problem_idx over problems that appear
    seen_pids: list[str] = []
    pid_set: set[str] = set()
    for _row, pid in filtered:
        if pid not in pid_set:
            pid_set.add(pid)
            seen_pids.append(pid)

    problem_idx_map = {pid: i for i, pid in enumerate(seen_pids)}

    # Median rating over problems that have numeric rating in extract
    ratings: list[float] = []
    for pid in seen_pids:
        raw = (prob_by_id[pid].get("rating") or "").strip()
        if not raw:
            continue
        try:
            ratings.append(float(raw))
        except ValueError:
            continue
    median_rating = statistics.median(ratings) if ratings else (RATING_MIN + RATING_MAX) / 2.0

    imputation_path = out_dir / "rating_imputation.json"
    imputation_path.write_text(
        json.dumps({"median_rating_used": median_rating, "count_with_rating": len(ratings)}),
        encoding="utf-8",
    )

    # Write interactions (submission_id when present in extract for VAE join)
    has_sub_id = any((row.get("id") or row.get("submission_id") or "").strip() for row, _ in filtered)
    header = ["student_id", "problem_idx", "order_in_seq", "r", "submitted_at"]
    if has_sub_id:
        header.append("submission_id")
    with interactions_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        order_by_user: dict[str, int] = {}
        for row, pid in filtered:
            uid = (row.get("user_id") or "").strip()
            v = (row.get("verdict") or "").strip()
            r_val = 1 if v == VERDICT_ACCEPTED else 0
            pidx = problem_idx_map[pid]
            o = order_by_user.get(uid, 0)
            order_by_user[uid] = o + 1
            out_row = [uid, pidx, o, r_val, (row.get("submitted_at") or "").strip()]
            if has_sub_id:
                sub_id = (row.get("id") or row.get("submission_id") or "").strip()
                out_row.append(sub_id)
            w.writerow(out_row)

    # problems_table
    with problems_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["problem_idx", "problem_id", "b_i", "rating", "kc_names"])
        for pid in seen_pids:
            p = prob_by_id[pid]
            raw_rating = (p.get("rating") or "").strip()
            if raw_rating:
                try:
                    rv = float(raw_rating)
                except ValueError:
                    rv = median_rating
            else:
                rv = median_rating
            b_i = _rating_to_b_i(rv, median_rating)
            kc_list = union_tags_concepts_kc_names(p.get("tags"), p.get("concepts"))
            kc_field = kc_names_to_semicolon_field(kc_list)
            rating_out = int(rv) if rv == int(rv) else rv
            w.writerow([problem_idx_map[pid], pid, f"{b_i:.8f}", rating_out, kc_field])

    print(f"Wrote {interactions_out}")
    print(f"Wrote {problems_out}")
    print(f"Wrote {imputation_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Build interactions_table and problems_table from CSV extracts.")
    p.add_argument(
        "--submissions",
        type=Path,
        default=_GPPKT.parent / "data" / "submissions_rows.csv",
        help="CSV with user_id, problem_id, verdict, submitted_at",
    )
    p.add_argument(
        "--problems",
        type=Path,
        default=_GPPKT.parent / "data" / "Problems_rows.csv",
        help="CSV with id, tags, concepts, rating (no difficulty required)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=DATA_DIR,
        help="Output directory for working tables",
    )
    args = p.parse_args()
    run(args.submissions, args.problems, args.out_dir)


if __name__ == "__main__":
    main()
