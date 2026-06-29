
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import DEFAULT_INTERACTIONS, DEFAULT_PROBLEMS, IRT_D, IRT_P_CLIP  # noqa: E402


def load_b_per_problem(problems_path: Path) -> dict[int, float]:
    out: dict[int, float] = {}
    with problems_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            idx = int((row.get("problem_idx") or "").strip())
            b_s = (row.get("b_i") or "").strip()
            out[idx] = float(b_s)
    return out


def clip_p(p: float) -> float:
    lo, hi = IRT_P_CLIP, 1.0 - IRT_P_CLIP
    return max(lo, min(hi, p))


def theta_from_b_and_p(b: float, p: float) -> float:
    p_c = clip_p(p)
    return b + (1.0 / IRT_D) * math.log(p_c / (1.0 - p_c))


def run(interactions_path: Path, problems_path: Path, out_path: Path) -> None:
    b_map = load_b_per_problem(problems_path)
    missing_b = False

    with interactions_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if "theta" in fieldnames:
            fieldnames = [c for c in fieldnames if c != "theta"]
        rows = list(reader)

    # Cumulative (correct, total) per (student_id, problem_idx), file order = timeline
    counts: dict[tuple[str, int], tuple[int, int]] = {}
    out_rows: list[dict[str, str]] = []

    for row in rows:
        sid = (row.get("student_id") or "").strip()
        pidx = int((row.get("problem_idx") or "").strip())
        r = int((row.get("r") or "").strip())

        key = (sid, pidx)
        c0, t0 = counts.get(key, (0, 0))
        t0 += 1
        c0 += r
        counts[key] = (c0, t0)
        p = c0 / t0 if t0 > 0 else IRT_P_CLIP

        b_i = b_map.get(pidx)
        if b_i is None:
            missing_b = True
            th = float("nan")
        else:
            th = theta_from_b_and_p(b_i, p)

        new_row = dict(row)
        new_row["theta"] = f"{th:.10g}" if not math.isnan(th) else ""
        out_rows.append(new_row)

    out_fields = fieldnames + ["theta"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    if missing_b:
        print("Warning: some problem_idx missing from problems_table; theta left empty for those rows.")
    print(f"Wrote {out_path} ({len(out_rows)} rows, theta column added)")


def main() -> None:
    p = argparse.ArgumentParser(description="Append IRT theta to interactions_table.csv")
    p.add_argument("--interactions", type=Path, default=DEFAULT_INTERACTIONS)
    p.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS)
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Defaults to --interactions (overwrite)",
    )
    args = p.parse_args()
    out = args.out if args.out is not None else args.interactions
    run(args.interactions, args.problems, out)


if __name__ == "__main__":
    main()
