from __future__ import annotations

import json
import re
from typing import Iterable


def _dedupe_preserve_order(names: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        s = n.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _normalize_kc_name(name: str) -> str:
    """
    Normalize known KC naming differences to match `Ai/kc_vocab.csv`.
    Keep this intentionally small and explicit to avoid accidental remapping.
    """
    s = name.strip()
    if not s:
        return ""
    # Normalize Unicode dashes to ASCII hyphen to match kc_vocab entries.
    s = s.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    # Fix known casing mismatches coming from problem tags.
    if s == "meet-in-the-middle":
        return "Meet-in-the-middle"
    if s == "schedules":
        return "Schedules"
    return s


def parse_json_array_cell(cell: str | None) -> list[str]:
    """Parse a cell that may be a JSON array of strings, or empty."""
    if cell is None:
        return []
    s = str(cell).strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return [str(x).strip() for x in parsed if str(x).strip()]
    # Fallback: pipe-separated
    return [p.strip() for p in s.split("|") if p.strip()]


def union_tags_concepts_kc_names(tags_cell: str | None, concepts_cell: str | None) -> list[str]:
    """Union of parsed tags and concepts; dedupe; order-preserving (tags first, then concepts)."""
    tags = [_normalize_kc_name(x) for x in parse_json_array_cell(tags_cell)]
    concepts = [_normalize_kc_name(x) for x in parse_json_array_cell(concepts_cell)]
    return _dedupe_preserve_order(list(tags) + list(concepts))


def kc_names_to_semicolon_field(kc_names: list[str]) -> str:
    """Semicolon-separated field for problems_table (no leading/trailing semicolons)."""
    return ";".join(kc_names)


def split_kc_names_field(field: str | None) -> list[str]:
    """Split problems_table kc_names column."""
    if field is None or not str(field).strip():
        return []
    return [p.strip() for p in str(field).split(";") if p.strip()]
