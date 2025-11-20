"""Workshop retrofit station capacity management."""

from models.workshop import Workshop


class StationState:
    """Track state of a single retrofit station."""
    def __init__(self, station_id: str) -> None:
        self.station_id = station_id
        self.is_occupied = False
        self.total_busy_time = 0.0
        self.last_occupied_time: float | None = None
        self.wagons_completed = 0
        self.current_wagon_id: str | None = None
        self.history: list[tuple[float, float, str]] = []  # (start_time, end_time, wagon_id)


class WorkshopCapacityManager:
    """Manages retrofit station capacity for workshops."""

    def __init__(self, workshops: list[Workshop]) -> None:
        self.workshops_by_track: dict[str, Workshop] = {}
        self.occupied_stations: dict[str, int] = {}
        self.stations: dict[str, list[StationState]] = {}

        for workshop in workshops:
            self.workshops_by_track[workshop.track_id] = workshop
            self.occupied_stations[workshop.track_id] = 0
            self.stations[workshop.track_id] = [
                StationState(f"{workshop.track_id}_station_{i}")
                for i in range(workshop.retrofit_stations)
            ]

    def get_available_stations(self, track_id: str) -> int:
        """Get number of available retrofit stations on track."""
        if track_id not in self.workshops_by_track:
            return 0
        workshop = self.workshops_by_track[track_id]
        return workshop.retrofit_stations - self.occupied_stations[track_id]

    def occupy_stations(self, track_id: str, count: int, current_time: float = 0.0, wagon_id: str | None = None) -> bool:
        """Occupy retrofit stations. Returns True if successful."""
        available = self.get_available_stations(track_id)
        if count <= available:
            self.occupied_stations[track_id] += count
            stations = self.stations.get(track_id, [])
            occupied_count = 0
            for station in stations:
                if not station.is_occupied and occupied_count < count:
                    station.is_occupied = True
                    station.last_occupied_time = current_time
                    station.current_wagon_id = wagon_id
                    occupied_count += 1
            return True
        return False

    def release_stations(self, track_id: str, count: int, current_time: float = 0.0) -> None:
        """Release retrofit stations."""
        if track_id in self.occupied_stations:
            self.occupied_stations[track_id] = max(0, self.occupied_stations[track_id] - count)
            stations = self.stations.get(track_id, [])
            released_count = 0
            for station in stations:
                if station.is_occupied and released_count < count:
                    station.is_occupied = False
                    if station.last_occupied_time is not None:
                        station.total_busy_time += current_time - station.last_occupied_time
                        if station.current_wagon_id:
                            station.history.append((station.last_occupied_time, current_time, station.current_wagon_id))
                    station.wagons_completed += 1
                    station.current_wagon_id = None
                    released_count += 1
    

