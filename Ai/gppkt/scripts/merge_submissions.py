from __future__ import annotations

import argparse
import csv
from pathlib import Path

SLIM = ["user_id", "problem_id", "verdict", "submitted_at"]


def read_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            yield {k: (row.get(k) or "").strip() for k in SLIM}


def merge(paths: list[Path], out: Path) -> dict[str, int]:
    out.parent.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[str, str, str, str]] = set()
    stats = {"read": 0, "dupes": 0, "written": 0}

    with out.open("w", encoding="utf-8", newline="") as fout:
        w = csv.DictWriter(fout, fieldnames=SLIM)
        w.writeheader()
        for path in paths:
            for row in read_rows(path):
                stats["read"] += 1
                key = (row["user_id"], row["problem_id"], row["submitted_at"], row["verdict"])
                if key in seen:
                    stats["dupes"] += 1
                    continue
                seen.add(key)
                w.writerow(row)
                stats["written"] += 1
    return stats


def main() -> None:
    gppkt = Path(__file__).resolve().parents[1]
    ai = gppkt.parent
    p = argparse.ArgumentParser(description="Merge old + new submission CSVs (dedupe).")
    p.add_argument("--old", type=Path, default=ai / "data" / "submissions_rows.csv")
    p.add_argument(
        "--new",
        type=Path,
        default=gppkt / "data_new" / "incoming" / "submissions_hf.csv",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=gppkt / "data_new" / "incoming" / "submissions_merged.csv",
    )
    args = p.parse_args()
    for path in (args.old, args.new):
        if not path.exists():
            raise SystemExit(f"Missing input: {path}")

    stats = merge([args.old, args.new], args.out)
    print(f"Read:      {stats['read']:,}")
    print(f"Dupes:     {stats['dupes']:,}")
    print(f"Merged:    {stats['written']:,}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
