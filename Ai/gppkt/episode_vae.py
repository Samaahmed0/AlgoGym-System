from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from config import MAX_EP_LEN, VAE_HIDDEN, Z_DIM
from episode_features import CONT_FEAT_NAMES, R_AC_WA_MISSING

N_CONT = len(CONT_FEAT_NAMES)


class EpisodeVAE(nn.Module):
    def __init__(
        self,
        n_verdicts: int,
        z_dim: int = Z_DIM,
        hidden_dim: int = VAE_HIDDEN,
        verdict_embed_dim: int = 16,
        max_ep_len: int = MAX_EP_LEN,
    ) -> None:
        super().__init__()
        self.n_verdicts = n_verdicts
        self.z_dim = z_dim
        self.hidden_dim = hidden_dim
        self.max_ep_len = max_ep_len
        self.verdict_embed = nn.Embedding(n_verdicts, verdict_embed_dim)
        self.input_dim = verdict_embed_dim + N_CONT

        self.encoder = nn.LSTM(
            self.input_dim,
            hidden_dim,
            batch_first=True,
            bidirectional=True,
            num_layers=1,
        )
        self.fc_mu = nn.Linear(hidden_dim * 2, z_dim)
        self.fc_logvar = nn.Linear(hidden_dim * 2, z_dim)

        self.dec_init = nn.Linear(z_dim, hidden_dim)
        self.decoder = nn.LSTM(self.input_dim, hidden_dim, batch_first=True, num_layers=1)
        self.dec_verdict = nn.Linear(hidden_dim, n_verdicts)
        self.dec_cont = nn.Linear(hidden_dim, N_CONT)

    def _pack_inputs(
        self,
        verdict_id: torch.Tensor,
        cont: torch.Tensor,
        lengths: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """verdict_id [B,T], cont [B,T,N_CONT] -> packed input, cpu lengths."""
        emb = self.verdict_embed(verdict_id.clamp(min=0))
        x = torch.cat([emb, cont], dim=-1)
        lens = lengths.detach().cpu().clamp(min=1)
        packed = pack_padded_sequence(x, lens, batch_first=True, enforce_sorted=False)
        return packed, lens

    def encode(
        self,
        verdict_id: torch.Tensor,
        cont: torch.Tensor,
        lengths: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        packed, _ = self._pack_inputs(verdict_id, cont, lengths)
        _, (h_n, _) = self.encoder(packed)
        h_fwd = h_n[-2]
        h_bwd = h_n[-1]
        h = torch.cat([h_fwd, h_bwd], dim=-1)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        if self.training:
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std
        return mu

    def decode_teacher(
        self,
        z: torch.Tensor,
        verdict_id: torch.Tensor,
        cont: torch.Tensor,
        lengths: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        emb = self.verdict_embed(verdict_id.clamp(min=0))
        x = torch.cat([emb, cont], dim=-1)
        h0 = self.dec_init(z).unsqueeze(0)
        c0 = torch.zeros_like(h0)
        packed = pack_padded_sequence(x, lengths.detach().cpu().clamp(min=1), batch_first=True, enforce_sorted=False)
        dec_out, _ = self.decoder(packed, (h0, c0))
        dec_pad, _ = pad_packed_sequence(dec_out, batch_first=True, total_length=x.shape[1])
        logits_v = self.dec_verdict(dec_pad)
        cont_hat = self.dec_cont(dec_pad)
        return logits_v, cont_hat

    def forward(
        self,
        verdict_id: torch.Tensor,
        cont: torch.Tensor,
        lengths: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        mu, logvar = self.encode(verdict_id, cont, lengths)
        z = self.reparameterize(mu, logvar)
        logits_v, cont_hat = self.decode_teacher(z, verdict_id, cont, lengths)
        return {
            "mu": mu,
            "logvar": logvar,
            "z": z,
            "verdict_logits": logits_v,
            "cont_hat": cont_hat,
        }


def cont_from_batch(
    attempt_index_norm: torch.Tensor,
    improved: torch.Tensor,
    dt_log_hours: torch.Tensor,
    r_ac_wa: torch.Tensor,
) -> torch.Tensor:
    """Stack continuous features [B, T, N_CONT]. Map missing r_ac_wa to 0.5 for encoding."""
    r = r_ac_wa.clone()
    r[r < 0] = 0.5
    return torch.stack([attempt_index_norm, improved, dt_log_hours, r], dim=-1)


def vae_loss(
    out: dict[str, torch.Tensor],
    verdict_id: torch.Tensor,
    cont: torch.Tensor,
    r_ac_wa: torch.Tensor,
    lengths: torch.Tensor,
    beta: float,
) -> tuple[torch.Tensor, dict[str, float]]:
    B, T, _ = cont.shape
    device = cont.device
    t_idx = torch.arange(T, device=device).view(1, T)
    mask = (t_idx < lengths.view(B, 1)).float()

    logits = out["verdict_logits"]
    ce = F.cross_entropy(
        logits.reshape(-1, logits.shape[-1]),
        verdict_id.reshape(-1),
        reduction="none",
    ).view(B, T)
    loss_v = (ce * mask).sum() / mask.sum().clamp(min=1.0)

    mse = F.mse_loss(out["cont_hat"], cont, reduction="none").mean(dim=-1)
    loss_c = (mse * mask).sum() / mask.sum().clamp(min=1.0)

    # Extra BCE on AC/WA channel where r_ac_wa is 0 or 1
    r_mask = (r_ac_wa >= 0).float() * mask
    r_tgt = r_ac_wa.clamp(0, 1)
    r_pred = out["cont_hat"][..., 3]
    loss_r = (F.mse_loss(r_pred, r_tgt, reduction="none") * r_mask).sum() / r_mask.sum().clamp(min=1.0)

    kl = -0.5 * torch.sum(1 + out["logvar"] - out["mu"].pow(2) - out["logvar"].exp(), dim=1)
    loss_kl = kl.mean()

    total = loss_v + loss_c + 0.1 * loss_r + beta * loss_kl
    stats = {
        "loss": float(total.detach()),
        "loss_verdict": float(loss_v.detach()),
        "loss_cont": float(loss_c.detach()),
        "loss_r": float(loss_r.detach()),
        "loss_kl": float(loss_kl.detach()),
    }
    return total, stats


def load_episode_batch(
    data: dict[str, Any],
    indices: list[int],
    device: torch.device,
) -> dict[str, torch.Tensor]:
    """Collate episodes by index list into padded tensors."""
    max_len = 1
    lengths_list: list[int] = []
    for ei in indices:
        start = int(data["ep_offsets"][ei])
        end = int(data["ep_offsets"][ei + 1])
        lengths_list.append(end - start)
        max_len = max(max_len, end - start)
    max_len = min(max_len, int(data.get("max_ep_len", MAX_EP_LEN)))
    B = len(indices)

    def sl(name: str, dtype=torch.long):
        arr = data[name]
        out = torch.zeros(B, max_len, dtype=dtype)
        for bi, ei in enumerate(indices):
            start = int(data["ep_offsets"][ei])
            end = int(data["ep_offsets"][ei + 1])
            seg = torch.as_tensor(arr[start:end], dtype=dtype)
            if seg.numel() > max_len:
                seg = seg[-max_len:]
            out[bi, : seg.numel()] = seg
        return out

    verdict_id = sl("verdict_id")
    r_ac_wa = sl("r_ac_wa", dtype=torch.float32).float()
    attempt_index_norm = sl("attempt_index_norm", dtype=torch.float32).float()
    improved = sl("improved", dtype=torch.float32).float()
    dt_log_hours = sl("dt_log_hours", dtype=torch.float32).float()
    lengths = torch.tensor(lengths_list, dtype=torch.long)
    lengths = lengths.clamp(max=max_len)

    cont = cont_from_batch(attempt_index_norm, improved, dt_log_hours, r_ac_wa)
    return {
        "verdict_id": verdict_id.to(device),
        "cont": cont.to(device),
        "r_ac_wa": r_ac_wa.to(device),
        "lengths": lengths.to(device),
    }
