from __future__ import annotations

import argparse
import importlib.util
import random
import sys
from pathlib import Path

import numpy as np

_SCRIPTS = Path(__file__).resolve().parent
_GPPKT = _SCRIPTS.parent
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


ds_mod = _load_script("gppkt_dataset", _SCRIPTS / "05_dataset.py")
model_mod = _load_script("gppkt_model", _SCRIPTS / "06_model.py")

from config import BATCH, DEFAULT_EXERCISE_VECTORS, DEFAULT_SEQUENCES_NPZ, SEED  # noqa: E402

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

DKT_HIDDEN = 128
DKT_LR = 0.001
DKT_EPOCHS = 30


def dkt_one_hot(problem_idx: torch.Tensor, r_t: torch.Tensor, k: int) -> torch.Tensor:
    """[B, T, 2K] one-hot: correct -> problem_idx, wrong -> problem_idx + K."""
    pi = problem_idx.clamp(min=0, max=k - 1)
    idx = pi + (1 - r_t.long()) * k
    return F.one_hot(idx, num_classes=2 * k).float()


class DKT(nn.Module):
    def __init__(self, k: int, hidden_dim: int = DKT_HIDDEN) -> None:
        super().__init__()
        self.k = k
        self.lstm = nn.LSTM(2 * k, hidden_dim, batch_first=True, num_layers=1)
        self.out = nn.Linear(hidden_dim, k)

    def forward(self, batch: dict[str, torch.Tensor]) -> torch.Tensor:
        x = dkt_one_hot(batch["problem_idx"], batch["r_t"], self.k)
        lengths = batch["seq_length"].detach().cpu()
        packed = pack_padded_sequence(x, lengths, batch_first=True, enforce_sorted=False)
        packed_out, _ = self.lstm(packed)
        h, _ = pad_packed_sequence(packed_out, batch_first=True, total_length=x.shape[1])
        return self.out(h)


@torch.no_grad()
def collect_problem_preds(
    model: DKT, batch: dict[str, torch.Tensor]
) -> tuple[torch.Tensor, torch.Tensor]:
    logits = model(batch)
    next_pi = batch["next_problem_idx"]
    y_next = batch["y_next"].float()
    mask = batch["loss_mask"]
    idx = next_pi.clamp(min=0).unsqueeze(-1)
    sel = logits.gather(2, idx).squeeze(-1)
    probs = torch.sigmoid(sel)
    m = mask.reshape(-1)
    return probs.reshape(-1)[m], y_next.reshape(-1)[m]


def auc_safe(y_true: np.ndarray, y_score: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return float("nan")
    if len(y_true) < 2 or len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, y_score))


def acc_at_threshold(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> float:
    if len(y_true) == 0:
        return float("nan")
    pred = (y_prob >= threshold).astype(np.int64)
    return float((pred == y_true.astype(np.int64)).mean())


def main() -> None:
    p = argparse.ArgumentParser(description="Train baseline DKT on gppkt_sequences.npz")
    p.add_argument("--npz", type=Path, default=DEFAULT_SEQUENCES_NPZ)
    p.add_argument("--exercise-vectors", type=Path, default=DEFAULT_EXERCISE_VECTORS)
    p.add_argument("--batch", type=int, default=BATCH)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--device", type=str, default="cpu")
    args = p.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device(args.device)
    k = int(ds_mod.load_exercise_vectors(args.exercise_vectors).shape[0])

    train_loader, val_loader, _, _ = ds_mod.get_dataloaders(
        args.npz, batch_size=args.batch, seed=args.seed
    )

    model = DKT(k).to(device)
    opt = optim.Adam(model.parameters(), lr=DKT_LR)

    for epoch in range(1, DKT_EPOCHS + 1):
        model.train()
        tr_loss = 0.0
        n_batches = 0
        for batch in train_loader:
            batch = {key: val.to(device) for key, val in batch.items()}
            opt.zero_grad()
            logits = model(batch)
            loss = model_mod.bce_loss_next_step(logits, batch)
            loss.backward()
            opt.step()
            tr_loss += float(loss.item())
            n_batches += 1
        tr_loss /= max(n_batches, 1)
        print(f"epoch {epoch}/{DKT_EPOCHS}  train_loss={tr_loss:.4f}")

    model.eval()
    ys: list[np.ndarray] = []
    ps: list[np.ndarray] = []
    with torch.no_grad():
        for batch in val_loader:
            batch = {key: val.to(device) for key, val in batch.items()}
            prob, y = collect_problem_preds(model, batch)
            ys.append(y.cpu().numpy())
            ps.append(prob.cpu().numpy())

    if ys:
        y_all = np.concatenate(ys)
        p_all = np.concatenate(ps)
        val_auc = auc_safe(y_all, p_all)
        val_acc = acc_at_threshold(y_all, p_all)
    else:
        val_auc = float("nan")
        val_acc = float("nan")

    print(f"DKT val_problem_auc: {val_auc:.4f}")
    print(f"DKT val_problem_acc: {val_acc:.4f}")


if __name__ == "__main__":
    main()
