from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import pandas as pd

from config import (
    ALLOWED_VERDICTS,
    LABEL_WINDOW,
    MAX_ROWS_PER_USER,
    MIN_PREFIX_ATTEMPTS,
    SUBMISSIONS_CSV,
    SUBMISSIONS_FALLBACK,
)
from recommender.catalog import ProblemCatalog
from recommender.kc_normalize import normalize_kc
from recommender.user_state import UserState


def _load_submissions(path: Path) -> dict[str, list[dict]]:
    by_user: dict[str, list[dict]] = defaultdict(list)
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            verdict = (row.get("verdict") or "").strip()
            if verdict not in ALLOWED_VERDICTS:
                continue
            uid = (row.get("user_id") or row.get("student_id") or "").strip()
            pid = (row.get("problem_id") or "").strip()
            if not uid or not pid:
                continue
            by_user[uid].append(
                {
                    "problem_id": pid,
                    "r": 1 if verdict == "ACCEPTED" else 0,
                    "submitted_at": row.get("submitted_at") or "",
                }
            )
    for uid in by_user:
        by_user[uid].sort(key=lambda x: x["submitted_at"])
    return dict(by_user)


def _solve_rate(counts: dict[str, list[int]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for kc, pairs in counts.items():
        if not pairs:
            continue
        out[kc] = sum(p[0] for p in pairs) / len(pairs)
    return out


def _update_kc_counts(
    counts: dict[str, list],
    problem_kcs: list[str],
    outcome: int,
) -> None:
    for kc in problem_kcs:
        if kc not in counts:
            counts[kc] = []
        counts[kc].append((outcome, 1))


def _learning_gain(
    kcs: list[str],
    before: dict[str, float],
    after: dict[str, float],
    weak_at_t: set[str],
) -> float:
    total = 0.0
    for kc in kcs:
        w = 2.0 if kc in weak_at_t else 1.0
        b = before.get(kc, 0.5)
        a = after.get(kc, b)
        total += w * (a - b)
    return total


def _prefix_user_state(
    kc_counts: dict[str, list[int]],
    weak_threshold: float = 0.4,
    min_attempts: int = 3,
) -> UserState:
    st = UserState(student_id="")
    rates = _solve_rate(kc_counts)
    for kc, rate in rates.items():
        n = len(kc_counts[kc])
        st.mastery[kc] = rate
        st.attempts[kc] = n
        if n >= min_attempts and rate < weak_threshold:
            st.weak_kcs.add(kc)
    return st


def build_training_labels(
    catalog: ProblemCatalog,
    submissions_path: Path | None = None,
    *,
    label_window: int = LABEL_WINDOW,
    min_prefix: int = MIN_PREFIX_ATTEMPTS,
    max_rows_per_user: int | None = MAX_ROWS_PER_USER,
    student_ids: set[str] | None = None,
) -> pd.DataFrame:
    path = submissions_path or SUBMISSIONS_CSV
    if not path.exists():
        path = SUBMISSIONS_FALLBACK
    by_user = _load_submissions(path)

    rows: list[dict] = []
    for uid, events in by_user.items():
        if student_ids is not None and uid not in student_ids:
            continue
        if len(events) < min_prefix + 1:
            continue

        solved: set[str] = set()
        kc_counts: dict[str, list] = defaultdict(list)
        n_added = 0

        for t, ev in enumerate(events):
            pid = ev["problem_id"]
            rec = catalog.get(pid)
            if rec is None:
                continue
            kcs = [normalize_kc(k) for k in rec.kc_names if k]
            if t < min_prefix:
                _update_kc_counts(kc_counts, kcs, ev["r"])
                if ev["r"] == 1:
                    solved.add(pid)
                continue
            if pid in solved:
                _update_kc_counts(kc_counts, kcs, ev["r"])
                continue

            before_counts = {k: list(v) for k, v in kc_counts.items()}
            before_rates = _solve_rate(before_counts)
            prefix_state = _prefix_user_state(kc_counts)
            weak_at_t = set(prefix_state.weak_kcs)

            # forward window on same user's timeline
            after_counts = {k: list(v) for k, v in kc_counts.items()}
            for j in range(t, min(t + label_window, len(events))):
                ev_j = events[j]
                rec_j = catalog.get(ev_j["problem_id"])
                if rec_j is None:
                    continue
                kcs_j = [normalize_kc(k) for k in rec_j.kc_names if k]
                _update_kc_counts(after_counts, kcs_j, ev_j["r"])
            after_rates = _solve_rate(after_counts)

            label = _learning_gain(kcs, before_rates, after_rates, weak_at_t)
            rows.append(
                {
                    "student_id": uid,
                    "problem_id": pid,
                    "timestep": t,
                    "label": label,
                }
            )
            n_added += 1
            if max_rows_per_user is not None and n_added >= max_rows_per_user:
                break

            _update_kc_counts(kc_counts, kcs, ev["r"])
            if ev["r"] == 1:
                solved.add(pid)

    return pd.DataFrame(rows)


def compute_label_at_step(
    catalog: ProblemCatalog,
    events: list[dict],
    t: int,
    problem_id: str,
    *,
    label_window: int = LABEL_WINDOW,
    min_prefix: int = MIN_PREFIX_ATTEMPTS,
) -> float | None:
    """Learning-gain label for recommending problem_id at timestep t."""
    if t < min_prefix or t >= len(events):
        return None
    rec = catalog.get(problem_id)
    if rec is None:
        return None
    kcs = [normalize_kc(k) for k in rec.kc_names if k]
    if not kcs:
        return None

    solved: set[str] = set()
    kc_counts: dict[str, list] = defaultdict(list)
    for ev in events[:t]:
        r = catalog.get(ev["problem_id"])
        if r is None:
            continue
        ekcs = [normalize_kc(k) for k in r.kc_names if k]
        _update_kc_counts(kc_counts, ekcs, ev["r"])
        if ev["r"] == 1:
            solved.add(ev["problem_id"])
    if problem_id in solved:
        return None

    before_rates = _solve_rate({k: list(v) for k, v in kc_counts.items()})
    weak_at_t = set(_prefix_user_state(kc_counts).weak_kcs)

    after_counts = {k: list(v) for k, v in kc_counts.items()}
    for j in range(t, min(t + label_window, len(events))):
        ev_j = events[j]
        rec_j = catalog.get(ev_j["problem_id"])
        if rec_j is None:
            continue
        kcs_j = [normalize_kc(k) for k in rec_j.kc_names if k]
        _update_kc_counts(after_counts, kcs_j, ev_j["r"])
    after_rates = _solve_rate(after_counts)
    return _learning_gain(kcs, before_rates, after_rates, weak_at_t)


def attach_prefix_features(
    catalog: ProblemCatalog,
    labels_df: pd.DataFrame,
    submissions_path: Path | None = None,
) -> pd.DataFrame:
    """Build feature matrix using prefix solve-rate user state per label row."""
    from recommender.features import build_features

    path = submissions_path or SUBMISSIONS_CSV
    if not path.exists():
        path = SUBMISSIONS_FALLBACK
    by_user = _load_submissions(path)

    rows = []
    for _, label_row in labels_df.iterrows():
        uid = label_row["student_id"]
        pid = label_row["problem_id"]
        t = int(label_row["timestep"])
        events = by_user.get(uid, [])
        if t > len(events):
            continue
        kc_counts: dict[str, list] = defaultdict(list)
        for ev in events[:t]:
            rec = catalog.get(ev["problem_id"])
            if rec:
                _update_kc_counts(kc_counts, [normalize_kc(k) for k in rec.kc_names if k], ev["r"])
        prefix_state = _prefix_user_state(kc_counts)
        prefix_state.student_id = uid
        prob = catalog.get(pid)
        if prob is None:
            continue
        feat = build_features(prefix_state, prob)
        rows.append({**feat, "student_id": uid, "problem_id": pid, "label": label_row["label"]})
    return pd.DataFrame(rows)
