from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

_AI_ROOT = Path(__file__).resolve().parents[2]
if str(_AI_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ROOT))

from gppkt.kc_strings import (  # noqa: E402
    _normalize_kc_name,
    split_kc_names_field,
    union_tags_concepts_kc_names,
)


def normalize_kc(name: str) -> str:
    return _normalize_kc_name(name)


def normalize_kc_list(names: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        s = normalize_kc(n)
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def parse_semicolon_kcs(field: str | None) -> list[str]:
    return normalize_kc_list(split_kc_names_field(field))


def problem_kc_names(tags_cell: str | None, concepts_cell: str | None) -> list[str]:
    return union_tags_concepts_kc_names(tags_cell, concepts_cell)


__all__ = [
    "normalize_kc",
    "normalize_kc_list",
    "parse_semicolon_kcs",
    "problem_kc_names",
    "union_tags_concepts_kc_names",
]
