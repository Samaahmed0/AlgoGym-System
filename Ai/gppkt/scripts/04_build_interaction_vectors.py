from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import (  # noqa: E402
    DEFAULT_CONCEPT_EMBEDDINGS,
    DEFAULT_EXERCISE_VECTORS,
    DEFAULT_INTERACTIONS,
    DEFAULT_KC_EMBEDDINGS,
    DEFAULT_KC_INDEX,
    DEFAULT_KC_VOCAB,
    DEFAULT_PROBLEMS,
    DEFAULT_SEQUENCES_NPZ,
    DEFAULT_Z_LATENT_CSV,
    SEQ_LEN,
    Z_DIM,
    Z_RAW_DIM,
)
from kc_embeddings import load_kc_embedding_matrix, save_kc_sidecars  # noqa: E402
from kc_strings import split_kc_names_field  # noqa: E402


def load_by_student(path: Path) -> dict[str, list[dict[str, str]]]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_sid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        sid = (row.get("student_id") or "").strip()
        by_sid[sid].append(row)
    for sid in by_sid:
        by_sid[sid].sort(key=lambda r: int((r.get("order_in_seq") or "0").strip() or 0))
    return dict(by_sid)


def load_problem_kc_indices(
    problems_path: Path,
    name_to_idx: dict[str, int],
) -> tuple[dict[int, list[int]], int]:
    """problem_idx -> list of kc_index; returns (map, unknown_tag_count)."""
    out: dict[int, list[int]] = {}
    unknown = 0
    with problems_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pi = int((row.get("problem_idx") or "0").strip() or 0)
            indices: list[int] = []
            for name in split_kc_names_field(row.get("kc_names")):
                idx = name_to_idx.get(name)
                if idx is None:
                    unknown += 1
                    continue
                indices.append(idx)
            out[pi] = indices
    return out, unknown


def load_z_latent(path: Path) -> dict[tuple[str, int], np.ndarray]:
    """(student_id, order_in_seq) -> z vector [Z_DIM]."""
    out: dict[tuple[str, int], np.ndarray] = {}
    z_cols = [f"z_{i}" for i in range(Z_DIM)]
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = (row.get("student_id") or "").strip()
            try:
                o = int((row.get("order_in_seq") or "").strip())
            except ValueError:
                continue
            vec = np.array([float(row.get(c) or 0) for c in z_cols], dtype=np.float32)
            if vec.shape[0] != Z_DIM:
                vec = np.resize(vec, Z_DIM)
            out[(sid, o)] = vec
    return out


