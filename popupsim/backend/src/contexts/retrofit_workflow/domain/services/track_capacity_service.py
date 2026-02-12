"""Track capacity service for calculating fill levels and capacity management."""

from typing import Any


class TrackCapacityService:
    """Domain service for track capacity calculations."""

    def calculate_fill_level(self, queue: Any, track_capacity: float) -> float:
        """Calculate track fill level as percentage (0.0 to 1.0).

        Args:
            queue: Queue containing wagons
            track_capacity: Maximum track capacity

        Returns
        -------
            Fill level as float between 0.0 and 1.0
        """
        if track_capacity <= 0:
            return 0.0

        total_length = sum(w.length for w in queue.items)
        return total_length / track_capacity
