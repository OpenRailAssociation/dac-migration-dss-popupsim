"""Wagon rejection reasons for yard operations."""

from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class RejectionReason(Enum):
    """Reasons why wagons are rejected at hump yard."""

    TRACK_CAPACITY_FULL = 'track_capacity_full'
    COUPLER_TYPE_MISMATCH = 'coupler_type_mismatch'
    WAGON_TOO_LONG = 'wagon_too_long'
    NO_SUITABLE_TRACK = 'no_suitable_track'
    WORKSHOP_UNAVAILABLE = 'workshop_unavailable'
    TECHNICAL_ISSUE = 'technical_issue'


class RejectionStats(BaseModel):
    """Statistics for wagon rejections by reason."""

    rejection_counts: dict[str, int] = Field(default_factory=dict, description='Count by rejection reason')
    total_rejections: int = Field(default=0, description='Total number of rejections')

    def add_rejection(self, reason: RejectionReason) -> None:
        """Record a wagon rejection with reason."""
        reason_key = reason.value
        self.rejection_counts[reason_key] = self.rejection_counts.get(reason_key, 0) + 1
        self.total_rejections += 1

    def get_top_rejection_reason(self) -> str:
        """Get the most common rejection reason."""
        if not self.rejection_counts:
            return 'No rejections'

        top_reason = max(self.rejection_counts.items(), key=lambda x: x[1])
        return f'{top_reason[0]}: {top_reason[1]} wagons ({top_reason[1] / self.total_rejections * 100:.1f}%)'

    def get_rejection_breakdown(self) -> dict[str, float]:
        """Get percentage breakdown of rejection reasons."""
        if self.total_rejections == 0:
            return {}

        return {reason: (count / self.total_rejections) * 100.0 for reason, count in self.rejection_counts.items()}
