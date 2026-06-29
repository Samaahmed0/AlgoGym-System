
from __future__ import annotations

import random
from dataclasses import dataclass

from recommender.catalog import ProblemRecord
from recommender.user_state import UserState

MMR_DIVERSITY_PENALTY = 0.3
BAND_SELECTION_ADJ = 0.02


@dataclass
class ScoredCandidate:
    problem_id: str
    record: ProblemRecord
    rank_score: float


@dataclass
class SelectedRecommendation:
    problem_id: str
    rank_score: float | None
    selection_score: float
    reason: str
    target_kcs: list[str]
    exploration: bool = False


def _catalog_topic(cand: ScoredCandidate) -> str:
    rec = cand.record
    return rec.parent_topic or (rec.kc_names[0] if rec.kc_names else "")


def _diversity_key(cand: ScoredCandidate, user: UserState, *, for_export: bool) -> str:
    """Export: penalize repeated weak KCs; picking: penalize repeated catalog topics."""
    if for_export and user.weak_kcs:
        pk = _primary_weak_kc(cand, user)
        if pk:
            return pk
    return _catalog_topic(cand)


def _band_selection_adjustment(
    cand: ScoredCandidate,
    *,
    easy_max: int = 1199,
    medium_max: int = 1599,
) -> float:
    band = difficulty_band(cand.record.rating, easy_max=easy_max, medium_max=medium_max)
    return _band_sort_key(band) * BAND_SELECTION_ADJ


def _export_selection_score(
    cand: ScoredCandidate,
    user: UserState,
    seen_keys: set[str],
    *,
    easy_max: int = 1199,
    medium_max: int = 1599,
) -> float:
    """Final JSON score: rank − weak-KC MMR penalty − difficulty band adjustment."""
    key = _diversity_key(cand, user, for_export=True)
    penalty = MMR_DIVERSITY_PENALTY if key in seen_keys else 0.0
    return (
        cand.rank_score
        - penalty
        - _band_selection_adjustment(cand, easy_max=easy_max, medium_max=medium_max)
    )


def _pick_mmr_score(
    cand: ScoredCandidate,
    user: UserState,
    seen_topics: set[str],
    *,
    easy_max: int = 1199,
    medium_max: int = 1599,
) -> float:
    """Score used while picking: catalog-topic MMR + band adjustment."""
    topic = _diversity_key(cand, user, for_export=False)
    penalty = MMR_DIVERSITY_PENALTY if topic in seen_topics else 0.0
    return (
        cand.rank_score
        - penalty
        - _band_selection_adjustment(cand, easy_max=easy_max, medium_max=medium_max)
    )


def _recommendations_with_mmr_scores(
    chosen: list[ScoredCandidate],
    user: UserState,
    *,
    easy_max: int = 1199,
    medium_max: int = 1599,
) -> list[SelectedRecommendation]:
    """Export selection_score with weak-KC MMR + difficulty adjustment in list order."""
    selected: list[SelectedRecommendation] = []
    seen_keys: set[str] = set()
    for cand in chosen:
        key = _diversity_key(cand, user, for_export=True)
        eff = _export_selection_score(cand, user, seen_keys, easy_max=easy_max, medium_max=medium_max)
        selected.append(_to_recommendation(cand, user, eff))
        seen_keys.add(key)
    return selected


def _weak_hits_sorted(user: UserState, rec: ProblemRecord) -> list[str]:
    hits = [k for k in rec.kc_names if k in user.weak_kcs]
    return sorted(hits, key=lambda k: user.mastery.get(k, 0.5))


def _reason_hybrid(user: UserState, rec: ProblemRecord, weak_hits: list[str]) -> str:
    if weak_hits:
        top = weak_hits[0]
        m = user.mastery.get(top, 0.0)
        return f"Targets weak KC: {top} (mastery {m:.2f}). Rating {rec.rating}."
    return f"Rating {rec.rating}. Covers: {', '.join(rec.kc_names[:3])}."


def _primary_weak_kc(cand: ScoredCandidate, user: UserState) -> str | None:
    weak_on = _weak_hits_sorted(user, cand.record)
    return weak_on[0] if weak_on else None


def difficulty_band(rating: int, *, easy_max: int = 1199, medium_max: int = 1599) -> str:
    """Easy/Medium/Hard bands matching Backend ProblemService."""
    if rating <= easy_max:
        return "easy"
    if rating <= medium_max:
        return "medium"
    return "hard"


