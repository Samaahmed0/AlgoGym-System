
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from config import EXPLORE_EPS, SELECTION_POOL_SIZE, TOP_K
from recommender.baselines import filter_candidates, hybrid_recommend
from recommender.catalog import ProblemCatalog
from recommender.cold_start import recommend_cold_start
from recommender.ranking import RankerModel
from recommender.selection import SelectedRecommendation, mmr_select, ScoredCandidate
from recommender.features import build_features
from recommender.user_state import UserStateStore

import pandas as pd


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
) -> tuple[list[SelectedRecommendation], dict]:
    meta_base = {
        "top_k": top_k,
        "mastery_source": user_store.source_files.get("mastery_report", ""),
        "weakness_source": user_store.source_files.get("weakness_summary", ""),
        "loaded_at": user_store.loaded_at,
    }

    solved = load_solved_ids(submissions_path, student_id)

    if not user_store.has_student(student_id):
        cold = recommend_cold_start(
            catalog,
            top_k=top_k,
            solved_ids=solved,
            student_id=student_id,
        )
        meta = {
            **meta_base,
            "mode": "cold_start",
            "warning": cold.warning,
            "ranker_version": None,
        }
        return cold.recommendations, meta

    if ranker is None:
        raise FileNotFoundError("ranker.pkl required for known students (hybrid mode)")

    user = user_store.get(student_id)
    assert user is not None

    pool = filter_candidates(catalog, user, solved)
    cands: list[ScoredCandidate] = []
    rows = []
    for pid in pool:
        rec = catalog.get(pid)
        if rec is None:
            continue
        feat = build_features(user, rec)
        rows.append(feat)
        cands.append(ScoredCandidate(problem_id=pid, record=rec, rank_score=0.0))

    if not cands:
        return [], {**meta_base, "mode": "hybrid", "warning": "no candidates in pool"}

    X = pd.DataFrame(rows)
    scores = ranker.predict(X)
    for i, s in enumerate(scores):
        cands[i].rank_score = float(s)

    selected = mmr_select(
        cands,
        user,
        top_k,
        pool_size=pool_size,
        explore_eps=explore_eps,
    )
    meta = {
        **meta_base,
        "mode": "hybrid",
        "ranker_version": "ranker.pkl",
        "n_candidates": len(cands),
    }
    return selected, meta
