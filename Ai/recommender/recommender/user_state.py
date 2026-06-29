from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from config import (
    MASTERY_WEAK_THRESHOLD,
    MIN_KC_ATTEMPTS,
    RATING_MAX,
    RATING_MIN,
    SKILL_RATING_DELTA,
    USE_WEAKEST_N,
    WEAK_KC_SKILL_BELOW,
    WEAK_KC_SKILL_STRETCH,
    WEAKEST_N_COLUMN,
)
from recommender.kc_normalize import normalize_kc, parse_semicolon_kcs

MASTERY_REQUIRED = frozenset({"student_id", "kc_name", "mastery", "n_attempts"})
WEAKNESS_REQUIRED = frozenset({"student_id", "weak_kcs"})


@dataclass
class UserState:
    student_id: str
    mastery: dict[str, float] = field(default_factory=dict)
    attempts: dict[str, int] = field(default_factory=dict)
    weak_kcs: set[str] = field(default_factory=set)

    def mean_mastery(self) -> float:
        if not self.mastery:
            return 0.5
        return sum(self.mastery.values()) / len(self.mastery)

    def skill_rating_estimate(
        self, rating_min: int = RATING_MIN, rating_max: int = RATING_MAX
    ) -> float:
        m = self.mean_mastery()
        return rating_min + m * (rating_max - rating_min)

    def min_weak_mastery(self) -> float:
        if not self.weak_kcs:
            return self.mean_mastery()
        vals = [self.mastery[k] for k in self.weak_kcs if k in self.mastery]
        return min(vals) if vals else self.mean_mastery()

    def mastery_to_skill(
        self, mastery: float, rating_min: int = RATING_MIN, rating_max: int = RATING_MAX
    ) -> float:
        return rating_min + mastery * (rating_max - rating_min)

    def skill_rating_for_weak_areas(
        self, rating_min: int = RATING_MIN, rating_max: int = RATING_MAX
    ) -> float:
        return self.mastery_to_skill(self.min_weak_mastery(), rating_min, rating_max)

    def rating_band_for_problem(
        self,
        problem_kcs: list[str],
        *,
        remedial: bool = False,
        skill_delta: int = SKILL_RATING_DELTA,
        stretch: int = WEAK_KC_SKILL_STRETCH,
        below: int = WEAK_KC_SKILL_BELOW,
    ) -> tuple[float, float]:
        """Rating window for a candidate; remedial uses mastery on overlapping weak KCs."""
        if remedial and self.weak_kcs:
            weak_on = [kc for kc in problem_kcs if kc in self.weak_kcs]
            if weak_on:
                m = min(self.mastery.get(kc, 0.5) for kc in weak_on)
            else:
                m = self.min_weak_mastery()
            skill = self.mastery_to_skill(m)
            lo = max(RATING_MIN, skill - below)
            hi = skill + stretch
            return lo, hi
        skill = self.skill_rating_estimate()
        return skill - skill_delta, skill + skill_delta


@dataclass
class UserStateStore:
    students: dict[str, UserState]
    source_files: dict[str, str]
    loaded_at: str

    def has_student(self, student_id: str) -> bool:
        return student_id in self.students

    def get(self, student_id: str) -> UserState | None:
        return self.students.get(student_id)


def _validate_columns(path: Path, required: frozenset[str]) -> list[str]:
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty or missing header")
        cols = {c.strip() for c in reader.fieldnames}
        missing = required - cols
        if missing:
            raise ValueError(f"{path}: missing required columns: {sorted(missing)}")
        return list(reader.fieldnames)


def load_user_state(
    mastery_path: Path,
    weakness_path: Path | None = None,
    *,
    weak_threshold: float = MASTERY_WEAK_THRESHOLD,
    min_attempts: int = MIN_KC_ATTEMPTS,
) -> UserStateStore:
    _validate_columns(mastery_path, MASTERY_REQUIRED)
    students: dict[str, UserState] = {}
    has_is_weak = False

    with mastery_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        has_is_weak = "is_weak" in (reader.fieldnames or [])
        for row in reader:
            sid = (row.get("student_id") or "").strip()
            kc = normalize_kc(row.get("kc_name") or "")
            if not sid or not kc:
                continue
            if sid not in students:
                students[sid] = UserState(student_id=sid)
            st = students[sid]
            st.mastery[kc] = float(row.get("mastery") or 0)
            st.attempts[kc] = int(float(row.get("n_attempts") or 0))
            if not USE_WEAKEST_N:
                if has_is_weak and int(row.get("is_weak") or 0) == 1:
                    st.weak_kcs.add(kc)
                elif st.attempts[kc] >= min_attempts and st.mastery[kc] < weak_threshold:
                    st.weak_kcs.add(kc)

    if weakness_path is not None and weakness_path.exists():
        _validate_columns(weakness_path, WEAKNESS_REQUIRED)
        if USE_WEAKEST_N:
            with weakness_path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if WEAKEST_N_COLUMN not in (reader.fieldnames or []):
                    raise ValueError(
                        f"{weakness_path}: missing column {WEAKEST_N_COLUMN!r} "
                        f"(required when USE_WEAKEST_N=True)"
                    )
        with weakness_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sid = (row.get("student_id") or "").strip()
                if not sid or sid not in students:
                    continue
                st = students[sid]
                if USE_WEAKEST_N:
                    kcs = parse_semicolon_kcs(row.get(WEAKEST_N_COLUMN))
                    if not kcs:
                        kcs = parse_semicolon_kcs(row.get("weak_kcs"))
                    st.weak_kcs = set(kcs)
                else:
                    for kc in parse_semicolon_kcs(row.get("weak_kcs")):
                        st.weak_kcs.add(kc)

    if USE_WEAKEST_N:
        for st in students.values():
            if st.weak_kcs:
                continue
            for kc, m in st.mastery.items():
                n = st.attempts.get(kc, 0)
                if n >= min_attempts and m < weak_threshold:
                    st.weak_kcs.add(kc)

    source_files = {"mastery_report": str(mastery_path.resolve())}
    if weakness_path is not None and weakness_path.exists():
        source_files["weakness_summary"] = str(weakness_path.resolve())

    return UserStateStore(
        students=students,
        source_files=source_files,
        loaded_at=datetime.now(timezone.utc).isoformat(),
    )
