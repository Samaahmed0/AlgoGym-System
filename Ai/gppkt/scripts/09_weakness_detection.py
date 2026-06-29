from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

_SCRIPTS = Path(__file__).resolve().parent
_GPPKT = _SCRIPTS.parent
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


ds_mod = _load_script("gppkt_dataset", _SCRIPTS / "05_dataset.py")
model_mod = _load_script("gppkt_model", _SCRIPTS / "06_model.py")

from config import (  # noqa: E402
    BATCH,
    DEFAULT_INTERACTIONS,
    DEFAULT_KC_CHECKPOINT,
    DEFAULT_KC_EMBEDDINGS,
    DEFAULT_KC_GRAPH,
    DEFAULT_KC_INDEX,
    DEFAULT_EXERCISE_VECTORS,
    DEFAULT_MASTERY_REPORT,
    DEFAULT_PROBLEMS,
    DEFAULT_SEQUENCES_NPZ,
    DEFAULT_WEAKNESS_SUMMARY,
    GRAPH_SMOOTH_BETA,
    MASTERY_WEAK_THRESHOLD,
    MIN_KC_ATTEMPTS,
    TOP_N_WEAK,
)
from kc_embeddings import load_kc_sidecars  # noqa: E402
from kc_graph import build_neighbor_blend_matrix  # noqa: E402
from kc_strings import split_kc_names_field  # noqa: E402

import torch
from torch.utils.data import DataLoader


def load_student_order(interactions_path: Path) -> list[str]:
    """Same sorted student_id order as script 04."""
    with interactions_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    sids = sorted({(r.get("student_id") or "").strip() for r in rows if (r.get("student_id") or "").strip()})
    return sids


def load_problem_kcs(problems_path: Path) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    with problems_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pi = int((row.get("problem_idx") or "0").strip() or 0)
            out[pi] = split_kc_names_field(row.get("kc_names") or "")
    return out


def aggregate_attempt_counts(
    interactions_path: Path,
    problem_kcs: dict[int, list[str]],
) -> dict[str, dict[str, float]]:
    """student_id -> kc_name -> n_attempts."""
    sums: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    with interactions_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = (row.get("student_id") or "").strip()
            if not sid:
                continue
            pi = int((row.get("problem_idx") or "0").strip() or 0)
            for kc in problem_kcs.get(pi) or []:
                sums[sid][kc] += 1.0
    return {sid: dict(kc_map) for sid, kc_map in sums.items()}


def prerequisite_parents(graph_path: Path, kc_names: list[str]) -> dict[str, list[str]]:
    """to_kc -> list of from_kc prerequisites."""
    name_set = set(kc_names)
    parents: dict[str, list[str]] = defaultdict(list)
    import json

    with graph_path.open(encoding="utf-8") as f:
        for e in json.load(f):
            fr = (e.get("from_kc") or "").strip()
            to = (e.get("to_kc") or "").strip()
            if fr in name_set and to in name_set:
                parents[to].append(fr)
    return dict(parents)


@torch.no_grad()
def collect_mastery_by_student(
    npz_path: Path,
    exercise_vectors_path: Path,
    kc_embeddings_path: Path,
    checkpoint_path: Path,
    blend_matrix: torch.Tensor,
    graph_beta: float,
    device: torch.device,
    batch_size: int,
) -> dict[int, np.ndarray]:
    """student_index -> mastery vector [C] (Option C: active steps + graph blend)."""
    E_np = ds_mod.load_exercise_vectors(exercise_vectors_path)
    E = torch.from_numpy(E_np).float().to(device)
    C_np = np.load(kc_embeddings_path)
    C_emb = torch.from_numpy(C_np).float().to(device)

    ck = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = model_mod.GPPKT(E, C_emb).to(device)
    model.load_state_dict(ck["model"], strict=False)
    model.eval()

    data = np.load(npz_path)
    if "step_kc_mask" not in data:
        raise ValueError(f"{npz_path} missing step_kc_mask; rerun script 04.")

    s_count = int(data["seq_lengths"].shape[0])
    all_idx = np.arange(s_count, dtype=np.int64)
    ds = ds_mod.GPPKTDataset(npz_path, all_idx)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0)

    beta = float(graph_beta)
    out: dict[int, np.ndarray] = {}
    offset = 0
    for batch in loader:
        bsz = int(batch["seq_length"].shape[0])
        batch = {k: v.to(device) for k, v in batch.items()}
        raw = model_mod.mastery_at_active_steps(model, batch)
        if beta > 0.0:
            blended = model_mod.apply_graph_blend(raw, blend_matrix)
            mastery = (1.0 - beta) * raw + beta * blended
        else:
            mastery = raw
        for bi in range(bsz):
            out[offset + bi] = mastery[bi].cpu().numpy()
        offset += bsz
    return out


