
from __future__ import annotations

import random

from config import SKILL_RATING_DELTA
from recommender.catalog import ProblemCatalog
from recommender.ranking import RankerModel
from recommender.selection import ScoredCandidate, mmr_select
from recommender.user_state import UserState


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
    return out


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


def hybrid_recommend(
    catalog: ProblemCatalog,
    user: UserState,
    ranker: RankerModel,
    solved_ids: set[str],
    *,
    top_k: int = 10,
    pool_size: int | None = None,
    explore_eps: float = 0.1,
    ranking_only: bool = False,
) -> list[str]:
    pool = filter_candidates(catalog, user, solved_ids)
    if not pool:
        return []

    rows = []
    cands: list[ScoredCandidate] = []
    for pid in pool:
        rec = catalog.get(pid)
        if rec is None:
            continue
        from recommender.features import build_features

        rows.append(build_features(user, rec))
        cands.append(ScoredCandidate(problem_id=pid, record=rec, rank_score=0.0))

    if not cands:
        return []

    import pandas as pd

    scores = ranker.predict(pd.DataFrame(rows))
    for i, score in enumerate(scores):
        cands[i].rank_score = float(score)

    if ranking_only:
        cands.sort(key=lambda c: c.rank_score, reverse=True)
        return [c.problem_id for c in cands[:top_k]]

    selected = mmr_select(
        cands,
        user,
        top_k,
        pool_size=pool_size,
        explore_eps=explore_eps,
    )
    return [s.problem_id for s in selected]
