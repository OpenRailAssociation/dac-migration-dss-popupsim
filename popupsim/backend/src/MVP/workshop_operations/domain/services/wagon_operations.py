"""Wagon business logic - no simulation dependencies."""

from MVP.workshop_operations.domain.entities.wagon import (
    Wagon,
    WagonStatus,
)


class WagonStateManager:
    """Manages wagon state transitions."""

    @staticmethod
    def start_movement(wagon: Wagon, from_track: str, to_track: str) -> None:
        """Update wagon state when starting movement."""
        wagon.status = WagonStatus.MOVING
        wagon.source_track_id = from_track
        wagon.destination_track_id = to_track
        wagon.track = None

    @staticmethod
    def complete_arrival(wagon: Wagon, track: str, status: WagonStatus) -> None:
        """Update wagon state when arriving at destination."""
        wagon.track = track
        wagon.source_track_id = None
        wagon.destination_track_id = None
        wagon.status = status

    @staticmethod
    def select_for_retrofit(wagon: Wagon, track_id: str) -> None:
        """Mark wagon as selected for retrofit."""
        wagon.track = track_id
        wagon.status = WagonStatus.SELECTED

    @staticmethod
    def reject_wagon(wagon: Wagon) -> None:
        """Mark wagon as rejected."""
        wagon.status = WagonStatus.REJECTED

    @staticmethod
    def mark_on_retrofit_track(wagon: Wagon) -> None:
        """Mark wagon as on retrofit track."""
        wagon.status = WagonStatus.ON_RETROFIT_TRACK

    @staticmethod
    def mark_moving_to_station(wagon: Wagon) -> None:
        """Mark wagon as moving to station."""
        wagon.status = WagonStatus.MOVING_TO_STATION


class WagonSelector:
    """Wagon selection business rules."""

    @staticmethod
    def needs_retrofit(wagon: Wagon) -> bool:
        """Check if wagon needs retrofit."""
        return wagon.needs_retrofit and not wagon.is_loaded

    @staticmethod
    def filter_selected_wagons(wagons: list[Wagon]) -> dict[str, list[Wagon]]:
        """Group selected wagons by track."""
        wagons_by_track: dict[str, list[Wagon]] = {}
        for wagon in wagons:
            if wagon.status == WagonStatus.SELECTED and wagon.track:
                wagons_by_track.setdefault(wagon.track, []).append(wagon)
        return wagons_by_track

    @staticmethod
    def group_by_retrofit_track(
        wagons_with_tracks: list[tuple[Wagon, str]],
    ) -> dict[str, list[Wagon]]:
        """Group wagons by their destination retrofit track."""
        wagons_by_retrofit: dict[str, list[Wagon]] = {}
        for wagon, retrofit_track_id in wagons_with_tracks:
            wagons_by_retrofit.setdefault(retrofit_track_id, []).append(wagon)
        return wagons_by_retrofit
