from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from config import EXPORT_SCORE_FLOOR, NORMALIZE_EXPORT_SCORES
from recommender.selection import SelectedRecommendation


def _shift_positive(values: list[float], *, floor: float = EXPORT_SCORE_FLOOR) -> list[float]:
    """Map scores to [floor, 1.0] preserving order; all values strictly positive."""
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi - lo < 1e-12:
        # Same raw score — decay slightly by list position so top item is highest.
        return [max(floor, 1.0 - 0.01 * i) for i in range(len(values))]
    return [floor + (v - lo) / (hi - lo) * (1.0 - floor) for v in values]


def normalize_recommendation_scores(
    recommendations: list[SelectedRecommendation],
) -> list[SelectedRecommendation]:
    """Export-only: make rank_score and selection_score strictly positive."""
    if not recommendations:
        return recommendations

    rank_indices = [i for i, r in enumerate(recommendations) if r.rank_score is not None]
    rank_vals = [recommendations[i].rank_score for i in rank_indices]  # type: ignore[misc]
    sel_vals = [r.selection_score for r in recommendations]

    rank_norm = _shift_positive([float(v) for v in rank_vals])
    sel_norm = _shift_positive([float(v) for v in sel_vals])

    out: list[SelectedRecommendation] = []
    rank_map = dict(zip(rank_indices, rank_norm))
    for i, rec in enumerate(recommendations):
        kwargs: dict[str, Any] = {"selection_score": sel_norm[i]}
        if i in rank_map:
            kwargs["rank_score"] = rank_map[i]
        elif rec.rank_score is None and rec.selection_score is not None:
            # Cold-start: no ranker score — mirror normalized selection for display.
            kwargs["rank_score"] = sel_norm[i]
        out.append(replace(rec, **kwargs))
    return out


def recommendations_to_dict(
    student_id: str,
    recommendations: list[SelectedRecommendation],
    meta: dict[str, Any],
) -> dict[str, Any]:
    if NORMALIZE_EXPORT_SCORES:
        recommendations = normalize_recommendation_scores(recommendations)
        meta = {**meta, "scores_normalized": True, "export_score_floor": EXPORT_SCORE_FLOOR}

    return {
        "student_id": student_id,
        "recommendations": [
            {
                "problem_id": r.problem_id,
                "rank_score": r.rank_score,
                "selection_score": r.selection_score,
                "reason": r.reason,
                "target_kcs": r.target_kcs,
                "exploration": r.exploration,
            }
            for r in recommendations
        ],
        "meta": meta,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_eval_report(path: Path, report: dict[str, Any]) -> None:
    write_json(path, report)