def run(
    interactions_path: Path,
    problems_path: Path,
    out_npz: Path,
    seq_len: int,
    kc_vocab_path: Path,
    embeddings_path: Path,
    kc_index_path: Path,
    kc_embeddings_path: Path,
    exercise_vectors_path: Path | None,
    z_latent_path: Path | None,
    legacy_z_feat: bool,
) -> None:
    z_latent: dict[tuple[str, int], np.ndarray] | None = None
    z_source = "legacy_z_feat"
    if z_latent_path is not None and z_latent_path.exists():
        z_latent = load_z_latent(z_latent_path)
        z_source = "vae_v1"
        print(f"Loaded z_latent from {z_latent_path} ({len(z_latent)} rows)")
    elif not legacy_z_feat:
        raise SystemExit(
            f"z_latent not found at {z_latent_path}; run 03_encode_z_latent or pass --legacy-z-feat"
        )

    z_width = 4 if z_source == "legacy_z_feat" else Z_RAW_DIM
    kc_names, c_emb = load_kc_embedding_matrix(kc_vocab_path, embeddings_path)
    name_to_idx = {n: i for i, n in enumerate(kc_names)}
    save_kc_sidecars(kc_names, c_emb, kc_index_path, kc_embeddings_path)

    problem_kcs, unknown_tags = load_problem_kc_indices(problems_path, name_to_idx)
    c_count = len(kc_names)

    by_sid = load_by_student(interactions_path)
    students = sorted(by_sid.keys())
    s_count = len(students)

    problem_idx_arr = np.zeros((s_count, seq_len), dtype=np.int64)
    z_raw = np.zeros((s_count, seq_len, z_width), dtype=np.float32)
    r_t = np.zeros((s_count, seq_len), dtype=np.int64)
    theta_st = np.zeros((s_count, seq_len), dtype=np.float32)
    y_next = np.zeros((s_count, seq_len), dtype=np.int64)
    next_problem_idx = np.full((s_count, seq_len), -1, dtype=np.int64)
    next_kc_mask = np.zeros((s_count, seq_len, c_count), dtype=np.float32)
    step_kc_mask = np.zeros((s_count, seq_len, c_count), dtype=np.float32)
    seq_lengths = np.zeros(s_count, dtype=np.int64)
    loss_mask = np.zeros((s_count, seq_len), dtype=bool)

    max_pi = 0
    truncated = 0
    kc_label_count = 0
    max_tags_on_step = 0

    for si, sid in enumerate(students):
        evs = by_sid[sid]
        ell = len(evs)
        if ell > seq_len:
            evs = evs[-seq_len:]
            ell = seq_len
            truncated += 1
        seq_lengths[si] = ell

        for t in range(ell):
            row = evs[t]
            pi = int((row.get("problem_idx") or "0").strip() or 0)
            max_pi = max(max_pi, pi)
            problem_idx_arr[si, t] = pi
            r_t[si, t] = int((row.get("r") or "0").strip() or 0)
            theta_st[si, t] = float((row.get("theta") or "0").strip() or 0.0)
            oseq = int((row.get("order_in_seq") or "0").strip() or 0)
            if z_latent is not None:
                zvec = z_latent.get((sid, oseq))
                if zvec is not None:
                    z_raw[si, t, :] = zvec
            else:
                for j, k in enumerate(("z_feat_0", "z_feat_1", "z_feat_2", "z_feat_3")):
                    z_raw[si, t, j] = float((row.get(k) or "0").strip() or 0.0)
            for cidx in problem_kcs.get(pi) or []:
                step_kc_mask[si, t, cidx] = 1.0

        for t in range(ell - 1):
            y_next[si, t] = r_t[si, t + 1]
            npi = int(problem_idx_arr[si, t + 1])
            next_problem_idx[si, t] = npi
            loss_mask[si, t] = True
            kc_indices = problem_kcs.get(npi) or []
            max_tags_on_step = max(max_tags_on_step, len(kc_indices))
            for cidx in kc_indices:
                next_kc_mask[si, t, cidx] = 1.0
                kc_label_count += 1

    if truncated:
        print(
            f"Warning: kept last {seq_len} interaction(s) for {truncated} student sequence(s)"
        )
    if unknown_tags:
        print(f"Warning: skipped {unknown_tags} unknown KC tag(s) when building problem_kcs")

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_npz,
        problem_idx=problem_idx_arr,
        z_raw=z_raw,
        r_t=r_t,
        theta_st=theta_st,
        y_next=y_next,
        next_problem_idx=next_problem_idx,
        next_kc_mask=next_kc_mask,
        step_kc_mask=step_kc_mask,
        seq_lengths=seq_lengths,
        loss_mask=loss_mask,
        z_source=np.array(z_source),
        z_dim=np.int64(z_width),
    )

    if exercise_vectors_path is not None and exercise_vectors_path.exists():
        ev = np.load(exercise_vectors_path)
        if ev.shape[0] <= max_pi:
            print(
                f"Warning: max problem_idx in data ({max_pi}) >= "
                f"exercise_vectors rows ({ev.shape[0]}); check K alignment."
            )

    total_loss = int(loss_mask.sum())
    print(
        f"Wrote {out_npz}  S={s_count}  T={seq_len}  C={c_count}  "
        f"kc_labels={kc_label_count}  loss_steps={total_loss}  max_tags/step={max_tags_on_step}"
    )
    print(f"Wrote {kc_index_path}  Wrote {kc_embeddings_path} shape={c_emb.shape}")


def main() -> None:
    p = argparse.ArgumentParser(description="Build gppkt_sequences.npz from interactions_table.csv")
    p.add_argument("--interactions", type=Path, default=DEFAULT_INTERACTIONS)
    p.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS)
    p.add_argument("--out", type=Path, default=DEFAULT_SEQUENCES_NPZ)
    p.add_argument("--seq-len", type=int, default=SEQ_LEN)
    p.add_argument("--kc-vocab", type=Path, default=DEFAULT_KC_VOCAB)
    p.add_argument("--embeddings", type=Path, default=DEFAULT_CONCEPT_EMBEDDINGS)
    p.add_argument("--kc-index", type=Path, default=DEFAULT_KC_INDEX)
    p.add_argument("--kc-embeddings", type=Path, default=DEFAULT_KC_EMBEDDINGS)
    p.add_argument(
        "--exercise-vectors",
        type=Path,
        default=DEFAULT_EXERCISE_VECTORS,
        help="Optional: validate max problem_idx vs K-1",
    )
    p.add_argument("--no-validate-k", action="store_true", help="Skip exercise_vectors shape check")
    p.add_argument("--z-latent", type=Path, default=DEFAULT_Z_LATENT_CSV)
    p.add_argument(
        "--legacy-z-feat",
        action="store_true",
        help="Use z_feat_0..3 from interactions_table instead of VAE latents",
    )
    args = p.parse_args()
    ev_path = None if args.no_validate_k else args.exercise_vectors
    z_path = None if args.legacy_z_feat else args.z_latent
    run(
        args.interactions,
        args.problems,
        args.out,
        args.seq_len,
        args.kc_vocab,
        args.embeddings,
        args.kc_index,
        args.kc_embeddings,
        ev_path,
        z_path,
        args.legacy_z_feat,
    )


if __name__ == "__main__":
    main()
