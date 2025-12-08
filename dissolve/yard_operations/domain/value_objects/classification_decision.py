"""Classification decision value object."""

from enum import Enum


class ClassificationDecision(Enum):
    """Decision for wagon routing after classification."""

    RETROFIT = "retrofit"  # Send to retrofit area
    REJECT = "reject"  # Reject wagon (no capacity or not eligible)
    BYPASS = "bypass"  # Skip retrofit (already has DAC)
    MAINTENANCE = "maintenance"  # Send to maintenance area
