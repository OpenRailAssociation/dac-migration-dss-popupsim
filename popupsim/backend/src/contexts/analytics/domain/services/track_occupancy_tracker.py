"""Track occupancy tracking over time."""

from typing import Any


class TrackOccupancyTracker:
    """Track wagon counts per track over time."""

    def __init__(self) -> None:
        self.track_history: dict[str, list[tuple[float, int]]] = {}
        self.current_counts: dict[str, int] = {}

    def record_wagon_arrival(self, track: str, sim_time: float) -> None:
        """Record wagon arrival on track."""
        if track not in self.current_counts:
            self.current_counts[track] = 0
            self.track_history[track] = [(0.0, 0)]
        
        self.current_counts[track] += 1
        self.track_history[track].append((sim_time, self.current_counts[track]))

    def record_wagon_departure(self, track: str, sim_time: float) -> None:
        """Record wagon departure from track."""
        if track not in self.current_counts:
            return
        
        self.current_counts[track] = max(0, self.current_counts[track] - 1)
        self.track_history[track].append((sim_time, self.current_counts[track]))

    def get_track_history(self, track: str) -> list[tuple[float, int]]:
        """Get time series for specific track."""
        return self.track_history.get(track, [])

    def get_all_tracks(self) -> list[str]:
        """Get all tracked tracks."""
        return list(self.track_history.keys())