def _band_sort_key(band: str) -> int:
    return {"easy": 0, "medium": 1, "hard": 2}.get(band, 1)


def _to_recommendation(
    cand: ScoredCandidate,
    user: UserState,
    selection_score: float,
    *,
    exploration: bool = False,
) -> SelectedRecommendation:
    weak_hits = _weak_hits_sorted(user, cand.record)
    reason = _reason_hybrid(user, cand.record, weak_hits)
    if exploration:
        reason += " (exploration)"
    return SelectedRecommendation(
        problem_id=cand.problem_id,
        rank_score=cand.rank_score,
        selection_score=selection_score,
        reason=reason,
        target_kcs=cand.record.kc_names[:5],
        exploration=exploration,
    )


def stratified_select(
    candidates: list[ScoredCandidate],
    user: UserState,
    top_k: int,
    *,
    quota_easy: int = 4,
    quota_medium: int = 4,
    quota_hard: int = 2,
    easy_max: int = 1199,
    medium_max: int = 1599,
    explore_eps: float = 0.1,
    seed: int = 42,
) -> list[SelectedRecommendation]:
    """Top-K with Easy/Medium/Hard quotas; final order easy → medium → hard by rating."""
    if not candidates:
        return []

    quotas = {"easy": quota_easy, "medium": quota_medium, "hard": quota_hard}
    if sum(quotas.values()) != top_k:
        raise ValueError(f"Difficulty quotas must sum to top_k={top_k}")

    rng = random.Random(seed)
    buckets: dict[str, list[ScoredCandidate]] = {"easy": [], "medium": [], "hard": []}
    for cand in candidates:
        band = difficulty_band(cand.record.rating, easy_max=easy_max, medium_max=medium_max)
        buckets[band].append(cand)
    for band in buckets:
        buckets[band].sort(key=lambda c: c.rank_score, reverse=True)

    chosen: list[ScoredCandidate] = []
    chosen_ids: set[str] = set()
    unfilled = 0

    for band in ("easy", "medium", "hard"):
        need = quotas[band]
        taken = 0
        for cand in buckets[band]:
            if taken >= need:
                break
            if cand.problem_id in chosen_ids:
                continue
            chosen.append(cand)
            chosen_ids.add(cand.problem_id)
            taken += 1
        unfilled += need - taken

    if unfilled > 0:
        remaining = [c for c in candidates if c.problem_id not in chosen_ids]
        remaining.sort(
            key=lambda c: (
                _band_sort_key(
                    difficulty_band(c.record.rating, easy_max=easy_max, medium_max=medium_max)
                ),
                -c.rank_score,
            )
        )
        for cand in remaining[:unfilled]:
            chosen.append(cand)
            chosen_ids.add(cand.problem_id)

    chosen.sort(
        key=lambda c: (
            _band_sort_key(
                difficulty_band(c.record.rating, easy_max=easy_max, medium_max=medium_max)
            ),
            c.record.rating,
            -c.rank_score,
        )
    )

    selected = _recommendations_with_mmr_scores(
        chosen[:top_k], user, easy_max=easy_max, medium_max=medium_max
    )
    by_id = {c.problem_id: c for c in candidates}

    def _rec_sort_key(rec: SelectedRecommendation) -> tuple:
        cand = by_id[rec.problem_id]
        band = difficulty_band(cand.record.rating, easy_max=easy_max, medium_max=medium_max)
        return (_band_sort_key(band), cand.record.rating, -(rec.rank_score or 0))

    if selected and explore_eps > 0 and rng.random() < explore_eps:
        remaining = [
            c
            for c in sorted(candidates, key=lambda x: x.rank_score, reverse=True)
            if c.problem_id not in {s.problem_id for s in selected}
        ]
        if remaining:
            swap_idx = rng.randrange(len(selected))
            pick = rng.choice(remaining[: max(20, top_k)])
            seen_keys = {
                _diversity_key(chosen[i], user, for_export=True)
                for i in range(len(chosen[:top_k]))
                if i != swap_idx
            }
            selected[swap_idx] = _to_recommendation(
                pick,
                user,
                _export_selection_score(
                    pick, user, seen_keys, easy_max=easy_max, medium_max=medium_max
                ),
                exploration=True,
            )
            selected.sort(key=_rec_sort_key)

    return selected


