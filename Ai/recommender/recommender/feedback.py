
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class FeedbackRecord:
    student_id: str
    problem_id: str
    recommended_at: str
    attempted: bool
    mastery_before: dict[str, float]
    mastery_after: dict[str, float]
    realized_gain: float

    @classmethod
    def now(cls, **kwargs) -> FeedbackRecord:
        if "recommended_at" not in kwargs:
            kwargs["recommended_at"] = datetime.now(timezone.utc).isoformat()
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return asdict(self)
