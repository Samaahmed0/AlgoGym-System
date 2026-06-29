from __future__ import annotations

import random

import pandas as pd

from config import (
    DIFFICULTY_EASY_MAX,
    DIFFICULTY_MEDIUM_MAX,
    DIFFICULTY_QUOTA_EASY,
    DIFFICULTY_QUOTA_HARD,
    DIFFICULTY_QUOTA_MEDIUM,
    DIFFICULTY_STRATIFY,
    FILTER_HARD_MAX_PER_KC,
    FILTER_HARD_POOL_FRACTION,
    FILTER_REMEDIAL_DIFFICULTY,
    MIN_WEAK_KC_OVERLAP,
    MMR_STRATIFY_POOL_SIZE,
    PER_KC_MASTERY_MAX_ONE_HARD,
    PER_KC_MASTERY_NO_HARD,
    PER_KC_STRATIFY,
    PER_KC_STRATIFY_USE_MMR,
    SKILL_RATING_DELTA,
    STRATIFY_USE_MMR,
    USE_WEAK_KC_SKILL,
    WEAK_FIRST_FALLBACK,
)
from recommender.catalog import ProblemCatalog, ProblemRecord
from recommender.features2 import build_features_for_ranker
from recommender.ranking3 import RankerModel
from recommender.selection import (
    ScoredCandidate,
    SelectedRecommendation,
    difficulty_band,
    mmr_select,
    per_kc_stratified_select,
    stratified_select,
)
from recommender.user_state import UserState


def _primary_weak_kc(rec: ProblemRecord, user: UserState) -> str | None:
    hits = [k for k in rec.kc_names if k in user.weak_kcs]
    if not hits:
        return None
    return min(hits, key=lambda k: user.mastery.get(k, 0.5))


def apply_remedial_difficulty_filter(
    catalog: ProblemCatalog,
    user: UserState,
    pool: list[str],
    *,
    easy_max: int = DIFFICULTY_EASY_MAX,
    medium_max: int = DIFFICULTY_MEDIUM_MAX,
    no_hard_below: float = PER_KC_MASTERY_NO_HARD,
    max_one_hard_below: float = PER_KC_MASTERY_MAX_ONE_HARD,
    hard_pool_fraction: float = FILTER_HARD_POOL_FRACTION,
    hard_max_per_kc: int = FILTER_HARD_MAX_PER_KC,
) -> list[str]:
    """Pre-ranking pool: keep all easy/medium; cap hard candidates per weak KC."""
    easy_medium: list[str] = []
    hard_by_kc: dict[str, list[tuple[int, str]]] = {}

    for pid in pool:
        rec = catalog.get(pid)
        if rec is None:
            continue
        band = difficulty_band(rec.rating, easy_max=easy_max, medium_max=medium_max)
        if band != "hard":
            easy_medium.append(pid)
            continue
        kc = _primary_weak_kc(rec, user)
        if kc is None:
            continue
        mastery = user.mastery.get(kc, 0.5)
        if mastery < no_hard_below:
            continue
        hard_by_kc.setdefault(kc, []).append((rec.rating, pid))

    kept_hard: list[str] = []
    for kc, items in hard_by_kc.items():
        mastery = user.mastery.get(kc, 0.5)
        if mastery < max_one_hard_below:
            cap = 1
        else:
            cap = max(1, int(len(items) * hard_pool_fraction))
        cap = min(cap, hard_max_per_kc)
        items.sort(key=lambda x: x[0])
        kept_hard.extend(pid for _, pid in items[:cap])

    return easy_medium + kept_hard


def filter_candidates(
    catalog: ProblemCatalog,
    user: UserState,
    solved_ids: set[str],
    *,
    skill_delta: int = SKILL_RATING_DELTA,
) -> list[str]:
    skill = user.skill_rating_estimate()
    lo, hi = skill - skill_delta, skill + skill_delta
    practiced = set(user.mastery.keys()) | user.weak_kcs

    out: list[str] = []
    for rec in catalog.iter_records():
        if rec.problem_id in solved_ids:
            continue
        if not (lo <= rec.rating <= hi):
            continue
        if practiced and not any(kc in practiced for kc in rec.kc_names):
            continue
        out.append(rec.problem_id)
    if FILTER_REMEDIAL_DIFFICULTY and user.weak_kcs:
        return apply_remedial_difficulty_filter(catalog, user, out)
    return out


def filter_weak_candidates(
    catalog: ProblemCatalog,
    user: UserState,
    solved_ids: set[str],
    *,
    min_weak_overlap: int = MIN_WEAK_KC_OVERLAP,
    fallback: bool = WEAK_FIRST_FALLBACK,
    skill_delta: int = SKILL_RATING_DELTA,
    use_weak_kc_skill: bool = USE_WEAK_KC_SKILL,
) -> list[str]:
    """Candidates that hit at least one weak KC; optional fallback to full pool."""
    if not user.weak_kcs:
        return filter_candidates(catalog, user, solved_ids, skill_delta=skill_delta)

    practiced = set(user.mastery.keys()) | user.weak_kcs
    weak_pool: list[str] = []
    for rec in catalog.iter_records():
        if rec.problem_id in solved_ids:
            continue
        overlap = sum(1 for kc in rec.kc_names if kc in user.weak_kcs)
        if overlap < min_weak_overlap:
            continue
        if practiced and not any(kc in practiced for kc in rec.kc_names):
            continue
        lo, hi = user.rating_band_for_problem(
            rec.kc_names,
            remedial=use_weak_kc_skill,
            skill_delta=skill_delta,
        )
        if not (lo <= rec.rating <= hi):
            continue
        weak_pool.append(rec.problem_id)

    if weak_pool:
        if FILTER_REMEDIAL_DIFFICULTY:
            weak_pool = apply_remedial_difficulty_filter(catalog, user, weak_pool)
        return weak_pool
    if fallback:
        pool = filter_candidates(catalog, user, solved_ids, skill_delta=skill_delta)
        return pool
    return []