def build_weakest_n(
    practiced_sorted: list[tuple[str, float, float, int]],
    weak_sorted: list[tuple[str, float, float, int]],
    top_n: int,
) -> list[str]:
    """Weak KCs (lowest mastery first), then fill from other practiced KCs."""
    seen: set[str] = set()
    out: list[str] = []
    for kc, _, _, _ in weak_sorted:
        if kc not in seen:
            out.append(kc)
            seen.add(kc)
        if len(out) >= top_n:
            return out
    for kc, _, _, _ in practiced_sorted:
        if kc not in seen:
            out.append(kc)
            seen.add(kc)
        if len(out) >= top_n:
            break
    return out


def build_reports(
    student_ids: list[str],
    kc_names: list[str],
    mastery_by_si: dict[int, np.ndarray],
    attempt_counts: dict[str, dict[str, float]],
    kc_parents: dict[str, list[str]],
    weak_threshold: float,
) -> tuple[list[dict[str, str | int | float]], list[dict[str, str]]]:
    report_rows: list[dict[str, str | int | float]] = []
    summary_rows: list[dict[str, str]] = []

    for si, sid in enumerate(student_ids):
        mastery_vec = mastery_by_si.get(si)
        if mastery_vec is None:
            continue
        counts = attempt_counts.get(sid, {})

        practiced: list[tuple[str, float, float, int]] = []
        for cidx, kc in enumerate(kc_names):
            n_att = int(counts.get(kc, 0))
            if n_att <= 0:
                continue
            m = float(mastery_vec[cidx])
            practiced.append((kc, m, n_att, cidx))

        weak_tuples = [
            x for x in practiced if x[1] < weak_threshold and x[2] >= MIN_KC_ATTEMPTS
        ]
        weak_sorted = sorted(weak_tuples, key=lambda x: x[1])
        weak_list = sorted(kc for kc, _, _, _ in weak_tuples)

        practiced_sorted = sorted(practiced, key=lambda x: x[1])
        weakest_n = build_weakest_n(practiced_sorted, weak_sorted, TOP_N_WEAK)

        related: list[str] = []
        for kc in weak_list:
            for p in kc_parents.get(kc, []):
                if p not in weak_list and p not in related:
                    related.append(p)
        related.sort()

        rank_map = {kc: i + 1 for i, (kc, _, _, _) in enumerate(practiced_sorted)}

        summary_rows.append(
            {
                "student_id": sid,
                "weak_kcs": ";".join(weak_list),
                "n_weak": str(len(weak_list)),
                f"weakest_{TOP_N_WEAK}": ";".join(weakest_n),
                "related_kcs": ";".join(related),
            }
        )

        for kc, m, n_att, _cidx in practiced:
            report_rows.append(
                {
                    "student_id": sid,
                    "kc_name": kc,
                    "mastery": f"{m:.6f}",
                    "n_attempts": n_att,
                    "is_weak": int(m < weak_threshold and n_att >= MIN_KC_ATTEMPTS),
                    "rank": rank_map.get(kc, ""),
                }
            )

    return report_rows, summary_rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def run(
    interactions_path: Path,
    problems_path: Path,
    npz_path: Path,
    kc_index_path: Path,
    exercise_vectors_path: Path,
    kc_embeddings_path: Path,
    kc_graph_path: Path,
    checkpoint_path: Path,
    report_path: Path,
    summary_path: Path,
    device: torch.device,
    batch_size: int,
    graph_beta: float,
    weak_threshold: float,
) -> None:
    student_ids = load_student_order(interactions_path)
    if int(np.load(npz_path)["seq_lengths"].shape[0]) != len(student_ids):
        raise ValueError(
            f"NPZ student count != interactions student count "
            f"({np.load(npz_path)['seq_lengths'].shape[0]} vs {len(student_ids)}). "
            "Rebuild NPZ from the same interactions_table."
        )

    kc_names, _ = load_kc_sidecars(kc_index_path, kc_embeddings_path)
    blend = build_neighbor_blend_matrix(kc_graph_path, kc_names)
    kc_parents = prerequisite_parents(kc_graph_path, kc_names)
    problem_kcs = load_problem_kcs(problems_path)
    attempt_counts = aggregate_attempt_counts(interactions_path, problem_kcs)

    print(
        f"Option C mastery: active-step mean + graph blend beta={graph_beta} "
        f"({blend.shape[0]} KCs, {kc_graph_path.name}); weak threshold={weak_threshold}"
    )
    print(f"Running KC mastery inference for {len(student_ids)} students …")
    mastery_by_si = collect_mastery_by_student(
        npz_path,
        exercise_vectors_path,
        kc_embeddings_path,
        checkpoint_path,
        blend,
        graph_beta,
        device,
        batch_size,
    )

    report_rows, summary_rows = build_reports(
        student_ids, kc_names, mastery_by_si, attempt_counts, kc_parents, weak_threshold
    )

    report_fields = ["student_id", "kc_name", "mastery", "n_attempts", "is_weak", "rank"]
    summary_fields = [
        "student_id",
        "weak_kcs",
        "n_weak",
        f"weakest_{TOP_N_WEAK}",
        "related_kcs",
    ]
    write_csv(report_path, report_rows, report_fields)
    write_csv(summary_path, summary_rows, summary_fields)

    n_weak_students = sum(1 for r in summary_rows if int(r["n_weak"]) > 0)
    n_weak_flags = sum(int(r["is_weak"]) for r in report_rows)
    print(f"Wrote {report_path}  ({len(report_rows)} rows)")
    print(
        f"Wrote {summary_path}  ({len(summary_rows)} students, "
        f"{n_weak_students} with at least 1 weak KC, {n_weak_flags} weak flags total)"
    )


