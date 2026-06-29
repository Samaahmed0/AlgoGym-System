
from __future__ import annotations

import logging
from dataclasses import dataclass

from config import COLD_START_RATING_MAX, COLD_START_RATING_MIN
from recommender.catalog import ProblemCatalog
from recommender.selection import SelectedRecommendation

logger = logging.getLogger(__name__)


@dataclass
class ColdStartResult:
    recommendations: list[SelectedRecommendation]
    warning: str


def recommend_cold_start(
    catalog: ProblemCatalog,
    *,
    top_k: int = 10,
    solved_ids: set[str] | None = None,
    rating_min: int = COLD_START_RATING_MIN,
    rating_max: int = COLD_START_RATING_MAX,
    student_id: str = "",
    quiet: bool = False,
) -> ColdStartResult:
    solved_ids = solved_ids or set()
    kc_freq = catalog.global_kc_frequencies()
    if not kc_freq:
        return ColdStartResult([], "empty catalog")

    top_kcs = sorted(kc_freq.keys(), key=lambda k: kc_freq[k], reverse=True)[:20]
    top_kc_set = set(top_kcs)

    candidates = []
    for rec in catalog.iter_records():
        if rec.problem_id in solved_ids:
            continue
        if not (rating_min <= rec.rating <= rating_max):
            continue
        overlap = sum(1 for kc in rec.kc_names if kc in top_kc_set)
        if overlap == 0:
            continue
        candidates.append((overlap, rec.rating, rec))

    candidates.sort(key=lambda x: (-x[0], x[1]))

    selected: list[SelectedRecommendation] = []
    used_topics: set[str] = set()
    for overlap, _rating, rec in candidates:
        if len(selected) >= top_k:
            break
        topic = rec.parent_topic or (rec.kc_names[0] if rec.kc_names else "")
        if topic in used_topics:
            continue
        used_topics.add(topic)
        common = [kc for kc in rec.kc_names if kc in top_kc_set][:3]
        selected.append(
            SelectedRecommendation(
                problem_id=rec.problem_id,
                rank_score=None,
                selection_score=float(overlap),
                reason=(
                    f"Cold-start: starter problem (rating {rec.rating}). "
                    f"Covers common KCs: {', '.join(common)}."
                ),
                target_kcs=rec.kc_names[:5],
            )
        )

    warning = (
        f"WARNING: cold-start recommendation for student_id={student_id} - "
        "not found in mastery report; using rule-based fallback."
    )
    if not quiet:
        logger.warning(warning)

    return ColdStartResult(recommendations=selected, warning=warning)
