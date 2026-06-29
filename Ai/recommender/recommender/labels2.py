
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd

from config import MASTERY_REPORT, SUBMISSIONS_CSV, SUBMISSIONS_FALLBACK, WEAKNESS_SUMMARY
from recommender.catalog import ProblemCatalog
from recommender.features2 import build_features_v2
from recommender.kc_normalize import normalize_kc
from recommender.labels import _load_submissions, _prefix_user_state, _update_kc_counts
from recommender.user_state import load_user_state


def attach_hybrid_features(
    catalog: ProblemCatalog,
    labels_df: pd.DataFrame,
    submissions_path: Path | None = None,
    mastery_path: Path | None = None,
    weakness_path: Path | None = None,
) -> pd.DataFrame:
    """Build v2 feature matrix: prefix state at t + GPPKT export per student."""
    sub_path = submissions_path or SUBMISSIONS_CSV
    if not sub_path.exists():
        sub_path = SUBMISSIONS_FALLBACK

    mas_path = mastery_path or MASTERY_REPORT
    weak_path = weakness_path if weakness_path is not None else WEAKNESS_SUMMARY
    if weak_path is not None and not weak_path.exists():
        weak_path = None

    by_user = _load_submissions(sub_path)
    user_store = load_user_state(mas_path, weak_path)

    rows = []
    for _, label_row in labels_df.iterrows():
        uid = label_row["student_id"]
        pid = label_row["problem_id"]
        t = int(label_row["timestep"])
        events = by_user.get(uid, [])
        if t > len(events):
            continue

        gppkt_user = user_store.get(uid)
        if gppkt_user is None:
            continue

        kc_counts: dict[str, list] = defaultdict(list)
        for ev in events[:t]:
            rec = catalog.get(ev["problem_id"])
            if rec:
                _update_kc_counts(
                    kc_counts,
                    [normalize_kc(k) for k in rec.kc_names if k],
                    ev["r"],
                )
        prefix_state = _prefix_user_state(kc_counts)
        prefix_state.student_id = uid

        prob = catalog.get(pid)
        if prob is None:
            continue

        feat = build_features_v2(prefix_state, gppkt_user, prob)
        rows.append({**feat, "student_id": uid, "problem_id": pid, "label": label_row["label"]})

    return pd.DataFrame(rows)
