
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import (  # noqa: E402
    DATA_DIR,
    DEFAULT_CONCEPT_EMBEDDINGS,
    DEFAULT_EXERCISE_VECTORS,
    DEFAULT_KC_VOCAB,
    DEFAULT_PROBLEMS,
)
from kc_strings import split_kc_names_field  # noqa: E402


def load_kc_vocab(path: Path) -> dict[str, int]:
    m: dict[str, int] = {}
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            name = (row.get("kc_name") or "").strip()
            eid = (row.get("entity_id") or "").strip()
            if not name or not eid:
                continue
            m[name] = int(eid)
    return m


def load_embeddings_matrix(path: Path) -> np.ndarray:
    """Dense matrix indexed by entity_id (row i = embedding for entity i)."""
    rows: list[tuple[int, list[float]]] = []
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        fieldnames = r.fieldnames or []
        if not fieldnames or fieldnames[0].strip().lower() != "entity_id":
            raise SystemExit("concept_embeddings.csv must start with entity_id column")
        for row in r:
            eid_s = (row.get(fieldnames[0]) or "").strip()
            if not eid_s:
                continue
            eid = int(eid_s)
            vec = [float(row[c]) for c in fieldnames[1:] if c in row]
            rows.append((eid, vec))
    if not rows:
        raise SystemExit("No embedding rows loaded")
    d = len(rows[0][1])
    max_id = max(eid for eid, _ in rows)
    mat = np.zeros((max_id + 1, d), dtype=np.float64)
    for eid, vec in rows:
        if len(vec) != d:
            raise SystemExit(f"Inconsistent embedding dim for entity_id={eid}")
        mat[eid] = vec
    return mat


def entity_vec(mat: np.ndarray, entity_id: int) -> np.ndarray:
    if entity_id < 0 or entity_id >= mat.shape[0]:
        return np.zeros(mat.shape[1], dtype=np.float64)
    return mat[entity_id]


def run(
    problems_path: Path,
    kc_vocab_path: Path,
    embeddings_path: Path,
    out_path: Path,
    mismatch_path: Path,
) -> None:
    kc_to_eid = load_kc_vocab(kc_vocab_path)
    mat = load_embeddings_matrix(embeddings_path)
    d = mat.shape[1]

    problem_rows: list[dict[str, str]] = []
    with problems_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            problem_rows.append(row)

    if not problem_rows:
        raise SystemExit("Empty problems_table")

    max_idx = max(int((r.get("problem_idx") or "0").strip() or 0) for r in problem_rows)
    k = max_idx + 1
    out = np.zeros((k, d), dtype=np.float32)

    mismatches: list[str] = []
    for row in problem_rows:
        pidx = int((row.get("problem_idx") or "").strip())
        names = split_kc_names_field(row.get("kc_names"))
        acc = np.zeros(d, dtype=np.float64)
        for name in names:
            eid = kc_to_eid.get(name)
            if eid is None:
                mismatches.append(f"{pidx}\t{name}")
                continue
            acc += entity_vec(mat, eid)
        out[pidx] = acc.astype(np.float32)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, out)

    body = "problem_idx\tunknown_kc\n" + "\n".join(mismatches) if mismatches else "(none)\n"
    mismatch_path.write_text(body, encoding="utf-8")
    print(f"Wrote {out_path} shape={out.shape}")
    print(f"Wrote {mismatch_path} ({len(mismatches)} unknown names)")


def main() -> None:
    p = argparse.ArgumentParser(description="Build exercise_vectors.npy from problems_table.")
    p.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS)
    p.add_argument("--kc-vocab", type=Path, default=DEFAULT_KC_VOCAB)
    p.add_argument("--embeddings", type=Path, default=DEFAULT_CONCEPT_EMBEDDINGS)
    p.add_argument("--out", type=Path, default=DEFAULT_EXERCISE_VECTORS)
    p.add_argument(
        "--mismatch-report",
        type=Path,
        default=DATA_DIR / "kc_mismatch_report.txt",
    )
    args = p.parse_args()
    run(args.problems, args.kc_vocab, args.embeddings, args.out, args.mismatch_report)


if __name__ == "__main__":
    main()
