
"""
Per row within a (student_id, problem_idx) episode (rows ordered by order_in_seq):
  z_feat_0 — first_result: r on the first attempt at this exercise
  z_feat_1 — min(attempt_index, Z_ATTEMPTS_MAX) / Z_ATTEMPTS_MAX
  z_feat_2 — final_result: r for this submission (current row)
  z_feat_3 — improved: 1 if previous attempt was WA and this attempt is AC, else 0

"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import DEFAULT_INTERACTIONS, Z_ATTEMPTS_MAX  # noqa: E402

_ZFEAT_COLS = ("z_feat_0", "z_feat_1", "z_feat_2", "z_feat_3")


def run(interactions_path: Path, out_path: Path, attempts_max: int) -> None:
    with interactions_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        base_fields = [c for c in (reader.fieldnames or []) if c not in _ZFEAT_COLS]
        rows = list(reader)

    # (student_id, problem_idx) -> list of (order_in_seq, row_index)
    by_ep: dict[tuple[str, int], list[tuple[int, int]]] = defaultdict(list)
    for i, row in enumerate(rows):
        sid = (row.get("student_id") or "").strip()
        pid = int((row.get("problem_idx") or "").strip())
        o = int((row.get("order_in_seq") or "").strip())
        by_ep[(sid, pid)].append((o, i))

    z_store: dict[int, tuple[float, float, float, float]] = {}

    for _key, idx_list in by_ep.items():
        idx_list.sort(key=lambda x: x[0])
        first_r: int | None = None
        prev_r: int | None = None
        for k, (_o, ri) in enumerate(idx_list):
            attempt_num = k + 1
            r = int((rows[ri].get("r") or "").strip())
            if first_r is None:
                first_r = r
            assert first_r is not None

            z0 = float(first_r)
            z1 = min(attempt_num, attempts_max) / float(attempts_max)
            z2 = float(r)
            z3 = 1.0 if (prev_r is not None and prev_r == 0 and r == 1) else 0.0

            z_store[ri] = (z0, z1, z2, z3)
            prev_r = r

    out_fields = base_fields + list(_ZFEAT_COLS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        for i, row in enumerate(rows):
            z0, z1, z2, z3 = z_store[i]
            new_row = dict(row)
            new_row["z_feat_0"] = f"{z0:.10g}"
            new_row["z_feat_1"] = f"{z1:.10g}"
            new_row["z_feat_2"] = f"{z2:.10g}"
            new_row["z_feat_3"] = f"{z3:.10g}"
            w.writerow(new_row)

    print(f"Wrote {out_path} ({len(rows)} rows, z_feat_0..3 added)")


def main() -> None:
    p = argparse.ArgumentParser(description="Append answer-summary features to interactions_table.csv")
    p.add_argument("--interactions", type=Path, default=DEFAULT_INTERACTIONS)
    p.add_argument("--out", type=Path, default=None, help="Defaults to --interactions")
    p.add_argument(
        "--attempts-max",
        type=int,
        default=Z_ATTEMPTS_MAX,
        help="Z_ATTEMPTS_MAX for z_feat_1 = min(attempts, Z_ATTEMPTS_MAX) / Z_ATTEMPTS_MAX",
    )
    args = p.parse_args()
    out = args.out if args.out is not None else args.interactions
    run(args.interactions, out, args.attempts_max)


if __name__ == "__main__":
    main()