def baseline_random(
    catalog: ProblemCatalog,
    user: UserState,
    solved_ids: set[str],
    top_k: int,
    rng: random.Random,
) -> list[str]:
    pool = filter_candidates(catalog, user, solved_ids)
    if len(pool) <= top_k:
        return pool
    return rng.sample(pool, top_k)


def baseline_rule_weakness(
    catalog: ProblemCatalog,
    user: UserState,
    solved_ids: set[str],
    top_k: int,
) -> list[str]:
    pool = filter_candidates(catalog, user, solved_ids)
    scored = []
    skill = user.skill_rating_estimate()
    for pid in pool:
        rec = catalog.get(pid)
        if rec is None:
            continue
        weak_overlap = sum(1 for kc in rec.kc_names if kc in user.weak_kcs)
        rating_dist = abs(rec.rating - skill)
        scored.append((weak_overlap, -rating_dist, pid))
    scored.sort(reverse=True)
    return [pid for _, _, pid in scored[:top_k]]


def score_and_select_v2(
    catalog: ProblemCatalog,
    prefix_user: UserState,
    gppkt_user: UserState,
    ranker: RankerModel,
    solved_ids: set[str],
    *,
    top_k: int = 10,
    pool_size: int | None = None,
    explore_eps: float = 0.1,
    weak_first: bool = False,
    min_weak_overlap: int = MIN_WEAK_KC_OVERLAP,
    weak_first_fallback: bool = WEAK_FIRST_FALLBACK,
) -> tuple[list[ScoredCandidate], list[SelectedRecommendation]]:
    """Score candidates and run MMR; returns (candidates, selected_recommendations)."""
    if weak_first:
        pool = filter_weak_candidates(
            catalog,
            gppkt_user,
            solved_ids,
            min_weak_overlap=min_weak_overlap,
            fallback=weak_first_fallback,
        )
    else:
        pool = filter_candidates(catalog, gppkt_user, solved_ids)

    if not pool:
        return [], []

    rows: list[dict] = []
    cands: list[ScoredCandidate] = []
    for pid in pool:
        rec = catalog.get(pid)
        if rec is None:
            continue
        rows.append(
            build_features_for_ranker(
                prefix_user, gppkt_user, rec, ranker.feature_columns
            )
        )
        cands.append(ScoredCandidate(problem_id=pid, record=rec, rank_score=0.0))

    if not cands:
        return [], []

    scores = ranker.predict(pd.DataFrame(rows))
    for i, score in enumerate(scores):
        cands[i].rank_score = float(score)

    if PER_KC_STRATIFY and weak_first and gppkt_user.weak_kcs:
        selected = per_kc_stratified_select(
            cands,
            gppkt_user,
            top_k,
            easy_max=DIFFICULTY_EASY_MAX,
            medium_max=DIFFICULTY_MEDIUM_MAX,
            use_mmr=PER_KC_STRATIFY_USE_MMR,
            no_hard_below=PER_KC_MASTERY_NO_HARD,
            max_one_hard_below=PER_KC_MASTERY_MAX_ONE_HARD,
            explore_eps=explore_eps,
        )
    elif DIFFICULTY_STRATIFY:
        stratify_pool = cands
        if STRATIFY_USE_MMR:
            mmr_k = pool_size if pool_size is not None else MMR_STRATIFY_POOL_SIZE
            mmr_k = min(mmr_k, len(cands))
            if mmr_k > top_k:
                mmr_picks = mmr_select(cands, gppkt_user, mmr_k, explore_eps=0.0)
                pick_ids = {s.problem_id for s in mmr_picks}
                stratify_pool = [c for c in cands if c.problem_id in pick_ids]
        selected = stratified_select(
            stratify_pool,
            gppkt_user,
            top_k,
            quota_easy=DIFFICULTY_QUOTA_EASY,
            quota_medium=DIFFICULTY_QUOTA_MEDIUM,
            quota_hard=DIFFICULTY_QUOTA_HARD,
            easy_max=DIFFICULTY_EASY_MAX,
            medium_max=DIFFICULTY_MEDIUM_MAX,
            explore_eps=explore_eps,
        )
    else:
        selected = mmr_select(
            cands,
            gppkt_user,
            top_k,
            pool_size=pool_size,
            explore_eps=explore_eps,
        )
    return cands, selected


def hybrid_recommend_v2(
    catalog: ProblemCatalog,
    prefix_user: UserState,
    gppkt_user: UserState,
    ranker: RankerModel,
    solved_ids: set[str],
    *,
    top_k: int = 10,
    pool_size: int | None = None,
    explore_eps: float = 0.1,
    ranking_only: bool = False,
    weak_first: bool = False,
    min_weak_overlap: int = MIN_WEAK_KC_OVERLAP,
    weak_first_fallback: bool = WEAK_FIRST_FALLBACK,
) -> list[str]:
    cands, selected = score_and_select_v2(
        catalog,
        prefix_user,
        gppkt_user,
        ranker,
        solved_ids,
        top_k=top_k,
        pool_size=pool_size,
        explore_eps=explore_eps,
        weak_first=weak_first,
        min_weak_overlap=min_weak_overlap,
        weak_first_fallback=weak_first_fallback,
    )
    if not cands:
        return []
    if ranking_only:
        cands.sort(key=lambda c: c.rank_score, reverse=True)
        return [c.problem_id for c in cands[:top_k]]
    return [s.problem_id for s in selected]
