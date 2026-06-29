from __future__ import annotations

import sys
from pathlib import Path

_GPPKT = Path(__file__).resolve().parents[1]
if str(_GPPKT) not in sys.path:
    sys.path.insert(0, str(_GPPKT))

from config import DROPOUT, GRAPH_PREREQ_MARGIN, HIDDEN_DIM, Z_DIM  # noqa: E402

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


class GPPKT(nn.Module):
    """
    exercise_embeddings: [K, d] buffer (sum of KC vectors per problem).
    kc_embeddings: [C, d] buffer (one TransE vector per KC).
    input_dim = d + Z + K + 1 (Eq. 10).
    """

    def __init__(
        self,
        exercise_embeddings: torch.Tensor,
        kc_embeddings: torch.Tensor,
        z_dim: int = Z_DIM,
        hidden_dim: int = HIDDEN_DIM,
        dropout: float = DROPOUT,
    ) -> None:
        super().__init__()
        self.register_buffer("E", exercise_embeddings)
        self.register_buffer("C_emb", kc_embeddings)
        self.K = int(exercise_embeddings.shape[0])
        self.C = int(kc_embeddings.shape[0])
        self.d = int(exercise_embeddings.shape[1])
        self.z_dim = z_dim
        self.hidden_dim = hidden_dim
        self.input_dim = self.d + z_dim + self.K + 1

        self.z_norm = nn.LayerNorm(z_dim)
        self.z_proj = nn.Linear(4, z_dim)  # legacy z_feat_0..3 only
        self.lstm = nn.LSTM(self.input_dim, hidden_dim, batch_first=True, num_layers=1)
        self.attn_u = nn.Linear(hidden_dim, hidden_dim, bias=True)
        self.u_w = nn.Parameter(torch.zeros(hidden_dim))
        self.W_t = nn.Linear(hidden_dim, hidden_dim)
        self.W_his = nn.Linear(hidden_dim, hidden_dim)
        self.b_g = nn.Parameter(torch.zeros(hidden_dim))
        self.out_proj = nn.Linear(hidden_dim, self.K)
        self.kc_proj = nn.Linear(hidden_dim, self.d)
        self.dropout = nn.Dropout(dropout)

    def build_x_t(
        self,
        problem_idx: torch.Tensor,
        z_raw: torch.Tensor,
        r_t: torch.Tensor,
        theta_st: torch.Tensor,
    ) -> torch.Tensor:
        """[B, T, input_dim]."""
        B, T, _ = z_raw.shape
        pi = problem_idx.clamp(min=0)
        e = self.E[pi]
        if z_raw.shape[-1] == self.z_dim:
            z = self.z_norm(z_raw)
        else:
            z = self.z_proj(z_raw)
        rf = r_t.float().unsqueeze(-1).expand(B, T, self.K)
        th = theta_st.unsqueeze(-1)
        # Option B: fixed order [e, z, rf, theta]; rf encodes AC (all-1) vs WA (all-0).
        return torch.cat([e, z, rf, th], dim=-1)

    def forward_trunk(self, batch: dict[str, torch.Tensor]) -> torch.Tensor:
        """Returns ks_out [B, T, H]."""
        problem_idx = batch["problem_idx"]
        z_raw = batch["z_raw"]
        r_t = batch["r_t"]
        theta_st = batch["theta_st"]
        seq_length = batch["seq_length"]

        x = self.build_x_t(problem_idx, z_raw, r_t, theta_st)
        B, T, _ = x.shape
        lengths = seq_length.detach().cpu()

        packed = pack_padded_sequence(x, lengths, batch_first=True, enforce_sorted=False)
        packed_out, _ = self.lstm(packed)
        ks, _ = pad_packed_sequence(packed_out, batch_first=True, total_length=T)
        ks = self.dropout(ks)

        H = self.hidden_dim
        ks_out = torch.zeros(B, T, H, device=ks.device, dtype=ks.dtype)
        for t in range(T):
            ks_t = ks[:, t, :]
            if t == 0:
                ks_his = torch.zeros(B, H, device=ks.device, dtype=ks.dtype)
            else:
                past = ks[:, :t, :]
                u = torch.tanh(self.attn_u(past))
                scores = (u * self.u_w).sum(dim=-1)
                attn = torch.softmax(scores, dim=-1)
                ks_his = (attn.unsqueeze(-1) * past).sum(dim=1)
            g = torch.sigmoid(self.W_t(ks_t) + self.W_his(ks_his) + self.b_g)
            ks_out[:, t, :] = g * ks_t + (1.0 - g) * ks_his
        return ks_out

    def forward(self, batch: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        ks_out = self.forward_trunk(batch)
        problem_logits = self.out_proj(ks_out)
        h = self.kc_proj(ks_out)
        kc_logits = torch.einsum("btd,cd->btc", h, self.C_emb)
        return {
            "problem_logits": problem_logits,
            "kc_logits": kc_logits,
            "ks_out": ks_out,
        }


def bce_loss_next_step(problem_logits: torch.Tensor, batch: dict[str, torch.Tensor]) -> torch.Tensor:
    """Eq. 15: select logit at next_problem_idx; BCE with y_next; mask by loss_mask."""
    next_pi = batch["next_problem_idx"]
    y_next = batch["y_next"].float()
    mask = batch["loss_mask"].float()

    idx = next_pi.clamp(min=0).unsqueeze(-1)
    sel = problem_logits.gather(2, idx).squeeze(-1)
    loss_unreduced = F.binary_cross_entropy_with_logits(sel, y_next, reduction="none")
    denom = mask.sum().clamp(min=1.0)
    return (loss_unreduced * mask).sum() / denom


def bce_loss_kc(kc_logits: torch.Tensor, batch: dict[str, torch.Tensor]) -> torch.Tensor:
    """BCE on KC tags of the next problem; mask by next_kc_mask and loss_mask."""
    y_next = batch["y_next"].float()
    step_mask = batch["loss_mask"].float()
    kc_mask = batch["next_kc_mask"].float()

    targets = y_next.unsqueeze(-1).expand_as(kc_logits)
    mask = step_mask.unsqueeze(-1) * kc_mask
    loss_unreduced = F.binary_cross_entropy_with_logits(kc_logits, targets, reduction="none")
    denom = mask.sum().clamp(min=1.0)
    return (loss_unreduced * mask).sum() / denom


def _time_valid_mask(batch: dict[str, torch.Tensor], kc_logits: torch.Tensor) -> torch.Tensor:
    """[B, T, 1] float mask: timestep t is within seq_length."""
    B, T, _ = kc_logits.shape
    seq_length = batch["seq_length"]
    t_idx = torch.arange(T, device=kc_logits.device).view(1, T)
    return (t_idx < seq_length.view(B, 1)).float().unsqueeze(-1)


def bce_loss_kc_current(kc_logits: torch.Tensor, batch: dict[str, torch.Tensor]) -> torch.Tensor:
    """BCE on KCs of the current problem; target = r_t (this step's outcome)."""
    r_t = batch["r_t"].float()
    kc_mask = batch["step_kc_mask"].float()
    time_mask = _time_valid_mask(batch, kc_logits)

    targets = r_t.unsqueeze(-1).expand_as(kc_logits)
    mask = time_mask * kc_mask
    loss_unreduced = F.binary_cross_entropy_with_logits(kc_logits, targets, reduction="none")
    denom = mask.sum().clamp(min=1.0)
    return (loss_unreduced * mask).sum() / denom


def mastery_from_kc_logits(
    kc_logits: torch.Tensor, batch: dict[str, torch.Tensor]
) -> torch.Tensor:
    """
    Per-student mastery [B, C]: recency-weighted mean sigmoid(kc_logits) at timesteps
    where KC is on the current problem (weight exp(0.1 * (t - T)) with T last valid step).
    Falls back to last-step mastery for KCs never active in the sequence.
    """
    decay = 0.1
    probs = torch.sigmoid(kc_logits)
    step_mask = batch["step_kc_mask"].float()
    time_mask = _time_valid_mask(batch, kc_logits)
    mask = step_mask * time_mask

    B, T, C = probs.shape
    seq_length = batch["seq_length"]
    last_t = (seq_length - 1).clamp(min=0)
    t_idx = torch.arange(T, device=kc_logits.device).view(1, T)
    recency = torch.exp(decay * (t_idx - last_t.view(B, 1))).unsqueeze(-1)

    weighted_mask = mask * recency
    summed = (probs * weighted_mask).sum(dim=1)
    denom = weighted_mask.sum(dim=1).clamp(min=1.0)
    avg = summed / denom

    idx = last_t.view(B, 1, 1).expand(B, 1, C)
    last_probs = probs.gather(1, idx).squeeze(1)
    has_active = (mask.sum(dim=1) > 0).float()
    return has_active * avg + (1.0 - has_active) * last_probs


def mastery_at_active_steps(model: GPPKT, batch: dict[str, torch.Tensor]) -> torch.Tensor:
    out = model(batch)
    return mastery_from_kc_logits(out["kc_logits"], batch)


def graph_prerequisite_loss(
    mastery: torch.Tensor,
    from_idx: torch.Tensor,
    to_idx: torch.Tensor,
    weights: torch.Tensor,
    margin: float = GRAPH_PREREQ_MARGIN,
) -> torch.Tensor:
    """
    Soft prerequisite constraint: dependent KC should not exceed prereq mastery by much.
    mastery: [B, C] in (0, 1).
    """
    if from_idx.numel() == 0:
        return mastery.new_zeros(())
    device = mastery.device
    fi = from_idx.to(device)
    ti = to_idx.to(device)
    w = weights.to(device).view(1, -1)
    m_from = mastery[:, fi]
    m_to = mastery[:, ti]
    viol = F.relu(m_to - m_from - margin)
    return (w * viol * viol).mean()


def apply_graph_blend(mastery: torch.Tensor, blend: torch.Tensor) -> torch.Tensor:
    """blend [C, C] row-stochastic; returns [B, C]."""
    return torch.matmul(mastery, blend.to(mastery.device).T)


@torch.no_grad()
def collect_preds_labels(
    model: GPPKT,
    batch: dict[str, torch.Tensor],
) -> tuple[torch.Tensor, torch.Tensor]:
    """Flattened (prob, y) for valid loss_mask positions (problem head)."""
    out = model(batch)
    problem_logits = out["problem_logits"]
    next_pi = batch["next_problem_idx"]
    y_next = batch["y_next"].float()
    mask = batch["loss_mask"]

    idx = next_pi.clamp(min=0).unsqueeze(-1)
    sel = problem_logits.gather(2, idx).squeeze(-1)
    probs = torch.sigmoid(sel)

    m = mask.reshape(-1)
    return probs.reshape(-1)[m], y_next.reshape(-1)[m]


@torch.no_grad()
def collect_kc_preds_labels(
    model: GPPKT,
    batch: dict[str, torch.Tensor],
) -> tuple[torch.Tensor, torch.Tensor]:
    """Flattened (prob, y) for masked KC tag positions."""
    out = model(batch)
    kc_logits = out["kc_logits"]
    y_next = batch["y_next"].float()
    step_mask = batch["loss_mask"]
    kc_mask = batch["next_kc_mask"]

    targets = y_next.unsqueeze(-1).expand_as(kc_logits)
    probs = torch.sigmoid(kc_logits)
    active = (step_mask.unsqueeze(-1) & kc_mask.bool()).reshape(-1)
    return probs.reshape(-1)[active], targets.reshape(-1)[active]


@torch.no_grad()
def mastery_at_last_step(model: GPPKT, batch: dict[str, torch.Tensor]) -> torch.Tensor:
    """Per-student mastery [B, C] at last valid timestep (legacy)."""
    out = model(batch)
    kc_logits = out["kc_logits"]
    seq_length = batch["seq_length"]
    B = kc_logits.shape[0]
    last_t = (seq_length - 1).clamp(min=0)
    idx = last_t.view(B, 1, 1).expand(B, 1, kc_logits.shape[-1])
    last_logits = kc_logits.gather(1, idx).squeeze(1)
    return torch.sigmoid(last_logits)


@torch.no_grad()
def collect_kc_current_preds_labels(
    model: GPPKT,
    batch: dict[str, torch.Tensor],
) -> tuple[torch.Tensor, torch.Tensor]:
    """Flattened (prob, y) for current-step KC tag positions (Option C)."""
    out = model(batch)
    kc_logits = out["kc_logits"]
    r_t = batch["r_t"].float()
    kc_mask = batch["step_kc_mask"]
    time_mask = _time_valid_mask(batch, kc_logits).bool()

    targets = r_t.unsqueeze(-1).expand_as(kc_logits)
    probs = torch.sigmoid(kc_logits)
    active = (time_mask & kc_mask.bool()).reshape(-1)
    return probs.reshape(-1)[active], targets.reshape(-1)[active]
