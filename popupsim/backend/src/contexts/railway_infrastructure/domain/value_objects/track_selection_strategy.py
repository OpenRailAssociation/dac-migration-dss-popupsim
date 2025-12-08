"""Track selection strategies."""

from enum import Enum


class TrackSelectionStrategy(Enum):
    """Strategy for selecting tracks from available options."""

    LEAST_OCCUPIED = "least_occupied"
    FIRST_AVAILABLE = "first_available"
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
