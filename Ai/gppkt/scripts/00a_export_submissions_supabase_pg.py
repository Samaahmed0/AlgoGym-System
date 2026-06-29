
from __future__ import annotations

import argparse
import csv
import os
import re
from pathlib import Path


def _parse_backend_application_properties(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _jdbc_to_pg_params(jdbc_url: str) -> tuple[str, int, str]:
    m = re.match(r"^jdbc:postgresql://([^/:]+)(?::(\d+))?/([^?]+)", jdbc_url.strip())
    if not m:
        raise ValueError(f"Unrecognized JDBC url: {jdbc_url!r}")
    host = m.group(1)
    port = int(m.group(2) or "5432")
    dbname = m.group(3)
    return host, port, dbname


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


_RICH_SELECT = (
    "SELECT id, user_id, problem_id, verdict, submitted_at "
    "FROM public.submissions "
    "ORDER BY submitted_at NULLS LAST, id"
)
_SLIM_SELECT = (
    "SELECT user_id, problem_id, verdict, submitted_at "
    "FROM public.submissions "
    "ORDER BY submitted_at NULLS LAST, id"
)


def export_submissions_pg(
    *,
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
    out_csv: Path,
    sslmode: str,
    slim: bool,
) -> None:
    inner = _SLIM_SELECT if slim else _RICH_SELECT
    copy_sql = f"COPY ({inner}) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)"

    try:
        import psycopg  # type: ignore

        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode=sslmode,
        )
        _ensure_parent(out_csv)
        with conn:
            with conn.cursor() as cur:
                with out_csv.open("wb") as f:
                    with cur.copy(copy_sql) as copy:
                        for data in copy:
                            f.write(bytes(data))
        conn.close()
        return
    except ModuleNotFoundError:
        pass

    import psycopg2  # type: ignore

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode=sslmode,
    )
    _ensure_parent(out_csv)
    try:
        with conn.cursor() as cur:
            with out_csv.open("w", encoding="utf-8", newline="") as f:
                cur.copy_expert(copy_sql, f)
    finally:
        conn.close()


def build_rich_from_csv(in_csv: Path, out_csv: Path) -> None:
    """Build submissions_rich.csv from slim CSV; assign id 1..N if missing."""
    with in_csv.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"No rows in {in_csv}")

    fieldnames = list(rows[0].keys())
    has_id = "id" in fieldnames
    out_fields = ["id", "user_id", "problem_id", "verdict", "submitted_at"]

    _ensure_parent(out_csv)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        for i, row in enumerate(rows, start=1):
            sid = (row.get("id") or "").strip() if has_id else ""
            w.writerow(
                {
                    "id": sid or str(i),
                    "user_id": (row.get("user_id") or "").strip(),
                    "problem_id": (row.get("problem_id") or "").strip(),
                    "verdict": (row.get("verdict") or "").strip(),
                    "submitted_at": (row.get("submitted_at") or "").strip(),
                }
            )
    print(f"Wrote {out_csv} ({len(rows)} rows, id={'present' if has_id else 'synthetic'})")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    _GPPKT = Path(__file__).resolve().parents[1]
    sys_path_insert = _GPPKT
    import sys

    if str(sys_path_insert) not in sys.path:
        sys.path.insert(0, str(sys_path_insert))
    from config import DATA_DIR, DEFAULT_SUBMISSIONS_RICH  # noqa: E402

    default_backend_props = repo_root / "Backend" / "src" / "main" / "resources" / "application.properties"
    default_slim_out = repo_root / "Ai" / "data" / "submissions_rows.csv"

    p = argparse.ArgumentParser(description="Export submissions CSV (rich or slim) from Postgres or local CSV.")
    p.add_argument("--out", type=Path, default=None, help="Output CSV path.")
    p.add_argument("--slim", action="store_true", help="4-column slim export (no id).")
    p.add_argument(
        "--from-csv",
        type=Path,
        default=None,
        help="Build rich CSV from local slim file (adds id if missing); skips Postgres.",
    )
    p.add_argument(
        "--backend-properties",
        type=Path,
        default=default_backend_props,
    )
    p.add_argument("--host", type=str, default=os.getenv("PGHOST", ""))
    p.add_argument("--port", type=int, default=int(os.getenv("PGPORT", "0") or "0"))
    p.add_argument("--dbname", type=str, default=os.getenv("PGDATABASE", ""))
    p.add_argument("--user", type=str, default=os.getenv("PGUSER", ""))
    p.add_argument("--password", type=str, default=os.getenv("PGPASSWORD", ""))
    p.add_argument("--sslmode", type=str, default=os.getenv("PGSSLMODE", "require"))
    args = p.parse_args()

    if args.from_csv is not None:
        out = args.out or DEFAULT_SUBMISSIONS_RICH
        build_rich_from_csv(args.from_csv, out)
        return

    out = args.out or (default_slim_out if args.slim else DEFAULT_SUBMISSIONS_RICH)

    props = _parse_backend_application_properties(args.backend_properties)
    jdbc = props.get("spring.datasource.url", "")
    host, port, dbname = _jdbc_to_pg_params(jdbc) if jdbc else ("", 0, "")
    user = props.get("spring.datasource.username", "")
    password = props.get("spring.datasource.password", "")

    final_host = args.host or host
    final_port = args.port or port
    final_dbname = args.dbname or dbname
    final_user = args.user or user
    final_password = args.password or password

    missing = [
        k
        for k, v in [
            ("host", final_host),
            ("port", final_port),
            ("dbname", final_dbname),
            ("user", final_user),
            ("password", final_password),
        ]
        if not v
    ]
    if missing:
        raise SystemExit(
            "Missing connection fields: "
            + ", ".join(missing)
            + ". Use --from-csv for offline rich build, or set PG* / Backend properties."
        )

    export_submissions_pg(
        host=str(final_host),
        port=int(final_port),
        dbname=str(final_dbname),
        user=str(final_user),
        password=str(final_password),
        out_csv=out,
        sslmode=args.sslmode,
        slim=args.slim,
    )
    print(f"Wrote {out} ({'slim' if args.slim else 'rich'})")


if __name__ == "__main__":
    main()
