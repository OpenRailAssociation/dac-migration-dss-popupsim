"""Severity value object."""

from dataclasses import dataclass
from enum import Enum


class SeverityLevel(Enum):
    """Severity levels for alerts and violations."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    def __lt__(self, other: "SeverityLevel") -> bool:
        order = {
            SeverityLevel.INFO: 0,
            SeverityLevel.WARNING: 1,
            SeverityLevel.CRITICAL: 2,
        }
        return order[self] < order[other]


@dataclass(frozen=True)
class Severity:
    """Severity with level and score."""

    level: SeverityLevel
    score: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            msg = "Severity score must be between 0.0 and 1.0"
            raise ValueError(msg)

    def is_critical(self) -> bool:
        """Check if severity is critical."""
        return self.level == SeverityLevel.CRITICAL

    def is_warning(self) -> bool:
        """Check if severity is warning."""
        return self.level == SeverityLevel.WARNING

    @classmethod
    def from_score(cls, score: float) -> "Severity":
        """Create severity from score."""
        if score >= 0.8:
            return cls(SeverityLevel.CRITICAL, score)
        if score >= 0.5:
            return cls(SeverityLevel.WARNING, score)
        return cls(SeverityLevel.INFO, score)
