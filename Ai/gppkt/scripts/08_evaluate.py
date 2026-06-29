from __future__ import annotations

import argparse
import importlib.util
import json
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

from config import (  # noqa: E402
    BATCH,
    DEFAULT_EXERCISE_VECTORS,
    DEFAULT_KC_CHECKPOINT,
    DEFAULT_KC_EMBEDDINGS,
    DEFAULT_METRICS_JSON,
    DEFAULT_SEQUENCES_NPZ,
    SEED,
    TRAIN_FRAC,
)

import torch


def auc_safe(y_true: np.ndarray, y_score: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return float("nan")
    if len(y_true) < 2:
        return float("nan")
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, y_score))


def classification_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    """AUC, accuracy, precision, recall, F1, BCE log loss; NaN where undefined."""
    y_true = np.asarray(y_true, dtype=np.float64)
    y_prob = np.asarray(y_prob, dtype=np.float64)
    n = int(y_true.shape[0])
    out: dict = {
        "n_labels": n,
        "positive_rate": float(y_true.mean()) if n else float("nan"),
        "threshold": threshold,
        "auc": auc_safe(y_true, y_prob),
    }
    if n == 0:
        out.update(
            {
                "accuracy": float("nan"),
                "precision": float("nan"),
                "recall": float("nan"),
                "f1": float("nan"),
                "bce_log_loss": float("nan"),
            }
        )
        return out

    pred = (y_prob >= threshold).astype(np.int64)
    out["accuracy"] = float((pred == y_true.astype(np.int64)).mean())

    try:
        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            log_loss,
            precision_score,
            recall_score,
        )

        out["accuracy"] = float(accuracy_score(y_true, pred))
        out["precision"] = float(precision_score(y_true, pred, zero_division=0))
        out["recall"] = float(recall_score(y_true, pred, zero_division=0))
        out["f1"] = float(f1_score(y_true, pred, zero_division=0))
        out["bce_log_loss"] = float(
            log_loss(y_true, np.clip(y_prob, 1e-6, 1 - 1e-6))
        )
    except ImportError:
        tp = int(((pred == 1) & (y_true == 1)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        fn = int(((pred == 0) & (y_true == 1)).sum())
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        out["precision"] = float(prec)
        out["recall"] = float(rec)
        out["f1"] = float(2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
        out["bce_log_loss"] = float("nan")

    return out


@torch.no_grad()
def collect_split_probs(
    model: torch.nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
    head: str,
) -> tuple[np.ndarray, np.ndarray]:
    ys: list[np.ndarray] = []
    ps: list[np.ndarray] = []
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items()}
        if head == "problem":
            pr, yt = model_mod.collect_preds_labels(model, batch)
        else:
            pr, yt = model_mod.collect_kc_preds_labels(model, batch)
        ys.append(yt.cpu().numpy())
        ps.append(pr.cpu().numpy())
    if not ys:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)
    return np.concatenate(ys), np.concatenate(ps)


def evaluate_checkpoint(
    npz_path: Path,
    exercise_vectors_path: Path,
    kc_embeddings_path: Path,
    checkpoint_path: Path,
    device: torch.device,
    batch_size: int = BATCH,
    seed: int = SEED,
    train_frac: float = TRAIN_FRAC,
    threshold: float = 0.5,
) -> dict:
    E_np = ds_mod.load_exercise_vectors(exercise_vectors_path)
    E = torch.from_numpy(E_np).float().to(device)
    C_np = np.load(kc_embeddings_path)
    C_emb = torch.from_numpy(C_np).float().to(device)

    ck = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = model_mod.GPPKT(E, C_emb).to(device)
    model.load_state_dict(ck["model"])
    model.eval()

    train_loader, val_loader, train_idx, val_idx = ds_mod.get_dataloaders(
        npz_path, batch_size=batch_size, seed=seed, train_frac=train_frac
    )

    data = np.load(npz_path)
    s_count = int(data["seq_lengths"].shape[0])
    t_pad = int(data["problem_idx"].shape[1])
    c_count = int(data["next_kc_mask"].shape[2])

    y_tr_p, p_tr_p = collect_split_probs(model, train_loader, device, "problem")
    y_va_p, p_va_p = collect_split_probs(model, val_loader, device, "problem")
    y_tr_k, p_tr_k = collect_split_probs(model, train_loader, device, "kc")
    y_va_k, p_va_k = collect_split_probs(model, val_loader, device, "kc")

    return {
        "checkpoint": str(checkpoint_path),
        "npz": str(npz_path),
        "exercise_vectors": str(exercise_vectors_path),
        "kc_embeddings": str(kc_embeddings_path),
        "checkpoint_epoch": ck.get("epoch"),
        "checkpoint_val_kc_auc": ck.get("val_kc_auc"),
        "checkpoint_val_problem_auc": ck.get("val_problem_auc"),
        "S": s_count,
        "T": t_pad,
        "K": int(E_np.shape[0]),
        "C": c_count,
        "train_students": int(len(train_idx)),
        "val_students": int(len(val_idx)),
        "problem": {
            "train": classification_metrics(y_tr_p, p_tr_p, threshold=threshold),
            "validation": classification_metrics(y_va_p, p_va_p, threshold=threshold),
        },
        "kc": {
            "train": classification_metrics(y_tr_k, p_tr_k, threshold=threshold),
            "validation": classification_metrics(y_va_k, p_va_k, threshold=threshold),
        },
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluate GPPKT checkpoint (script 08)")
    p.add_argument("--npz", type=Path, default=DEFAULT_SEQUENCES_NPZ)
    p.add_argument("--exercise-vectors", type=Path, default=DEFAULT_EXERCISE_VECTORS)
    p.add_argument("--kc-embeddings", type=Path, default=DEFAULT_KC_EMBEDDINGS)
    p.add_argument("--checkpoint", type=Path, default=DEFAULT_KC_CHECKPOINT)
    p.add_argument("--out", type=Path, default=DEFAULT_METRICS_JSON)
    p.add_argument("--batch", type=int, default=BATCH)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--train-frac", type=float, default=TRAIN_FRAC)
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--device", type=str, default="cpu")
    args = p.parse_args()

    device = torch.device(args.device)
    metrics = evaluate_checkpoint(
        args.npz,
        args.exercise_vectors,
        args.kc_embeddings,
        args.checkpoint,
        device,
        batch_size=args.batch,
        seed=args.seed,
        train_frac=args.train_frac,
        threshold=args.threshold,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    tr_p = metrics["problem"]["train"]
    va_p = metrics["problem"]["validation"]
    tr_k = metrics["kc"]["train"]
    va_k = metrics["kc"]["validation"]
    print(f"Wrote {args.out}")
    print(
        f"problem train  n={tr_p['n_labels']}  auc={tr_p['auc']:.4f}  acc={tr_p['accuracy']:.4f}"
    )
    print(
        f"problem val    n={va_p['n_labels']}  auc={va_p['auc']:.4f}  acc={va_p['accuracy']:.4f}"
    )
    print(
        f"kc      train  n={tr_k['n_labels']}  auc={tr_k['auc']:.4f}  acc={tr_k['accuracy']:.4f}"
    )
    print(
        f"kc      val    n={va_k['n_labels']}  auc={va_k['auc']:.4f}  acc={va_k['accuracy']:.4f}"
    )


if __name__ == "__main__":
    main()
