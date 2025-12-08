"""Classification decision value object."""

from dataclasses import dataclass
from enum import Enum


class DecisionType(Enum):
    """Types of classification decisions."""

    ACCEPT_FOR_RETROFIT = 'accept_for_retrofit'
    REJECT = 'reject'
    PARK = 'park'


@dataclass(frozen=True)
class ClassificationDecision:
    """Decision made during wagon classification."""

    decision_type: DecisionType
    reason: str
    target_location: str | None = None

    @classmethod
    def accept_for_retrofit(cls, target_location: str) -> 'ClassificationDecision':
        """Create decision to accept wagon for retrofit."""
        return cls(
            decision_type=DecisionType.ACCEPT_FOR_RETROFIT,
            reason='Wagon accepted for retrofit',
            target_location=target_location,
        )

    @classmethod
    def reject(cls, reason: str) -> 'ClassificationDecision':
        """Create decision to reject wagon."""
        return cls(decision_type=DecisionType.REJECT, reason=reason)

    @classmethod
    def park(cls, target_location: str) -> 'ClassificationDecision':
        """Create decision to park wagon."""
        return cls(
            decision_type=DecisionType.PARK,
            reason='Wagon parked',
            target_location=target_location,
        )
