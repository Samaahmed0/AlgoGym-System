
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from recommender.catalog import ProblemCatalog, ProblemRecord
from recommender.features import FEATURE_COLUMNS, build_features
from recommender.kc_normalize import normalize_kc
from recommender.labels import _prefix_user_state, _update_kc_counts
from recommender.user_state import UserState

FEATURE_COLUMNS_V2 = FEATURE_COLUMNS + [
    "gppkt_mean_mastery_on_kcs",
    "gppkt_min_mastery_on_kcs",
    "gppkt_weak_kc_overlap",
    "gppkt_weak_overlap_ratio",
    "prefix_gppkt_mastery_gap",
]


def is_v2_feature_schema(feature_columns: list[str]) -> bool:
    return "gppkt_mean_mastery_on_kcs" in feature_columns


def build_features_v2(
    prefix_user: UserState,
    gppkt_user: UserState,
    problem: ProblemRecord,
) -> dict[str, float]:
    """Prefix solve-rate features + static GPPKT export features per problem."""
    feat = build_features(prefix_user, problem)
    kcs = [k for k in problem.kc_names if k]
    if not kcs:
        gppkt_mean = gppkt_user.mean_mastery()
        gppkt_min = gppkt_mean
        weak_overlap = 0.0
    else:
        masteries = [gppkt_user.mastery.get(kc, 0.5) for kc in kcs]
        gppkt_mean = float(np.mean(masteries))
        gppkt_min = float(np.min(masteries))
        weak_overlap = float(sum(1 for kc in kcs if kc in gppkt_user.weak_kcs))

    ratio = weak_overlap / len(kcs) if kcs else 0.0
    feat.update(
        {
            "gppkt_mean_mastery_on_kcs": gppkt_mean,
            "gppkt_min_mastery_on_kcs": gppkt_min,
            "gppkt_weak_kc_overlap": weak_overlap,
            "gppkt_weak_overlap_ratio": ratio,
            "prefix_gppkt_mastery_gap": feat["mean_mastery_on_kcs"] - gppkt_mean,
        }
    )
    return feat


def build_prefix_user_from_submissions(
    catalog: ProblemCatalog,
    submissions_path: Path,
    student_id: str,
) -> UserState:
    """Prefix user state from full submission history (inference-time)."""
    kc_counts: dict[str, list] = defaultdict(list)
    if submissions_path.exists():
        with submissions_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                uid = (row.get("user_id") or row.get("student_id") or "").strip()
                if uid != student_id:
                    continue
                verdict = (row.get("verdict") or "").strip()
                if verdict not in {"ACCEPTED", "WRONG_ANSWER"}:
                    continue
                pid = (row.get("problem_id") or "").strip()
                rec = catalog.get(pid)
                if rec is None:
                    continue
                r = 1 if verdict == "ACCEPTED" else 0
                _update_kc_counts(
                    kc_counts,
                    [normalize_kc(k) for k in rec.kc_names if k],
                    r,
                )
    prefix_state = _prefix_user_state(kc_counts)
    prefix_state.student_id = student_id
    return prefix_state


def load_prefix_users_by_student(
    catalog: ProblemCatalog,
    submissions_path: Path,
) -> dict[str, UserState]:
    """One-pass index: student_id -> prefix UserState (for batch inference)."""
    kc_by_user: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    if not submissions_path.exists():
        return {}

    with submissions_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uid = (row.get("user_id") or row.get("student_id") or "").strip()
            if not uid:
                continue
            verdict = (row.get("verdict") or "").strip()
            if verdict not in {"ACCEPTED", "WRONG_ANSWER"}:
                continue
            pid = (row.get("problem_id") or "").strip()
            rec = catalog.get(pid)
            if rec is None:
                continue
            r = 1 if verdict == "ACCEPTED" else 0
            _update_kc_counts(
                kc_by_user[uid],
                [normalize_kc(k) for k in rec.kc_names if k],
                r,
            )

    out: dict[str, UserState] = {}
    for uid, kc_counts in kc_by_user.items():
        prefix_state = _prefix_user_state(kc_counts)
        prefix_state.student_id = uid
        out[uid] = prefix_state
    return out


def build_features_for_ranker(
    prefix_user: UserState,
    gppkt_user: UserState,
    problem: ProblemRecord,
    feature_columns: list[str],
) -> dict[str, float]:
    if is_v2_feature_schema(feature_columns):
        return build_features_v2(prefix_user, gppkt_user, problem)
    return build_features(gppkt_user, problem)
