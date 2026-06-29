
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from config import RATING_MIN
from recommender.kc_normalize import normalize_kc, problem_kc_names


@dataclass
class ProblemRecord:
    problem_id: str
    rating: int
    kc_names: list[str] = field(default_factory=list)
    parent_topic: str = ""

    @property
    def normalized_rating(self) -> float:
        from config import RATING_MAX, RATING_MIN

        r = max(RATING_MIN, min(RATING_MAX, float(self.rating)))
        return (r - RATING_MIN) / (RATING_MAX - RATING_MIN)


class ProblemCatalog:
    def __init__(self, records: dict[str, ProblemRecord]) -> None:
        self._records = records
        self._kc_freq: dict[str, int] | None = None

    def __len__(self) -> int:
        return len(self._records)

    def get(self, problem_id: str) -> ProblemRecord | None:
        return self._records.get(problem_id)

    def all_ids(self) -> list[str]:
        return list(self._records.keys())

    def iter_records(self):
        return self._records.values()

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for pid, rec in self._records.items():
            rows.append(
                {
                    "problem_id": pid,
                    "rating": rec.rating,
                    "normalized_rating": rec.normalized_rating,
                    "kc_names": rec.kc_names,
                    "parent_topic": rec.parent_topic,
                    "n_kcs": len(rec.kc_names),
                }
            )
        return pd.DataFrame(rows)

    def global_kc_frequencies(self) -> dict[str, int]:
        if self._kc_freq is not None:
            return self._kc_freq
        freq: dict[str, int] = {}
        for rec in self._records.values():
            for kc in rec.kc_names:
                freq[kc] = freq.get(kc, 0) + 1
        self._kc_freq = freq
        return freq

    def save_parquet(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        df = self.to_dataframe()
        df["kc_names"] = df["kc_names"].apply(lambda xs: ";".join(xs))
        df.to_parquet(path, index=False)

    @classmethod
    def from_parquet(cls, path: Path) -> ProblemCatalog:
        df = pd.read_parquet(path)
        records: dict[str, ProblemRecord] = {}
        for _, row in df.iterrows():
            kcs = [k.strip() for k in str(row["kc_names"]).split(";") if k.strip()]
            records[str(row["problem_id"])] = ProblemRecord(
                problem_id=str(row["problem_id"]),
                rating=int(row["rating"]),
                kc_names=[normalize_kc(k) for k in kcs],
                parent_topic=str(row.get("parent_topic") or (kcs[0] if kcs else "")),
            )
        return cls(records)


def load_catalog(problems_path: Path) -> ProblemCatalog:
    records: dict[str, ProblemRecord] = {}
    with problems_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = (row.get("id") or "").strip()
            if not pid:
                continue
            raw_rating = (row.get("rating") or "").strip()
            try:
                rating = int(float(raw_rating)) if raw_rating else RATING_MIN
            except ValueError:
                rating = RATING_MIN
            kcs = problem_kc_names(row.get("tags"), row.get("concepts"))
            parent = kcs[0] if kcs else ""
            records[pid] = ProblemRecord(
                problem_id=pid,
                rating=rating,
                kc_names=kcs,
                parent_topic=parent,
            )
    return ProblemCatalog(records)
