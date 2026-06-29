from __future__ import annotations

import csv
from pathlib import Path

from config import (
    DIFFICULTY_QUOTA_EASY,
    DIFFICULTY_QUOTA_HARD,
    DIFFICULTY_QUOTA_MEDIUM,
    DIFFICULTY_STRATIFY,
    EXPLORE_EPS,
    FILTER_HARD_MAX_PER_KC,
    FILTER_HARD_POOL_FRACTION,
    FILTER_REMEDIAL_DIFFICULTY,
    MMR_STRATIFY_POOL_SIZE,
    PER_KC_STRATIFY,
    PER_KC_STRATIFY_USE_MMR,
    SELECTION_POOL_SIZE,
    STRATIFY_USE_MMR,
    TOP_K,
    USE_WEAK_KC_SKILL,
    USE_WEAKEST_N,
    WEAK_FIRST,
    WEAK_KC_SKILL_STRETCH,
    WEAKEST_N_COLUMN,
)
from recommender.baselines_v2 import score_and_select_v2
from recommender.catalog import ProblemCatalog
from recommender.cold_start import recommend_cold_start
from recommender.features2 import build_prefix_user_from_submissions
from recommender.ranking3 import RankerModel
from recommender.selection import SelectedRecommendation
from recommender.user_state import UserStateStore


def load_solved_ids(submissions_path: Path, student_id: str) -> set[str]:
    solved: set[str] = set()
    if not submissions_path.exists():
        return solved
    with submissions_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uid = (row.get("user_id") or row.get("student_id") or "").strip()
            if uid != student_id:
                continue
            if (row.get("verdict") or "").strip() == "ACCEPTED":
                pid = (row.get("problem_id") or "").strip()
                if pid:
                    solved.add(pid)
    return solved


def recommend_for_student(
    student_id: str,
    catalog: ProblemCatalog,
    user_store: UserStateStore,
    ranker: RankerModel | None,
    submissions_path: Path,
    *,
    top_k: int = TOP_K,
    pool_size: int | None = SELECTION_POOL_SIZE,
    explore_eps: float = EXPLORE_EPS,
    weak_first: bool | None = None,
    solved_ids: set[str] | None = None,
    prefix_user=None,
) -> tuple[list[SelectedRecommendation], dict]:
    meta_base = {
        "top_k": top_k,
        "mastery_source": user_store.source_files.get("mastery_report", ""),
        "weakness_source": user_store.source_files.get("weakness_summary", ""),
        "loaded_at": user_store.loaded_at,
    }

    use_weak_first = WEAK_FIRST if weak_first is None else weak_first
    if solved_ids is None:
        solved_ids = load_solved_ids(submissions_path, student_id)

    if not user_store.has_student(student_id):
        cold = recommend_cold_start(
            catalog,
            top_k=top_k,
            solved_ids=solved_ids,
            student_id=student_id,
        )
        return cold.recommendations, {
            **meta_base,
            "mode": "cold_start",
            "warning": cold.warning,
            "ranker_version": None,
        }

    if ranker is None:
        raise FileNotFoundError("artifacts/ranker.pkl required for known students (hybrid mode)")

    gppkt_user = user_store.get(student_id)
    assert gppkt_user is not None

    if prefix_user is None:
        prefix_user = build_prefix_user_from_submissions(catalog, submissions_path, student_id)
    cands, selected = score_and_select_v2(
        catalog,
        prefix_user,
        gppkt_user,
        ranker,
        solved_ids,
        top_k=top_k,
        pool_size=pool_size,
        explore_eps=explore_eps,
        weak_first=use_weak_first,
    )

    mode = "hybrid_weak_first" if use_weak_first else "hybrid_v2"
    if not cands:
        return [], {**meta_base, "mode": mode, "warning": "no candidates in pool"}

    return selected, {
        **meta_base,
        "mode": mode,
        "ranker_version": "ranker.pkl",
        "feature_version": "v2",
        "weak_first": use_weak_first,
        "use_weakest_n": USE_WEAKEST_N if use_weak_first else False,
        "weakest_n_column": WEAKEST_N_COLUMN if use_weak_first and USE_WEAKEST_N else None,
        "n_candidates": len(cands),
        "per_kc_stratify": PER_KC_STRATIFY if use_weak_first else False,
        "per_kc_stratify_use_mmr": (
            PER_KC_STRATIFY_USE_MMR if use_weak_first and PER_KC_STRATIFY else False
        ),
        "difficulty_stratify": DIFFICULTY_STRATIFY and not (
            PER_KC_STRATIFY and use_weak_first and gppkt_user.weak_kcs
        ),
        "difficulty_quotas": (
            {"easy": DIFFICULTY_QUOTA_EASY, "medium": DIFFICULTY_QUOTA_MEDIUM, "hard": DIFFICULTY_QUOTA_HARD}
            if DIFFICULTY_STRATIFY
            and not (PER_KC_STRATIFY and use_weak_first and gppkt_user.weak_kcs)
            else None
        ),
        "stratify_use_mmr": (
            STRATIFY_USE_MMR
            if DIFFICULTY_STRATIFY
            and not (PER_KC_STRATIFY and use_weak_first and gppkt_user.weak_kcs)
            else False
        ),
        "mmr_stratify_pool_size": (
            MMR_STRATIFY_POOL_SIZE
            if DIFFICULTY_STRATIFY
            and STRATIFY_USE_MMR
            and not (PER_KC_STRATIFY and use_weak_first and gppkt_user.weak_kcs)
            else None
        ),
        "use_weak_kc_skill": USE_WEAK_KC_SKILL if use_weak_first else False,
        "weak_kc_skill_stretch": WEAK_KC_SKILL_STRETCH if use_weak_first and USE_WEAK_KC_SKILL else None,
        "weak_kc_skill_rating": (
            round(gppkt_user.skill_rating_for_weak_areas(), 1)
            if use_weak_first and USE_WEAK_KC_SKILL and gppkt_user.weak_kcs
            else None
        ),
        "overall_skill_rating": round(gppkt_user.skill_rating_estimate(), 1),
        "filter_remedial_difficulty": FILTER_REMEDIAL_DIFFICULTY if use_weak_first else False,
        "filter_hard_pool_fraction": (
            FILTER_HARD_POOL_FRACTION if use_weak_first and FILTER_REMEDIAL_DIFFICULTY else None
        ),
        "filter_hard_max_per_kc": (
            FILTER_HARD_MAX_PER_KC if use_weak_first and FILTER_REMEDIAL_DIFFICULTY else None
        ),
    }
