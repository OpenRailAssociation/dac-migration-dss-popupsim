"""Workshop retrofit station capacity management."""

from models.workshop import Workshop


class WorkshopCapacityManager:
    """Manages retrofit station capacity for workshops."""

    def __init__(self, workshops: list[Workshop]) -> None:
        self.workshops_by_track: dict[str, Workshop] = {}
        self.occupied_stations: dict[str, int] = {}

        for workshop in workshops:
            self.workshops_by_track[workshop.track_id] = workshop
            self.occupied_stations[workshop.track_id] = 0

    def get_available_stations(self, track_id: str) -> int:
        """Get number of available retrofit stations on track."""
        if track_id not in self.workshops_by_track:
            return 0
        workshop = self.workshops_by_track[track_id]
        return workshop.retrofit_stations - self.occupied_stations[track_id]

    def occupy_stations(self, track_id: str, count: int) -> bool:
        """Occupy retrofit stations. Returns True if successful."""
        available = self.get_available_stations(track_id)
        if count <= available:
            self.occupied_stations[track_id] += count
            return True
        return False

    def release_stations(self, track_id: str, count: int) -> None:
        """Release retrofit stations."""
        if track_id in self.occupied_stations:
            self.occupied_stations[track_id] = max(0, self.occupied_stations[track_id] - count)
