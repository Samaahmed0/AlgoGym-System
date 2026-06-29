
from __future__ import annotations

import csv
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
    WEAK_FIRST,
)
from recommender.baselines_v2 import (
    baseline_random,
    baseline_rule_weakness,
    hybrid_recommend_v2,
)
from recommender.catalog import ProblemCatalog
from recommender.eval import (
    _behavioral_gain_for_recs,
    _counterfactual_gain_for_recs,
    _weak_kc_hit_rate,
    load_solved_by_user,
)
from recommender.kc_normalize import normalize_kc
from recommender.labels import _prefix_user_state, _update_kc_counts
from recommender.ranking3 import RankerModel
from recommender.user_state import UserStateStore


def run_offline_eval_v2(
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
    weak_first: bool = WEAK_FIRST,
) -> dict:
    if ranker is None:
        raise ValueError("v2 eval requires a trained ranker")

    rng = random.Random(seed)
    solved_map = load_solved_by_user(submissions_path)

    by_user: dict[str, list[dict]] = defaultdict(list)
    with submissions_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            verdict = (row.get("verdict") or "").strip()
            if verdict not in ALLOWED_VERDICTS:
                continue
            uid = (row.get("user_id") or row.get("student_id") or "").strip()
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

    methods = ["random", "rule_weakness", "hybrid_v2", "hybrid_weak_first"]
    totals = {m: {"cf_gain": 0.0, "beh_gain": 0.0, "weak_hit": 0.0, "n": 0} for m in methods}

    for uid in student_ids:
        events = sorted(by_user[uid], key=lambda x: x["submitted_at"])
        gppkt_user = user_store.get(uid)
        if gppkt_user is None:
            continue
        solved = solved_map.get(uid, set())
        kc_counts: dict[str, list[tuple[int, int]]] = defaultdict(list)

        for t in range(0, len(events), stride):
            forward = events[t : t + forward_window]
            for ev in events[:t]:
                rec = catalog.get(ev["problem_id"])
                if rec:
                    _update_kc_counts(
                        kc_counts,
                        [normalize_kc(k) for k in rec.kc_names if k],
                        ev["r"],
                    )

            prefix_user = _prefix_user_state(kc_counts)
            prefix_user.student_id = uid

            recs = {
                "random": baseline_random(catalog, gppkt_user, solved, top_k, rng),
                "rule_weakness": baseline_rule_weakness(catalog, gppkt_user, solved, top_k),
                "hybrid_v2": hybrid_recommend_v2(
                    catalog,
                    prefix_user,
                    gppkt_user,
                    ranker,
                    solved,
                    top_k=top_k,
                    weak_first=False,
                ),
                "hybrid_weak_first": hybrid_recommend_v2(
                    catalog,
                    prefix_user,
                    gppkt_user,
                    ranker,
                    solved,
                    top_k=top_k,
                    weak_first=True,
                ),
            }

            for method, ids in recs.items():
                cf = _counterfactual_gain_for_recs(
                    catalog, events, t, ids, label_window=forward_window
                )
                beh = _behavioral_gain_for_recs(catalog, kc_counts, ids, forward)
                totals[method]["cf_gain"] += cf
                totals[method]["beh_gain"] += beh
                totals[method]["weak_hit"] += _weak_kc_hit_rate(catalog, gppkt_user, ids)
                totals[method]["n"] += 1

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
        "top_k": top_k,
        "stride": stride,
        "forward_window": forward_window,
        "label_window": LABEL_WINDOW,
        "feature_version": "v2",
        "weak_first_default": weak_first,
    }