def main() -> None:
    p = argparse.ArgumentParser(description="KC mastery and weakness export (Option C)")
    p.add_argument("--interactions", type=Path, default=DEFAULT_INTERACTIONS)
    p.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS)
    p.add_argument("--npz", type=Path, default=DEFAULT_SEQUENCES_NPZ)
    p.add_argument("--kc-index", type=Path, default=DEFAULT_KC_INDEX)
    p.add_argument("--exercise-vectors", type=Path, default=DEFAULT_EXERCISE_VECTORS)
    p.add_argument("--kc-embeddings", type=Path, default=DEFAULT_KC_EMBEDDINGS)
    p.add_argument("--kc-graph", type=Path, default=DEFAULT_KC_GRAPH)
    p.add_argument("--checkpoint", type=Path, default=DEFAULT_KC_CHECKPOINT)
    p.add_argument("--report", type=Path, default=DEFAULT_MASTERY_REPORT)
    p.add_argument("--summary", type=Path, default=DEFAULT_WEAKNESS_SUMMARY)
    p.add_argument("--graph-beta", type=float, default=GRAPH_SMOOTH_BETA)
    p.add_argument(
        "--weak-threshold",
        type=float,
        default=None,
        help=f"Override MASTERY_WEAK_THRESHOLD (config default: {MASTERY_WEAK_THRESHOLD})",
    )
    p.add_argument(
        "--output-suffix",
        type=str,
        default="",
        help="Append to default CSV stems, e.g. _t05 -> mastery_report_t05.csv",
    )
    p.add_argument("--batch", type=int, default=BATCH)
    p.add_argument("--device", type=str, default="cpu")
    args = p.parse_args()

    report_path = args.report
    summary_path = args.summary
    if args.output_suffix:
        if report_path == DEFAULT_MASTERY_REPORT:
            report_path = DEFAULT_MASTERY_REPORT.with_name(
                f"mastery_report{args.output_suffix}.csv"
            )
        if summary_path == DEFAULT_WEAKNESS_SUMMARY:
            summary_path = DEFAULT_WEAKNESS_SUMMARY.with_name(
                f"weakness_summary{args.output_suffix}.csv"
            )

    weak_threshold = (
        args.weak_threshold if args.weak_threshold is not None else MASTERY_WEAK_THRESHOLD
    )

    run(
        args.interactions,
        args.problems,
        args.npz,
        args.kc_index,
        args.exercise_vectors,
        args.kc_embeddings,
        args.kc_graph,
        args.checkpoint,
        report_path,
        summary_path,
        torch.device(args.device),
        args.batch,
        args.graph_beta,
        weak_threshold,
    )


if __name__ == "__main__":
    main()
