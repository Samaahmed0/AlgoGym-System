from __future__ import annotations

import csv
import logging
import random
from collections import defaultdict
from pathlib import Path

from config import (
    ALLOWED_VERDICTS,
    EVAL_FORWARD_WINDOW,
    EVAL_STRIDE,
    EVAL_STUDENT_SAMPLE,
    LABEL_WINDOW,
    SEED,
)
from recommender.baselines import (
    baseline_cold_start,
    baseline_random,
    baseline_rule_weakness,
    filter_candidates,
    hybrid_recommend,
)
from recommender.catalog import ProblemCatalog
from recommender.kc_normalize import normalize_kc
from recommender.labels import _learning_gain, _solve_rate, _update_kc_counts, compute_label_at_step
from recommender.ranking import RankerModel
from recommender.user_state import UserStateStore

logger = logging.getLogger(__name__)


def load_solved_by_user(submissions_path: Path) -> dict[str, set[str]]:
    solved: dict[str, set[str]] = defaultdict(set)
    with submissions_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            verdict = (row.get("verdict") or "").strip()
            if verdict != "ACCEPTED":
                continue
            uid = (row.get("user_id") or row.get("student_id") or "").strip()
            pid = (row.get("problem_id") or "").strip()
            if uid and pid:
                solved[uid].add(pid)
    return dict(solved)


def _behavioral_gain_for_recs(
    catalog: ProblemCatalog,
    user_kc_counts: dict[str, list[tuple[int, int]]],
    rec_ids: list[str],
    forward_events: list[dict],
) -> float:
    """Gain only when user actually attempts a recommended problem in the forward window."""
    if not rec_ids or not forward_events:
        return 0.0

    before = _solve_rate(user_kc_counts)
    after_counts = {k: list(v) for k, v in user_kc_counts.items()}
    weak = {
        k
        for k, pairs in user_kc_counts.items()
        if len(pairs) >= 3 and sum(p[0] for p in pairs) / len(pairs) < 0.4
    }

    rec_set = set(rec_ids)
    gain = 0.0
    for ev in forward_events:
        if ev["problem_id"] not in rec_set:
            continue
        rec = catalog.get(ev["problem_id"])
        if rec is None:
            continue
        kcs = [normalize_kc(k) for k in rec.kc_names if k]
        _update_kc_counts(after_counts, kcs, ev["r"])
        after = _solve_rate(after_counts)
        gain += _learning_gain(kcs, before, after, weak)
        before = after

    return gain / max(len(rec_ids), 1)


def _counterfactual_gain_for_recs(
    catalog: ProblemCatalog,
    events: list[dict],
    t: int,
    rec_ids: list[str],
    *,
    label_window: int = LABEL_WINDOW,
) -> float:
    """Mean learning-gain label for recommended problems at timestep t (primary eval metric)."""
    if not rec_ids:
        return 0.0
    gains: list[float] = []
    for pid in rec_ids:
        label = compute_label_at_step(catalog, events, t, pid, label_window=label_window)
        if label is not None:
            gains.append(label)
    if not gains:
        return 0.0
    return sum(gains) / len(gains)


def _weak_kc_hit_rate(catalog: ProblemCatalog, user, rec_ids: list[str]) -> float:
    if not rec_ids or not user.weak_kcs:
        return 0.0
    hits = 0
    for pid in rec_ids:
        rec = catalog.get(pid)
        if rec and any(k in user.weak_kcs for k in rec.kc_names):
            hits += 1
    return hits / len(rec_ids)


