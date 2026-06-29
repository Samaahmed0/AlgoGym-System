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

from config import (  # noqa: E402
    BATCH,
    DEFAULT_EXERCISE_VECTORS,
    DEFAULT_KC_CHECKPOINT,
    VAE_RUN_DIR,
    DEFAULT_KC_EMBEDDINGS,
    DEFAULT_KC_GRAPH,
    DEFAULT_KC_INDEX,
    DEFAULT_SEQUENCES_NPZ,
    EPOCHS,
    GRAPH_LOSS_WEIGHT,
    KC_CURRENT_LOSS_WEIGHT,
    KC_LOSS_WEIGHT,
    LR,
    PROBLEM_LOSS_WEIGHT,
    SEED,
    WEIGHT_DECAY,
)
from kc_embeddings import load_kc_sidecars  # noqa: E402
from kc_graph import load_kc_graph_edges  # noqa: E402

import torch
from torch import optim


def main() -> None:
    p = argparse.ArgumentParser(description="Train GPPKT with KC mastery head")
    p.add_argument("--npz", type=Path, default=DEFAULT_SEQUENCES_NPZ)
    p.add_argument("--exercise-vectors", type=Path, default=DEFAULT_EXERCISE_VECTORS)
    p.add_argument("--kc-embeddings", type=Path, default=DEFAULT_KC_EMBEDDINGS)
    p.add_argument("--checkpoint", type=Path, default=None, help="Default: gppkt_kc_best.pt in --run-dir")
    p.add_argument("--run-dir", type=Path, default=VAE_RUN_DIR, help="Output directory for vae_v1 run")
    p.add_argument("--init-checkpoint", type=Path, default=None, help="Warm-start trunk from existing checkpoint")
    p.add_argument("--epochs", type=int, default=EPOCHS)
    p.add_argument("--batch", type=int, default=BATCH)
    p.add_argument("--lr", type=float, default=LR)
    p.add_argument("--problem-loss-weight", type=float, default=PROBLEM_LOSS_WEIGHT)
    p.add_argument("--kc-loss-weight", type=float, default=KC_LOSS_WEIGHT)
    p.add_argument("--weight-decay", type=float, default=WEIGHT_DECAY)
    p.add_argument("--kc-current-loss-weight", type=float, default=KC_CURRENT_LOSS_WEIGHT)
    p.add_argument("--graph-loss-weight", type=float, default=GRAPH_LOSS_WEIGHT)
    p.add_argument("--kc-graph", type=Path, default=DEFAULT_KC_GRAPH)
    p.add_argument("--kc-index", type=Path, default=DEFAULT_KC_INDEX)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--device", type=str, default="cpu")
    args = p.parse_args()
    if args.checkpoint is None:
        args.checkpoint = args.run_dir / "gppkt_kc_best.pt"

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device(args.device)

    E_np = ds_mod.load_exercise_vectors(args.exercise_vectors)
    E = torch.from_numpy(E_np).float().to(device)
    C_np = np.load(args.kc_embeddings)
    C_emb = torch.from_numpy(C_np).float().to(device)

    train_loader, val_loader, _, _ = ds_mod.get_dataloaders(
        args.npz, batch_size=args.batch, seed=args.seed
    )

    kc_names, _ = load_kc_sidecars(args.kc_index, args.kc_embeddings)
    name_to_idx = {n: i for i, n in enumerate(kc_names)}
    graph_from, graph_to, graph_w = load_kc_graph_edges(args.kc_graph, name_to_idx)
    print(f"KC graph edges for training: {graph_from.numel()}")

    model = model_mod.GPPKT(E, C_emb).to(device)

    if args.init_checkpoint is not None and args.init_checkpoint.exists():
        ck = torch.load(args.init_checkpoint, map_location=device, weights_only=False)
        missing, unexpected = model.load_state_dict(ck["model"], strict=False)
        print(f"Warm-start from {args.init_checkpoint}  missing={len(missing)}  unexpected={len(unexpected)}")

    opt = optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        roc_auc_score = None  # type: ignore

    def auc_safe(y_true: np.ndarray, y_score: np.ndarray) -> float:
        if roc_auc_score is None or len(y_true) < 2:
            return float("nan")
        u = np.unique(y_true)
        if len(u) < 2:
            return float("nan")
        return float(roc_auc_score(y_true, y_score))

    best_kc_auc_next = -1.0
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        tr_loss = 0.0
        n_batches = 0
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            opt.zero_grad()
            out = model(batch)
            loss_p = model_mod.bce_loss_next_step(out["problem_logits"], batch)
            loss_k_next = model_mod.bce_loss_kc(out["kc_logits"], batch)
            loss_k_cur = model_mod.bce_loss_kc_current(out["kc_logits"], batch)
            mastery = model_mod.mastery_from_kc_logits(out["kc_logits"], batch)
            loss_graph = model_mod.graph_prerequisite_loss(
                mastery, graph_from, graph_to, graph_w
            )
            loss_k = loss_k_next + args.kc_current_loss_weight * loss_k_cur
            loss = (
                args.problem_loss_weight * loss_p
                + args.kc_loss_weight * loss_k
                + args.graph_loss_weight * loss_graph
            )
            loss.backward()
            opt.step()
            tr_loss += float(loss.item())
            n_batches += 1
        tr_loss /= max(n_batches, 1)

        model.eval()
        val_problem_auc = float("nan")
        val_kc_auc_next = float("nan")
        val_kc_auc_current = float("nan")
        if len(val_loader) > 0:
            ys_p: list[np.ndarray] = []
            ps_p: list[np.ndarray] = []
            ys_k_next: list[np.ndarray] = []
            ps_k_next: list[np.ndarray] = []
            ys_k_cur: list[np.ndarray] = []
            ps_k_cur: list[np.ndarray] = []
            with torch.no_grad():
                for batch in val_loader:
                    batch = {k: v.to(device) for k, v in batch.items()}
                    pr, yt = model_mod.collect_preds_labels(model, batch)
                    kr, yk = model_mod.collect_kc_preds_labels(model, batch)
                    kcr, ykc = model_mod.collect_kc_current_preds_labels(model, batch)
                    ys_p.append(yt.cpu().numpy())
                    ps_p.append(pr.cpu().numpy())
                    ys_k_next.append(yk.cpu().numpy())
                    ps_k_next.append(kr.cpu().numpy())
                    ys_k_cur.append(ykc.cpu().numpy())
                    ps_k_cur.append(kcr.cpu().numpy())
            if ys_p:
                val_problem_auc = auc_safe(np.concatenate(ys_p), np.concatenate(ps_p))
            if ys_k_next:
                val_kc_auc_next = auc_safe(np.concatenate(ys_k_next), np.concatenate(ps_k_next))
            if ys_k_cur:
                val_kc_auc_current = auc_safe(np.concatenate(ys_k_cur), np.concatenate(ps_k_cur))

        if not np.isnan(val_kc_auc_next) and val_kc_auc_next > best_kc_auc_next:
            best_kc_auc_next = val_kc_auc_next
            torch.save(
                {
                    "model": model.state_dict(),
                    "epoch": epoch,
                    "val_kc_auc": val_kc_auc_next,
                    "val_kc_auc_next": val_kc_auc_next,
                    "val_kc_auc_current": val_kc_auc_current,
                    "val_problem_auc": val_problem_auc,
                },
                args.checkpoint,
            )

        if len(val_loader) == 0:
            torch.save(
                {
                    "model": model.state_dict(),
                    "epoch": epoch,
                    "val_kc_auc": None,
                    "val_problem_auc": None,
                },
                args.checkpoint,
            )

        msg = f"epoch {epoch}/{args.epochs}  train_loss={tr_loss:.4f}"
        if not np.isnan(val_problem_auc):
            msg += f"  val_problem_auc={val_problem_auc:.4f}"
        else:
            msg += "  val_problem_auc=n/a"
        if not np.isnan(val_kc_auc_next):
            msg += f"  val_kc_auc_next={val_kc_auc_next:.4f}"
        else:
            msg += "  val_kc_auc_next=n/a"
        if not np.isnan(val_kc_auc_current):
            msg += f"  val_kc_auc_current={val_kc_auc_current:.4f}"
        else:
            msg += "  val_kc_auc_current=n/a"
        print(msg)

    print(
        f"Done. best_val_kc_auc_next={best_kc_auc_next if best_kc_auc_next >= 0 else 'n/a'}  "
        f"checkpoint={args.checkpoint}"
    )


if __name__ == "__main__":
    main()
