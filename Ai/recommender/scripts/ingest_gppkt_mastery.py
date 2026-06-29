from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GPPKT = ROOT.parent / "gppkt" / "data_new" / "option_c"
WEAKNESS_CSV = GPPKT / "weakness_summary_infer_only.csv"
MASTERY_CSV = GPPKT / "mastery_report_infer_only.csv"

BATCH = 2000


def get_conn():
    try:
        import psycopg2
    except ImportError:
        print("Install psycopg2-binary: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Set DATABASE_URL (postgresql://...)", file=sys.stderr)
        sys.exit(1)
    return psycopg2.connect(url)


def ingest_weakness(cur, df: pd.DataFrame) -> int:
    rows = [
        (
            r.student_id,
            None if pd.isna(r.weak_kcs) or r.weak_kcs == "" else str(r.weak_kcs),
            int(r.n_weak) if not pd.isna(r.n_weak) else 0,
            str(r.weakest_5),
            None if pd.isna(r.related_kcs) or r.related_kcs == "" else str(r.related_kcs),
        )
        for r in df.itertuples(index=False)
    ]
    sql = """
        INSERT INTO user_weakness_summary (user_id, weak_kcs, n_weak, weakest_5, related_kcs)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            weak_kcs = EXCLUDED.weak_kcs,
            n_weak = EXCLUDED.n_weak,
            weakest_5 = EXCLUDED.weakest_5,
            related_kcs = EXCLUDED.related_kcs
    """
    cur.executemany(sql, rows)
    return len(rows)


def ingest_mastery(cur, df: pd.DataFrame) -> int:
    total = 0
    buf = []
    sql = """
        INSERT INTO user_kc_mastery (user_id, kc_name, mastery, n_attempts, is_weak, rank)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, kc_name) DO UPDATE SET
            mastery = EXCLUDED.mastery,
            n_attempts = EXCLUDED.n_attempts,
            is_weak = EXCLUDED.is_weak,
            rank = EXCLUDED.rank
    """
    for r in df.itertuples(index=False):
        is_weak = bool(int(r.is_weak)) if not pd.isna(r.is_weak) else False
        rank = int(r.rank) if not pd.isna(r.rank) else None
        n_attempts = int(r.n_attempts) if not pd.isna(r.n_attempts) else 0
        buf.append(
            (r.student_id, str(r.kc_name), float(r.mastery), n_attempts, is_weak, rank)
        )
        if len(buf) >= BATCH:
            cur.executemany(sql, buf)
            total += len(buf)
            buf.clear()
    if buf:
        cur.executemany(sql, buf)
        total += len(buf)
    return total


def main():
    parser = argparse.ArgumentParser(description="Ingest GPPKT mastery CSVs into Postgres")
    parser.add_argument("--all", action="store_true", help="Ingest all users (~10k)")
    parser.add_argument("--user-ids", nargs="+", help="Ingest specific student_ids (e.g. user7)")
    args = parser.parse_args()

    if not args.all and not args.user_ids:
        parser.error("Pass --all or --user-ids")

    if not WEAKNESS_CSV.exists() or not MASTERY_CSV.exists():
        print(f"Missing CSV under {GPPKT}", file=sys.stderr)
        sys.exit(1)

    weak_df = pd.read_csv(WEAKNESS_CSV)
    mastery_df = pd.read_csv(MASTERY_CSV)

    if args.user_ids:
        ids = set(args.user_ids)
        weak_df = weak_df[weak_df["student_id"].isin(ids)]
        mastery_df = mastery_df[mastery_df["student_id"].isin(ids)]

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                n_weak = ingest_weakness(cur, weak_df)
                n_mastery = ingest_mastery(cur, mastery_df)
        print(f"Ingested weakness rows: {n_weak}, mastery rows: {n_mastery}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