def run_offline_eval(
    catalog: ProblemCatalog,
    user_store: UserStateStore,
    ranker: RankerModel | None,
    submissions_path: Path,
    *,
    top_k: int = 10,
    stride: int = EVAL_STRIDE,
    forward_window: int = EVAL_FORWARD_WINDOW,
    max_students: int = EVAL_STUDENT_SAMPLE,
    seed: int = SEED,
) -> dict:
    rng = random.Random(seed)
    solved_map = load_solved_by_user(submissions_path)

    by_user: dict[str, list[dict]] = defaultdict(list)
    with submissions_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            verdict = (row.get("verdict") or "").strip()
            if verdict not in ALLOWED_VERDICTS:
                continue
            uid = (row.get("user_id") or "").strip()
            pid = (row.get("problem_id") or "").strip()
            if uid and pid:
                by_user[uid].append(
                    {
                        "problem_id": pid,
                        "r": 1 if verdict == "ACCEPTED" else 0,
                        "submitted_at": row.get("submitted_at") or "",
                    }
                )

    student_ids = [s for s in by_user if user_store.has_student(s)]
    if max_students and max_students > 0 and len(student_ids) > max_students:
        student_ids = rng.sample(student_ids, max_students)

    methods = ["random", "rule_weakness", "ranking_only", "hybrid"]
    if ranker is None:
        methods = ["random", "rule_weakness", "cold_start"]

    totals = {
        m: {"cf_gain": 0.0, "beh_gain": 0.0, "weak_hit": 0.0, "n": 0} for m in methods
    }
    cold_students = [s for s in by_user if not user_store.has_student(s)]
    if cold_students:
        methods.append("cold_start")
        totals["cold_start"] = {"cf_gain": 0.0, "beh_gain": 0.0, "weak_hit": 0.0, "n": 0}

    for uid in student_ids:
        events = sorted(by_user[uid], key=lambda x: x["submitted_at"])
        user = user_store.get(uid)
        if user is None:
            continue
        solved = solved_map.get(uid, set())
        kc_counts: dict[str, list[tuple[int, int]]] = defaultdict(list)

        for t in range(0, len(events), stride):
            prefix = events[:t]
            forward = events[t : t + forward_window]
            for ev in prefix:
                rec = catalog.get(ev["problem_id"])
                if rec:
                    _update_kc_counts(kc_counts, [normalize_kc(k) for k in rec.kc_names if k], ev["r"])

            if ranker is not None:
                recs = {
                    "random": baseline_random(catalog, user, solved, top_k, rng),
                    "rule_weakness": baseline_rule_weakness(catalog, user, solved, top_k),
                    "ranking_only": hybrid_recommend(
                        catalog, user, ranker, solved, top_k=top_k, ranking_only=True
                    ),
                    "hybrid": hybrid_recommend(catalog, user, ranker, solved, top_k=top_k),
                }
            else:
                recs = {}

            for method, ids in recs.items():
                cf = _counterfactual_gain_for_recs(catalog, events, t, ids, label_window=forward_window)
                beh = _behavioral_gain_for_recs(catalog, kc_counts, ids, forward)
                totals[method]["cf_gain"] += cf
                totals[method]["beh_gain"] += beh
                totals[method]["weak_hit"] += _weak_kc_hit_rate(catalog, user, ids)
                totals[method]["n"] += 1

    for uid in cold_students[: min(50, len(cold_students))]:
        solved = solved_map.get(uid, set())
        baseline_cold_start(catalog, solved, top_k, student_id=uid, quiet=True)
        totals["cold_start"]["n"] += 1

    summary = {}
    for method, agg in totals.items():
        n = max(agg["n"], 1)
        summary[method] = {
            "avg_counterfactual_gain": agg["cf_gain"] / n,
            "avg_behavioral_gain": agg["beh_gain"] / n,
            "avg_gain_per_rec": agg["cf_gain"] / n,
            "avg_weak_kc_hit_rate": agg["weak_hit"] / n,
            "n_eval_points": agg["n"],
        }

    return {
        "methods": summary,
        "n_students_evaluated": len(student_ids),
        "n_cold_start_students_sampled": min(50, len(cold_students)),
        "top_k": top_k,
        "stride": stride,
        "forward_window": forward_window,
        "label_window": LABEL_WINDOW,
    }