def _allocate_kc_slots(kcs: list[str], top_k: int) -> dict[str, int]:
    """Split top_k across weak KCs; weakest (first in list) get +1 from remainder."""
    if not kcs:
        return {}
    base, rem = divmod(top_k, len(kcs))
    alloc = {kc: base for kc in kcs}
    for i in range(rem):
        alloc[kcs[i]] += 1
    return alloc


def _kc_quotas_for_slots(
    n: int,
    mastery: float,
    *,
    no_hard_below: float = 0.4,
    max_one_hard_below: float = 0.45,
) -> tuple[int, int, int]:
    """Easy/Medium/Hard quotas for n slots on one KC, gated by mastery."""
    if n <= 0:
        return 0, 0, 0
    if mastery < no_hard_below:
        q_hard = 0
        q_easy = min(1, n)
        q_med = n - q_easy
    elif mastery < max_one_hard_below:
        q_hard = min(1, n)
        q_easy = min(1, max(0, n - q_hard - 1))
        q_med = n - q_easy - q_hard
    else:
        q_easy = max(0, round(n * 0.4))
        q_med = max(0, round(n * 0.4))
        q_hard = n - q_easy - q_med
        if q_hard < 0:
            q_med += q_hard
            q_hard = 0
    total = q_easy + q_med + q_hard
    while total > n:
        if q_med > 0:
            q_med -= 1
        elif q_easy > 0:
            q_easy -= 1
        else:
            q_hard -= 1
        total -= 1
    while total < n:
        q_med += 1
        total += 1
    return q_easy, q_med, q_hard


def _mmr_shortlist(
    candidates: list[ScoredCandidate],
    user: UserState,
    shortlist_k: int,
    *,
    easy_max: int = 1199,
    medium_max: int = 1599,
) -> list[ScoredCandidate]:
    if shortlist_k >= len(candidates):
        return list(candidates)
    picks = mmr_select(
        candidates,
        user,
        shortlist_k,
        explore_eps=0.0,
        easy_max=easy_max,
        medium_max=medium_max,
    )
    pick_ids = {p.problem_id for p in picks}
    return [c for c in candidates if c.problem_id in pick_ids]


