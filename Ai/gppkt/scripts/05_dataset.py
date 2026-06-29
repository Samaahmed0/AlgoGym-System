from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import (  # noqa: E402
    BATCH,
    DEFAULT_EXERCISE_VECTORS,
    DEFAULT_SEQUENCES_NPZ,
    SEED,
    TRAIN_FRAC,
)

try:
    import torch
    from torch.utils.data import DataLoader, Dataset
except ImportError as e:
    raise ImportError("05_dataset.py requires PyTorch: pip install torch") from e


def load_exercise_vectors(path: Path) -> np.ndarray:
    """[K, d] float array for embedding lookup by problem_idx."""
    return np.load(path)


def train_val_indices(n_students: int, seed: int = SEED, train_frac: float = TRAIN_FRAC) -> tuple[np.ndarray, np.ndarray]:
    """Shuffle student indices; return (train_idx, val_idx) into axis 0 of NPZ arrays."""
    if n_students <= 0:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    rng = np.random.RandomState(seed)
    perm = rng.permutation(n_students)
    n_train = int(train_frac * n_students)
    if n_train == 0 and n_students > 0:
        n_train = 1
    if n_train >= n_students and n_students > 1:
        n_train = n_students - 1
    return perm[:n_train].astype(np.int64), perm[n_train:].astype(np.int64)


class GPPKTDataset(Dataset):
    """One sample = one student’s padded timeline [T]."""

    def __init__(self, npz_path: Path, student_indices: np.ndarray):
        data = np.load(npz_path)
        if "next_kc_mask" not in data or "step_kc_mask" not in data:
            raise ValueError(
                f"{npz_path} missing next_kc_mask/step_kc_mask; rerun 04_build_interaction_vectors.py"
            )
        self._idx = np.asarray(student_indices, dtype=np.int64)
        self.problem_idx = data["problem_idx"]
        self.z_raw = data["z_raw"]
        self.r_t = data["r_t"]
        self.theta_st = data["theta_st"]
        self.y_next = data["y_next"]
        self.next_problem_idx = data["next_problem_idx"]
        self.next_kc_mask = data["next_kc_mask"]
        self.step_kc_mask = data["step_kc_mask"]
        self.seq_lengths = data["seq_lengths"]
        self.loss_mask = data["loss_mask"]

    def __len__(self) -> int:
        return int(self._idx.shape[0])

    def __getitem__(self, i: int) -> dict[str, torch.Tensor]:
        si = int(self._idx[i])
        return {
            "problem_idx": torch.from_numpy(self.problem_idx[si].copy()).long(),
            "z_raw": torch.from_numpy(self.z_raw[si].copy()).float(),
            "r_t": torch.from_numpy(self.r_t[si].copy()).long(),
            "theta_st": torch.from_numpy(self.theta_st[si].copy()).float(),
            "y_next": torch.from_numpy(self.y_next[si].copy()).long(),
            "next_problem_idx": torch.from_numpy(self.next_problem_idx[si].copy()).long(),
            "next_kc_mask": torch.from_numpy(self.next_kc_mask[si].copy()).float(),
            "step_kc_mask": torch.from_numpy(self.step_kc_mask[si].copy()).float(),
            "seq_length": torch.tensor(int(self.seq_lengths[si]), dtype=torch.long),
            "loss_mask": torch.from_numpy(self.loss_mask[si].copy()),
        }


def get_dataloaders(
    npz_path: Path,
    batch_size: int = BATCH,
    seed: int = SEED,
    train_frac: float = TRAIN_FRAC,
    num_workers: int = 0,
    pin_memory: bool = False,
) -> tuple[DataLoader, DataLoader, np.ndarray, np.ndarray]:
    """
    Returns train_loader, val_loader, train_student_indices, val_student_indices.
    """
    data = np.load(npz_path)
    n = int(data["seq_lengths"].shape[0])
    train_idx, val_idx = train_val_indices(n, seed=seed, train_frac=train_frac)

    train_ds = GPPKTDataset(npz_path, train_idx)
    val_ds = GPPKTDataset(npz_path, val_idx)

    gen = torch.Generator()
    gen.manual_seed(seed)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        generator=gen,
        drop_last=False,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=False,
    )
    return train_loader, val_loader, train_idx, val_idx


def main() -> None:
    p = argparse.ArgumentParser(description="Smoke-test GPPKT DataLoaders")
    p.add_argument("--npz", type=Path, default=DEFAULT_SEQUENCES_NPZ)
    p.add_argument("--exercise-vectors", type=Path, default=DEFAULT_EXERCISE_VECTORS)
    p.add_argument("--batch", type=int, default=BATCH)
    args = p.parse_args()

    E = load_exercise_vectors(args.exercise_vectors)
    print(f"exercise_vectors {E.shape}")

    train_loader, val_loader, tr, va = get_dataloaders(args.npz, batch_size=args.batch)
    print(f"students train={len(tr)} val={len(va)}  batches train={len(train_loader)} val={len(val_loader)}")

    batch = next(iter(train_loader))
    print({k: tuple(v.shape) for k, v in batch.items()})


if __name__ == "__main__":
    main()
