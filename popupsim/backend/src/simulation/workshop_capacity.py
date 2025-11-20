"""Workshop retrofit station capacity management."""

from typing import Any

from models.workshop import Workshop

from .sim_adapter import SimulationAdapter


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

    def __init__(self, sim: SimulationAdapter, workshops: list[Workshop]) -> None:
        self.sim = sim
        self.workshops_by_track: dict[str, Workshop] = {}
        self.resources: dict[str, Any] = {}  # SimPy Resources
        self.stations: dict[str, list[StationState]] = {}  # For metrics

        for workshop in workshops:
            track_id = workshop.track_id
            self.workshops_by_track[track_id] = workshop
            # Create SimPy Resource for station allocation
            self.resources[track_id] = sim.create_resource(capacity=workshop.retrofit_stations)
            # Keep station tracking for metrics/history
            self.stations[track_id] = [
                StationState(f'{track_id}_station_{i}') for i in range(workshop.retrofit_stations)
            ]

    def get_resource(self, track_id: str) -> Any:
        """Get SimPy Resource for requesting stations."""
        return self.resources[track_id]

    def get_available_stations(self, track_id: str) -> int:
        """Get number of available stations (for backward compatibility)."""
        return sum(1 for s in self.stations.get(track_id, []) if not s.is_occupied)

    def occupy_stations(
        self, track_id: str, count: int, current_time: float = 0.0, wagon_id: str | None = None
    ) -> bool:
        """Occupy stations (for backward compatibility - will be removed)."""
        for _ in range(count):
            self.record_station_occupied(track_id, wagon_id or '', current_time)
        return True

    def release_stations(self, track_id: str, count: int, current_time: float = 0.0) -> None:
        """Release stations (for backward compatibility - will be removed)."""
        for _ in range(count):
            self.record_station_released(track_id, current_time)

    def record_station_occupied(self, track_id: str, wagon_id: str, time: float) -> None:
        """Record station occupied for metrics (find first free station)."""
        for station in self.stations.get(track_id, []):
            if not station.is_occupied:
                station.is_occupied = True
                station.last_occupied_time = time
                station.current_wagon_id = wagon_id
                break

    def record_station_released(self, track_id: str, time: float) -> None:
        """Record station released for metrics (find first occupied station)."""
        for station in self.stations.get(track_id, []):
            if station.is_occupied:
                station.is_occupied = False
                if station.last_occupied_time is not None:
                    station.total_busy_time += time - station.last_occupied_time
                    if station.current_wagon_id:
                        station.history.append((station.last_occupied_time, time, station.current_wagon_id))
                station.wagons_completed += 1
                station.current_wagon_id = None
                break