def per_kc_stratified_select(
    candidates: list[ScoredCandidate],
    user: UserState,
    top_k: int,
    *,
    easy_max: int = 1199,
    medium_max: int = 1599,
    use_mmr: bool = True,
    no_hard_below: float = 0.4,
    max_one_hard_below: float = 0.45,
    explore_eps: float = 0.1,
    seed: int = 42,
) -> list[SelectedRecommendation]:
    """Allocate Top-K across weak KCs; MMR + stratify inside each concept."""
    if not candidates:
        return []
    if not user.weak_kcs:
        return stratified_select(
            candidates,
            user,
            top_k,
            easy_max=easy_max,
            medium_max=medium_max,
            explore_eps=explore_eps,
            seed=seed,
        )

    groups: dict[str, list[ScoredCandidate]] = {}
    for cand in candidates:
        kc = _primary_weak_kc(cand, user)
        if kc:
            groups.setdefault(kc, []).append(cand)

    active_kcs = sorted(
        [kc for kc in user.weak_kcs if groups.get(kc)],
        key=lambda k: user.mastery.get(k, 0.5),
    )
    if not active_kcs:
        return stratified_select(
            candidates,
            user,
            top_k,
            easy_max=easy_max,
            medium_max=medium_max,
            explore_eps=explore_eps,
            seed=seed,
        )

    slot_alloc = _allocate_kc_slots(active_kcs, top_k)
    chosen: list[ScoredCandidate] = []
    chosen_ids: set[str] = set()
    by_id = {c.problem_id: c for c in candidates}

    for kc in active_kcs:
        n = slot_alloc.get(kc, 0)
        if n <= 0:
            continue
        kc_pool = groups[kc]
        mastery = user.mastery.get(kc, 0.5)
        q_easy, q_med, q_hard = _kc_quotas_for_slots(
            n,
            mastery,
            no_hard_below=no_hard_below,
            max_one_hard_below=max_one_hard_below,
        )

        shortlist = kc_pool
        if use_mmr:
            mmr_k = min(len(kc_pool), max(n * 3, n + 5))
            if mmr_k > n:
                shortlist = _mmr_shortlist(
                    kc_pool, user, mmr_k, easy_max=easy_max, medium_max=medium_max
                )

        kc_recs = stratified_select(
            shortlist,
            user,
            n,
            quota_easy=q_easy,
            quota_medium=q_med,
            quota_hard=q_hard,
            easy_max=easy_max,
            medium_max=medium_max,
            explore_eps=0.0,
            seed=seed,
        )
        for rec in kc_recs:
            if rec.problem_id in chosen_ids:
                continue
            cand = by_id.get(rec.problem_id)
            if cand is not None:
                chosen.append(cand)
                chosen_ids.add(rec.problem_id)

    if len(chosen) < top_k:
        remaining = sorted(
            [c for c in candidates if c.problem_id not in chosen_ids],
            key=lambda c: -c.rank_score,
        )
        for cand in remaining:
            if len(chosen) >= top_k:
                break
            chosen.append(cand)
            chosen_ids.add(cand.problem_id)

    chosen = chosen[:top_k]
    chosen.sort(
        key=lambda c: (
            user.mastery.get(_primary_weak_kc(c, user) or "", 0.5),
            _band_sort_key(
                difficulty_band(c.record.rating, easy_max=easy_max, medium_max=medium_max)
            ),
            c.record.rating,
            -c.rank_score,
        )
    )

    selected = _recommendations_with_mmr_scores(
        chosen, user, easy_max=easy_max, medium_max=medium_max
    )
    rng = random.Random(seed)

    if selected and explore_eps > 0 and rng.random() < explore_eps:
        swap_idx = rng.randrange(len(selected))
        swap_cand = chosen[swap_idx]
        primary = _primary_weak_kc(swap_cand, user)
        pool = [
            c
            for c in candidates
            if c.problem_id not in chosen_ids and _primary_weak_kc(c, user) == primary
        ]
        if not pool:
            pool = [c for c in candidates if c.problem_id not in chosen_ids]
        if pool:
            pool.sort(key=lambda c: -c.rank_score)
            pick = rng.choice(pool[: max(10, top_k)])
            seen_keys = {
                _diversity_key(chosen[i], user, for_export=True)
                for i in range(len(chosen))
                if i != swap_idx
            }
            selected[swap_idx] = _to_recommendation(
                pick,
                user,
                _export_selection_score(
                    pick, user, seen_keys, easy_max=easy_max, medium_max=medium_max
                ),
                exploration=True,
            )

    return selected


def mmr_select(
    candidates: list[ScoredCandidate],
    user: UserState,
    top_k: int,
    *,
    pool_size: int | None = None,
    explore_eps: float = 0.1,
    seed: int = 42,
    easy_max: int = 1199,
    medium_max: int = 1599,
) -> list[SelectedRecommendation]:
    if not candidates:
        return []

    rng = random.Random(seed)
    sorted_cands = sorted(candidates, key=lambda c: c.rank_score, reverse=True)
    pool = sorted_cands if pool_size is None else sorted_cands[:pool_size]

    selected: list[SelectedRecommendation] = []
    selected_topics: set[str] = set()

    while len(selected) < top_k and pool:
        best_idx = 0
        best_score = -1e9
        for i, cand in enumerate(pool):
            score = _pick_mmr_score(
                cand, user, selected_topics, easy_max=easy_max, medium_max=medium_max
            )
            if score > best_score:
                best_score = score
                best_idx = i
        cand = pool.pop(best_idx)
        selected_topics.add(_diversity_key(cand, user, for_export=False))
        selected.append(_to_recommendation(cand, user, best_score))

    if selected and explore_eps > 0 and rng.random() < explore_eps:
        remaining = [c for c in sorted_cands if c.problem_id not in {s.problem_id for s in selected}]
        if remaining:
            swap_idx = rng.randrange(len(selected))
            pick = rng.choice(remaining[: max(20, top_k)])
            swap_pid = selected[swap_idx].problem_id
            other_topics = {
                _diversity_key(c, user, for_export=False)
                for c in sorted_cands
                if c.problem_id in {s.problem_id for s in selected}
                and c.problem_id != swap_pid
            }
            selected[swap_idx] = _to_recommendation(
                pick,
                user,
                _pick_mmr_score(
                    pick, user, other_topics, easy_max=easy_max, medium_max=medium_max
                ),
                exploration=True,
            )

    return selected
