
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import (  # noqa: E402
    DEFAULT_EPISODE_NPZ,
    DEFAULT_INTERACTIONS,
    DEFAULT_VAE_CHECKPOINT,
    DEFAULT_Z_LATENT_CSV,
    ENCODE_UNMATCHED_MAX_FRAC,
    Z_DIM,
)
from episode_features import parse_ts  # noqa: E402
from episode_vae import EpisodeVAE, cont_from_batch  # noqa: E402


def _build_episode_lookup(data: dict) -> dict[tuple[str, int], int]:
    out: dict[tuple[str, int], int] = {}
    for ei in range(int(data["n_episodes"])):
        u = str(data["ep_user_id"][ei])
        p = int(data["ep_problem_idx"][ei])
        out[(u, p)] = ei
    return out


def _resolve_ep_step(
    row: dict[str, str],
    sub_to_ep_step: dict[int, tuple[int, int]],
    ep_lookup: dict[tuple[str, int], int],
    data: dict,
) -> tuple[int | None, int | None]:
    sub_raw = (row.get("submission_id") or "").strip()
    if sub_raw:
        try:
            sid = int(sub_raw)
            hit = sub_to_ep_step.get(sid)
            if hit is not None:
                return hit
        except ValueError:
            pass

    student_id = (row.get("student_id") or "").strip()
    try:
        pidx = int((row.get("problem_idx") or "").strip())
    except ValueError:
        return None, None
    ep_idx = ep_lookup.get((student_id, pidx))
    if ep_idx is None:
        return None, None

    ts_row = parse_ts(row.get("submitted_at") or "")
    start = int(data["ep_offsets"][ep_idx])
    end = int(data["ep_offsets"][ep_idx + 1])
    if ts_row is None:
        return ep_idx, end - start - 1

    target = ts_row.timestamp()
    ts_arr = data["submitted_at_unix"][start:end]
    best_t = 0
    best_diff = float("inf")
    for t in range(end - start):
        raw = float(ts_arr[t])
        if raw <= 0:
            continue
        diff = abs(raw - target)
        if diff < best_diff:
            best_diff = diff
            best_t = t
    if best_diff > 3600.0:
        return None, None
    return ep_idx, best_t


def _build_submission_index(data: dict) -> dict[int, tuple[int, int]]:
    """submission_id -> (episode_index, step_index within episode)."""
    out: dict[int, tuple[int, int]] = {}
    n_ep = int(data["n_episodes"])
    for ei in range(n_ep):
        start = int(data["ep_offsets"][ei])
        end = int(data["ep_offsets"][ei + 1])
        for t, sid in enumerate(data["submission_id"][start:end]):
            out[int(sid)] = (ei, t)
    return out


def _episode_rows_by_user_problem(
    interactions_path: Path,
) -> dict[tuple[str, int], list[dict[str, str]]]:
    with interactions_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_key: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        sid = (row.get("student_id") or "").strip()
        try:
            pidx = int((row.get("problem_idx") or "").strip())
        except ValueError:
            continue
        by_key[(sid, pidx)].append(row)
    return dict(by_key)


def _encode_prefix(
    model: EpisodeVAE,
    data: dict,
    ep_idx: int,
    end_step: int,
    device: torch.device,
) -> np.ndarray:
    start = int(data["ep_offsets"][ep_idx])
    end = int(data["ep_offsets"][ep_idx + 1])
    end = min(end, start + end_step + 1)
    length = end - start
    if length <= 0:
        return np.zeros(Z_DIM, dtype=np.float32)

    def seg(name: str, dtype=torch.long):
        s = data[name][start:end]
        t = torch.as_tensor(s, dtype=dtype)
        if t.dim() == 1:
            return t.unsqueeze(0)
        return t.unsqueeze(0)

    verdict_id = seg("verdict_id").to(device)
    r_ac_wa = seg("r_ac_wa", dtype=torch.float32).float().to(device)
    attempt_index_norm = seg("attempt_index_norm", dtype=torch.float32).float().to(device)
    improved = seg("improved", dtype=torch.float32).float().to(device)
    dt_log_hours = seg("dt_log_hours", dtype=torch.float32).float().to(device)
    lengths = torch.tensor([length], dtype=torch.long, device=device)

    cont = cont_from_batch(attempt_index_norm, improved, dt_log_hours, r_ac_wa)
    model.eval()
    with torch.no_grad():
        mu, _ = model.encode(verdict_id, cont, lengths)
    return mu.squeeze(0).cpu().numpy().astype(np.float32)


def run(
    interactions_path: Path,
    episode_npz: Path,
    ckpt_path: Path,
    out_csv: Path,
    max_unmatched_frac: float,
) -> None:
    raw = np.load(episode_npz, allow_pickle=True)
    data = {k: raw[k] for k in raw.files}
    sub_to_ep_step = _build_submission_index(data)
    ep_lookup = _build_episode_lookup(data)

    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    n_verdicts = int(ck["n_verdicts"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = EpisodeVAE(n_verdicts=n_verdicts, z_dim=Z_DIM).to(device)
    model.load_state_dict(ck["model"])
    model.eval()

    with interactions_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    z_cols = [f"z_{i}" for i in range(Z_DIM)]
    out_fields = ["student_id", "order_in_seq"] + z_cols

    matched = 0
    unmatched = 0
    out_rows: list[dict[str, str]] = []

    for row in rows:
        student_id = (row.get("student_id") or "").strip()
        order_in_seq = (row.get("order_in_seq") or "").strip()
        ep_idx, step = _resolve_ep_step(row, sub_to_ep_step, ep_lookup, data)

        if ep_idx is None or step is None:
            unmatched += 1
            z = np.zeros(Z_DIM, dtype=np.float32)
        else:
            matched += 1
            z = _encode_prefix(model, data, ep_idx, step, device)

        out_row = {"student_id": student_id, "order_in_seq": order_in_seq}
        for i, c in enumerate(z_cols):
            out_row[c] = f"{float(z[i]):.8g}"
        out_rows.append(out_row)

    n = len(rows)
    frac = unmatched / max(n, 1)
    print(f"Encoded {n} rows: matched={matched} unmatched={unmatched} ({frac:.2%})")

    if frac > max_unmatched_frac:
        raise SystemExit(
            f"Unmatched fraction {frac:.2%} exceeds limit {max_unmatched_frac:.2%}. "
            "Re-run 00 with submission_id from rich export."
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {out_csv}")


def main() -> None:
    p = argparse.ArgumentParser(description="Encode VAE latents per interaction row")
    p.add_argument("--interactions", type=Path, default=DEFAULT_INTERACTIONS)
    p.add_argument("--episodes", type=Path, default=DEFAULT_EPISODE_NPZ)
    p.add_argument("--checkpoint", type=Path, default=DEFAULT_VAE_CHECKPOINT)
    p.add_argument("--out", type=Path, default=DEFAULT_Z_LATENT_CSV)
    p.add_argument("--max-unmatched-frac", type=float, default=ENCODE_UNMATCHED_MAX_FRAC)
    args = p.parse_args()
    run(
        args.interactions,
        args.episodes,
        args.checkpoint,
        args.out,
        args.max_unmatched_frac,
    )


if __name__ == "__main__":
    main()
