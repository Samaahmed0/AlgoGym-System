from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


def load_kc_vocab(path: Path) -> dict[str, int]:
    """kc_name -> entity_id."""
    m: dict[str, int] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
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
            raise ValueError("concept_embeddings.csv must start with entity_id column")
        for row in r:
            eid_s = (row.get(fieldnames[0]) or "").strip()
            if not eid_s:
                continue
            eid = int(eid_s)
            vec = [float(row[c]) for c in fieldnames[1:] if c in row]
            rows.append((eid, vec))
    if not rows:
        raise ValueError("No embedding rows loaded")
    d = len(rows[0][1])
    max_id = max(eid for eid, _ in rows)
    mat = np.zeros((max_id + 1, d), dtype=np.float64)
    for eid, vec in rows:
        if len(vec) != d:
            raise ValueError(f"Inconsistent embedding dim for entity_id={eid}")
        mat[eid] = vec
    return mat


def entity_vec(mat: np.ndarray, entity_id: int) -> np.ndarray:
    if entity_id < 0 or entity_id >= mat.shape[0]:
        return np.zeros(mat.shape[1], dtype=np.float64)
    return mat[entity_id]


def load_kc_index(kc_vocab_path: Path) -> tuple[list[str], dict[str, int]]:
    """Stable sorted kc_names and name -> kc_index (0 .. C-1)."""
    kc_to_eid = load_kc_vocab(kc_vocab_path)
    names = sorted(kc_to_eid.keys())
    name_to_idx = {n: i for i, n in enumerate(names)}
    return names, name_to_idx


def load_kc_embedding_matrix(
    kc_vocab_path: Path,
    embeddings_path: Path,
) -> tuple[list[str], np.ndarray]:
    """Return (kc_names, C_emb) with C_emb shape [C, d]."""
    names, name_to_idx = load_kc_index(kc_vocab_path)
    kc_to_eid = load_kc_vocab(kc_vocab_path)
    mat = load_embeddings_matrix(embeddings_path)
    d = mat.shape[1]
    c_emb = np.zeros((len(names), d), dtype=np.float32)
    for name, idx in name_to_idx.items():
        eid = kc_to_eid[name]
        c_emb[idx] = entity_vec(mat, eid).astype(np.float32)
    return names, c_emb


def save_kc_sidecars(
    kc_names: list[str],
    c_emb: np.ndarray,
    index_path: Path,
    embeddings_path: Path,
) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps({"kc_names": kc_names}, indent=2), encoding="utf-8")
    np.save(embeddings_path, c_emb)


def load_kc_sidecars(
    index_path: Path,
    embeddings_path: Path,
) -> tuple[list[str], np.ndarray]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    names: list[str] = list(data["kc_names"])
    c_emb = np.load(embeddings_path)
    if c_emb.shape[0] != len(names):
        raise ValueError(
            f"kc_embeddings rows ({c_emb.shape[0]}) != kc_index length ({len(names)})"
        )
    return names, c_emb.astype(np.float32)
