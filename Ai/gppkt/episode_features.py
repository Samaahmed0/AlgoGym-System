from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

from config import MAX_EP_LEN, VERDICT_ACCEPTED, VERDICT_WRONG_ANSWER

R_AC_WA_MISSING = -1.0
CONT_FEAT_NAMES = ("attempt_index_norm", "improved", "dt_log_hours", "r_ac_wa_scalar")


def parse_ts(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        norm = s.replace("Z", "+00:00")
        if "T" not in norm and " " in norm:
            norm = norm.replace(" ", "T", 1)
        return datetime.fromisoformat(norm)
    except ValueError:
        return None


def build_verdict_vocab(verdicts: list[str]) -> dict[str, int]:
    counts = Counter(v.strip() for v in verdicts if v.strip())
    ordered = sorted(counts.keys(), key=lambda x: (-counts[x], x))
    return {v: i for i, v in enumerate(ordered)}


def verdict_to_r_ac_wa(verdict: str) -> float:
    v = (verdict or "").strip()
    if v == VERDICT_ACCEPTED:
        return 1.0
    if v == VERDICT_WRONG_ANSWER:
        return 0.0
    return R_AC_WA_MISSING


def compute_episode_arrays(
    attempts: list[dict[str, str]],
    verdict_to_id: dict[str, int],
    max_ep_len: int = MAX_EP_LEN,
) -> dict[str, np.ndarray]:
    """
    attempts: sorted list of dicts with verdict, submitted_at, id (submission_id).
    Truncates oldest if len > max_ep_len.
    """
    if len(attempts) > max_ep_len:
        attempts = attempts[-max_ep_len:]

    n = len(attempts)
    submission_id = np.zeros(n, dtype=np.int64)
    submitted_at_unix = np.zeros(n, dtype=np.float64)
    verdict_id = np.zeros(n, dtype=np.int64)
    r_ac_wa = np.full(n, R_AC_WA_MISSING, dtype=np.float32)
    attempt_index_norm = np.zeros(n, dtype=np.float32)
    improved = np.zeros(n, dtype=np.float32)
    dt_log_hours = np.zeros(n, dtype=np.float32)

    prev_r: float | None = None
    prev_ts: datetime | None = None

    for i, row in enumerate(attempts):
        sid = (row.get("id") or row.get("submission_id") or "").strip()
        try:
            submission_id[i] = int(sid)
        except ValueError:
            submission_id[i] = i + 1

        v = (row.get("verdict") or "").strip()
        verdict_id[i] = verdict_to_id.get(v, 0)
        r = verdict_to_r_ac_wa(v)
        r_ac_wa[i] = r
        attempt_index_norm[i] = min(i + 1, max_ep_len) / float(max_ep_len)

        if prev_r is not None and prev_r == 0.0 and r == 1.0:
            improved[i] = 1.0

        ts = parse_ts(row.get("submitted_at") or "")
        if ts is not None:
            submitted_at_unix[i] = ts.timestamp()
        if prev_ts is not None and ts is not None:
            delta_h = max(0.0, (ts - prev_ts).total_seconds() / 3600.0)
            dt_log_hours[i] = math.log1p(delta_h)

        prev_r = r if r >= 0 else prev_r
        prev_ts = ts if ts is not None else prev_ts

    return {
        "submission_id": submission_id,
        "submitted_at_unix": submitted_at_unix,
        "verdict_id": verdict_id,
        "r_ac_wa": r_ac_wa,
        "attempt_index_norm": attempt_index_norm,
        "improved": improved,
        "dt_log_hours": dt_log_hours,
        "length": n,
    }


def save_verdict_vocab(path: Path, verdict_to_id: dict[str, int]) -> None:
    path.write_text(json.dumps(verdict_to_id, indent=2), encoding="utf-8")


def load_verdict_vocab(path: Path) -> dict[str, int]:
    return json.loads(path.read_text(encoding="utf-8"))
