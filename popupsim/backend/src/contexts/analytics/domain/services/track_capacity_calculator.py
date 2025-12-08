"""Track capacity metrics calculator."""

from enum import Enum
from typing import Any


class TrackState(Enum):
    """Track capacity state classification."""

    GREEN = 'green'  # < 60% occupied
    YELLOW = 'yellow'  # 60-90% occupied
    RED = 'red'  # > 90% occupied


class TrackCapacityCalculator:
    """Calculates track capacity metrics from state tracking."""

    def __init__(
        self,
        track_capacities: dict[str, float],
        track_occupancy: dict[str, set[str]],
        wagon_lengths: dict[str, float],
    ) -> None:
        """Initialize calculator.

        Parameters
        ----------
        track_capacities : dict[str, float]
            Maximum capacity per track (in length units).
        track_occupancy : dict[str, set[str]]
            Current wagon IDs on each track.
        wagon_lengths : dict[str, float]
            Length of each wagon.
        """
        self.track_capacities = track_capacities
        self.track_occupancy = track_occupancy
        self.wagon_lengths = wagon_lengths

    def calculate(self) -> dict[str, Any]:
        """Calculate track capacity metrics.

        Returns
        -------
        dict[str, Any]
            Track metrics including utilization and state.
        """
        tracks = {}

        for track_id, max_capacity in self.track_capacities.items():
            wagon_ids = self.track_occupancy.get(track_id, set())
            current_capacity = sum(self.wagon_lengths.get(wid, 0.0) for wid in wagon_ids)

            utilization = current_capacity / max_capacity if max_capacity > 0 else 0.0
            state = self._classify_state(utilization)

            tracks[track_id] = {
                'current_capacity': current_capacity,
                'max_capacity': max_capacity,
                'available_capacity': max(0.0, max_capacity - current_capacity),
                'utilization_percent': utilization * 100,
                'wagon_count': len(wagon_ids),
                'state': state.value,
            }

        return {'tracks': tracks, 'total_tracks': len(tracks)}

    def _classify_state(self, utilization: float) -> TrackState:
        """Classify track state based on utilization.

        Parameters
        ----------
        utilization : float
            Utilization ratio (0.0 to 1.0).

        Returns
        -------
        TrackState
            State classification.
        """
        if utilization < 0.6:
            return TrackState.GREEN
        if utilization < 0.9:
            return TrackState.YELLOW
        return TrackState.RED

    def get_track_state(self, track_id: str) -> str:
        """Get state for specific track.

        Parameters
        ----------
        track_id : str
            Track identifier.

        Returns
        -------
        str
            State classification (green/yellow/red).
        """
        max_capacity = self.track_capacities.get(track_id, 0.0)
        if max_capacity == 0:
            return TrackState.GREEN.value

        wagon_ids = self.track_occupancy.get(track_id, set())
        current_capacity = sum(self.wagon_lengths.get(wid, 0.0) for wid in wagon_ids)
        utilization = current_capacity / max_capacity

        return self._classify_state(utilization).value
