from __future__ import annotations

import json
from pathlib import Path

import torch


def load_kc_graph_edges(
    graph_path: Path,
    name_to_idx: dict[str, int],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Prerequisite edges: from_kc (prereq) -> to_kc (dependent).

    Returns (from_idx, to_idx, weights) each [E] long/float on CPU.
    Skips edges whose endpoints are missing from name_to_idx.
    """
    with graph_path.open(encoding="utf-8") as f:
        edges = json.load(f)
    from_list: list[int] = []
    to_list: list[int] = []
    weights: list[float] = []
    for e in edges:
        fr = (e.get("from_kc") or "").strip()
        to = (e.get("to_kc") or "").strip()
        if not fr or not to:
            continue
        i = name_to_idx.get(fr)
        j = name_to_idx.get(to)
        if i is None or j is None:
            continue
        from_list.append(i)
        to_list.append(j)
        weights.append(float(e.get("weight") or 1.0))
    if not from_list:
        empty = torch.zeros(0, dtype=torch.long)
        return empty, empty.clone(), torch.zeros(0, dtype=torch.float32)
    return (
        torch.tensor(from_list, dtype=torch.long),
        torch.tensor(to_list, dtype=torch.long),
        torch.tensor(weights, dtype=torch.float32),
    )


def build_neighbor_blend_matrix(
    graph_path: Path,
    kc_names: list[str],
    self_weight: float = 1.0,
) -> torch.Tensor:
    """
    Row-stochastic blend matrix [C, C] for inference smoothing along prerequisites.
    Row c mixes mastery from c and prerequisite parents that point to c (from -> c).
    """
    c = len(kc_names)
    name_to_idx = {n: i for i, n in enumerate(kc_names)}
    blend = torch.eye(c, dtype=torch.float32) * self_weight
    with graph_path.open(encoding="utf-8") as f:
        edges = json.load(f)
    for e in edges:
        fr = (e.get("from_kc") or "").strip()
        to = (e.get("to_kc") or "").strip()
        if not fr or not to:
            continue
        i = name_to_idx.get(fr)
        j = name_to_idx.get(to)
        if i is None or j is None:
            continue
        w = float(e.get("weight") or 1.0)
        blend[j, i] += w
    row_sum = blend.sum(dim=1, keepdim=True).clamp(min=1e-8)
    return blend / row_sum
