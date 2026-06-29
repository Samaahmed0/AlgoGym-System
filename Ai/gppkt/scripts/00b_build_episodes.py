
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import (  
    DEFAULT_EPISODE_NPZ,
    DEFAULT_EPISODE_STATS,
    DEFAULT_PROBLEMS,
    DEFAULT_SUBMISSIONS_RICH,
    MAX_EP_LEN,
)
from episode_features import (  
    build_verdict_vocab,
    compute_episode_arrays,
    parse_ts,
    save_verdict_vocab,
)


def _load_problem_id_to_idx(problems_path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    with problems_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = (row.get("problem_id") or "").strip()
            try:
                pidx = int((row.get("problem_idx") or "").strip())
            except ValueError:
                continue
            if pid:
                out[pid] = pidx
    return out


def _read_rich_submissions(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            clean = {k: (v or "") for k, v in row.items() if k}
            if "id" not in clean or not clean["id"].strip():
                clean["id"] = str(i + 1)
            rows.append(clean)
    return rows


def run(
    rich_path: Path,
    problems_path: Path,
    out_npz: Path,
    stats_path: Path,
    vocab_path: Path,
    max_ep_len: int,
) -> None:
    pid_to_idx = _load_problem_id_to_idx(problems_path)
    subs = _read_rich_submissions(rich_path)

    verdicts = [(r.get("verdict") or "").strip() for r in subs]
    verdict_to_id = build_verdict_vocab(verdicts)
    save_verdict_vocab(vocab_path, verdict_to_id)

    # (user_id, problem_idx) -> list of rows sorted by time
    by_ep: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    skipped_no_problem = 0
    for row in subs:
        uid = (row.get("user_id") or "").strip()
        pid = (row.get("problem_id") or "").strip()
        pidx = pid_to_idx.get(pid)
        if pidx is None:
            skipped_no_problem += 1
            continue
        by_ep[(uid, pidx)].append(row)

    def ep_sort_key(r: dict[str, str]) -> tuple[datetime, int]:
        ts = parse_ts(r.get("submitted_at") or "")
        try:
            sid = int((r.get("id") or "0").strip())
        except ValueError:
            sid = 0
        return (ts or datetime.min, sid)

    episodes: list[tuple[str, int, list[dict[str, str]]]] = []
    for key, rows in by_ep.items():
        rows.sort(key=ep_sort_key)
        episodes.append((key[0], key[1], rows))

    n_ep = len(episodes)
    ep_offsets = np.zeros(n_ep + 1, dtype=np.int64)
    lengths: list[int] = []
    trunc_count = 0

    flat_sub: list[np.ndarray] = []
    flat_vid: list[np.ndarray] = []
    flat_r: list[np.ndarray] = []
    flat_ain: list[np.ndarray] = []
    flat_imp: list[np.ndarray] = []
    flat_dt: list[np.ndarray] = []
    flat_ts: list[np.ndarray] = []
    ep_user: list[str] = []
    ep_pidx: list[int] = []

    length_hist: Counter[int] = Counter()

    for uid, pidx, rows in episodes:
        if len(rows) > max_ep_len:
            trunc_count += 1
        arrs = compute_episode_arrays(rows, verdict_to_id, max_ep_len)
        L = arrs["length"]
        lengths.append(L)
        length_hist[L] += 1
        ep_user.append(uid)
        ep_pidx.append(pidx)
        flat_sub.append(arrs["submission_id"])
        flat_vid.append(arrs["verdict_id"])
        flat_r.append(arrs["r_ac_wa"])
        flat_ain.append(arrs["attempt_index_norm"])
        flat_imp.append(arrs["improved"])
        flat_dt.append(arrs["dt_log_hours"])
        flat_ts.append(arrs["submitted_at_unix"])

    total_steps = sum(lengths)
    ep_offsets[1:] = np.cumsum(np.array(lengths, dtype=np.int64))

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_npz,
        n_episodes=np.int64(n_ep),
        ep_offsets=ep_offsets,
        ep_user_id=np.array(ep_user, dtype=object),
        ep_problem_idx=np.array(ep_pidx, dtype=np.int64),
        submission_id=np.concatenate(flat_sub) if flat_sub else np.zeros(0, dtype=np.int64),
        verdict_id=np.concatenate(flat_vid) if flat_vid else np.zeros(0, dtype=np.int64),
        r_ac_wa=np.concatenate(flat_r) if flat_r else np.zeros(0, dtype=np.float32),
        attempt_index_norm=np.concatenate(flat_ain) if flat_ain else np.zeros(0, dtype=np.float32),
        improved=np.concatenate(flat_imp) if flat_imp else np.zeros(0, dtype=np.float32),
        dt_log_hours=np.concatenate(flat_dt) if flat_dt else np.zeros(0, dtype=np.float32),
        submitted_at_unix=np.concatenate(flat_ts) if flat_ts else np.zeros(0, dtype=np.float64),
        max_ep_len=np.int64(max_ep_len),
        n_verdicts=np.int64(len(verdict_to_id)),
    )

    verdict_counts = Counter(verdicts)
    stats = {
        "n_episodes": n_ep,
        "total_attempt_steps": int(total_steps),
        "truncated_episodes": trunc_count,
        "skipped_no_problem_idx": skipped_no_problem,
        "max_ep_len": max_ep_len,
        "length_histogram": {str(k): v for k, v in sorted(length_hist.items())},
        "verdict_counts": dict(verdict_counts.most_common(30)),
        "n_verdict_types": len(verdict_to_id),
    }
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print(f"Wrote {out_npz}  episodes={n_ep}  steps={total_steps}  verdict_types={len(verdict_to_id)}")
    print(f"Wrote {stats_path}  Wrote {vocab_path}")
    if trunc_count:
        print(f"Warning: truncated {trunc_count} episodes to max_ep_len={max_ep_len}")


def main() -> None:
    p = argparse.ArgumentParser(description="Build episode_attempts.npz from submissions_rich.csv")
    p.add_argument("--rich", type=Path, default=DEFAULT_SUBMISSIONS_RICH)
    p.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS)
    p.add_argument("--out", type=Path, default=DEFAULT_EPISODE_NPZ)
    p.add_argument("--stats", type=Path, default=DEFAULT_EPISODE_STATS)
    p.add_argument(
        "--vocab",
        type=Path,
        default=None,
        help="verdict_vocab.json path (default: next to --out)",
    )
    p.add_argument("--max-ep-len", type=int, default=MAX_EP_LEN)
    args = p.parse_args()
    vocab = args.vocab or args.out.parent / "verdict_vocab.json"
    run(args.rich, args.problems, args.out, args.stats, vocab, args.max_ep_len)


if __name__ == "__main__":
    main()
