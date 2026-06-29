
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.optim as optim

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import (  # noqa: E402
    DEFAULT_EPISODE_NPZ,
    DEFAULT_VAE_CHECKPOINT,
    DEFAULT_VAE_METRICS,
    SEED,
    TRAIN_FRAC,
    VAE_BATCH,
    VAE_BETA_MAX,
    VAE_EPOCHS,
    VAE_LR,
    Z_DIM,
)
from episode_vae import EpisodeVAE, load_episode_batch, vae_loss  # noqa: E402


def _user_split(data: dict, train_frac: float, seed: int) -> tuple[list[int], list[int]]:
    users = list({str(u) for u in data["ep_user_id"]})
    rng = random.Random(seed)
    rng.shuffle(users)
    n_train = max(1, int(len(users) * train_frac))
    train_users = set(users[:n_train])
    train_idx: list[int] = []
    val_idx: list[int] = []
    for ei in range(int(data["n_episodes"])):
        u = str(data["ep_user_id"][ei])
        if u in train_users:
            train_idx.append(ei)
        else:
            val_idx.append(ei)
    return train_idx, val_idx


def _maybe_subsample(indices: list[int], max_n: int | None, seed: int) -> list[int]:
    if max_n is None or len(indices) <= max_n:
        return indices
    rng = random.Random(seed)
    return rng.sample(indices, max_n)


def run(
    episode_npz: Path,
    ckpt_path: Path,
    metrics_path: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    beta_max: float,
    seed: int,
    max_train_episodes: int | None,
    max_val_episodes: int | None,
) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    raw = np.load(episode_npz, allow_pickle=True)
    data = {k: raw[k] for k in raw.files}
    n_verdicts = int(data["n_verdicts"])
    train_idx, val_idx = _user_split(data, TRAIN_FRAC, seed)
    train_idx = _maybe_subsample(train_idx, max_train_episodes, seed)
    val_idx = _maybe_subsample(val_idx, max_val_episodes, seed + 1)
    print(f"Episodes train={len(train_idx)} val={len(val_idx)}  verdict_types={n_verdicts}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = EpisodeVAE(n_verdicts=n_verdicts, z_dim=Z_DIM).to(device)
    opt = optim.Adam(model.parameters(), lr=lr)

    best_val = float("inf")
    history: list[dict] = []

    for epoch in range(1, epochs + 1):
        beta = beta_max * min(1.0, epoch / max(1, epochs // 4))
        model.train()
        rng = random.Random(seed + epoch)
        order = train_idx.copy()
        rng.shuffle(order)
        train_losses: list[float] = []

        for start in range(0, len(order), batch_size):
            batch_idx = order[start : start + batch_size]
            batch = load_episode_batch(data, batch_idx, device)
            out = model(batch["verdict_id"], batch["cont"], batch["lengths"])
            loss, _ = vae_loss(
                out,
                batch["verdict_id"],
                batch["cont"],
                batch["r_ac_wa"],
                batch["lengths"],
                beta,
            )
            opt.zero_grad()
            loss.backward()
            opt.step()
            train_losses.append(float(loss.detach()))

        model.eval()
        val_losses: list[float] = []
        with torch.no_grad():
            for start in range(0, len(val_idx), batch_size):
                batch_idx = val_idx[start : start + batch_size]
                if not batch_idx:
                    continue
                batch = load_episode_batch(data, batch_idx, device)
                out = model(batch["verdict_id"], batch["cont"], batch["lengths"])
                loss, st = vae_loss(
                    out,
                    batch["verdict_id"],
                    batch["cont"],
                    batch["r_ac_wa"],
                    batch["lengths"],
                    beta,
                )
                val_losses.append(st["loss"])

        tr = float(np.mean(train_losses)) if train_losses else float("nan")
        va = float(np.mean(val_losses)) if val_losses else float("nan")
        row = {"epoch": epoch, "train_loss": tr, "val_loss": va, "beta": beta}
        history.append(row)
        print(f"epoch {epoch:3d}  train={tr:.4f}  val={va:.4f}  beta={beta:.4f}")

        if va < best_val:
            best_val = va
            ckpt_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "model": model.state_dict(),
                    "n_verdicts": n_verdicts,
                    "z_dim": Z_DIM,
                    "epoch": epoch,
                    "val_loss": va,
                },
                ckpt_path,
            )

    metrics = {
        "best_val_loss": best_val,
        "epochs": epochs,
        "n_train_episodes": len(train_idx),
        "n_val_episodes": len(val_idx),
        "history": history,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Best val_loss={best_val:.4f}  saved {ckpt_path}")
    print(f"Wrote {metrics_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Pretrain Episode VAE")
    p.add_argument("--episodes", type=Path, default=DEFAULT_EPISODE_NPZ)
    p.add_argument("--out", type=Path, default=DEFAULT_VAE_CHECKPOINT)
    p.add_argument("--metrics", type=Path, default=DEFAULT_VAE_METRICS)
    p.add_argument("--epochs", type=int, default=VAE_EPOCHS)
    p.add_argument("--batch", type=int, default=VAE_BATCH)
    p.add_argument("--lr", type=float, default=VAE_LR)
    p.add_argument("--beta-max", type=float, default=VAE_BETA_MAX)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument(
        "--max-train-episodes",
        type=int,
        default=None,
        help="Subsample train episodes (faster dev runs; omit for full data)",
    )
    p.add_argument("--max-val-episodes", type=int, default=None)
    args = p.parse_args()
    run(
        args.episodes,
        args.out,
        args.metrics,
        args.epochs,
        args.batch,
        args.lr,
        args.beta_max,
        args.seed,
        args.max_train_episodes,
        args.max_val_episodes,
    )


if __name__ == "__main__":
    main()
