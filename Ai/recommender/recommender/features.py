
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from recommender.catalog import ProblemRecord
from recommender.kc_normalize import normalize_kc_list
from recommender.user_state import UserState

FEATURE_COLUMNS = [
    "mean_mastery_on_kcs",
    "min_mastery_on_kcs",
    "weak_kc_overlap",
    "weak_overlap_ratio",
    "max_weak_gap",
    "total_attempts_on_kcs",
    "problem_rating",
    "normalized_rating",
    "n_kcs",
    "rating_minus_skill",
    "mean_user_mastery",
]


@dataclass
class FeatureRow:
    student_id: str
    problem_id: str
    features: dict[str, float]
    label: float | None = None


def build_features(user: UserState, problem: ProblemRecord) -> dict[str, float]:
    kcs = normalize_kc_list(problem.kc_names)
    if not kcs:
        kcs = [""]

    masteries = [user.mastery.get(kc, 0.5) for kc in kcs if kc]
    attempts = [user.attempts.get(kc, 0) for kc in kcs if kc]
    weak_overlap = sum(1 for kc in kcs if kc in user.weak_kcs)

    mean_m = float(np.mean(masteries)) if masteries else 0.5
    min_m = float(np.min(masteries)) if masteries else 0.5
    max_gap = max((0.4 - user.mastery.get(kc, 0.5)) for kc in kcs if kc in user.weak_kcs) if weak_overlap else 0.0
    max_gap = max(0.0, max_gap)

    skill = user.skill_rating_estimate()
    ratio = weak_overlap / len(kcs) if kcs else 0.0

    return {
        "mean_mastery_on_kcs": mean_m,
        "min_mastery_on_kcs": min_m,
        "weak_kc_overlap": float(weak_overlap),
        "weak_overlap_ratio": ratio,
        "max_weak_gap": max_gap,
        "total_attempts_on_kcs": float(sum(attempts)),
        "problem_rating": float(problem.rating),
        "normalized_rating": problem.normalized_rating,
        "n_kcs": float(len(kcs)),
        "rating_minus_skill": float(problem.rating) - skill,
        "mean_user_mastery": user.mean_mastery(),
    }


def features_to_vector(feat: dict[str, float]) -> np.ndarray:
    return np.array([feat[c] for c in FEATURE_COLUMNS], dtype=np.float32)


def features_dataframe(rows: list[FeatureRow]) -> pd.DataFrame:
    data = []
    for r in rows:
        row = {"student_id": r.student_id, "problem_id": r.problem_id, **r.features}
        if r.label is not None:
            row["label"] = r.label
        data.append(row)
    return pd.DataFrame(data)
