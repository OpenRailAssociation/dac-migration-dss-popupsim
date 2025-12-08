"""Parking area entity for wagon storage operations."""

from workshop_operations.domain.entities.track import Track
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.infrastructure.resources.track_capacity_manager import (
    TrackCapacityManager,
)


class ParkingArea:  # pylint: disable=too-few-public-methods
    """Parking area for storing wagons awaiting processing or pickup.

    Parameters
    ----------
    parking_tracks : list[Track]
        Available parking tracks
    track_capacity : TrackCapacityManager
        Track capacity manager for space allocation
    """

    def __init__(
        self, parking_tracks: list[Track], track_capacity: TrackCapacityManager
    ) -> None:
        self.parking_tracks = parking_tracks
        self.track_capacity = track_capacity
        self.current_track_index = 0

    def select_parking_track(self, wagons: list[Wagon]) -> Track | None:
        """Select parking track for wagon batch using sequential fill strategy.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to park

        Returns
        -------
        Track | None
            Selected parking track or None if no capacity
        """
        # Try tracks starting from current index (sequential fill)
        for i in range(len(self.parking_tracks)):
            idx = (self.current_track_index + i) % len(self.parking_tracks)
            track = self.parking_tracks[idx]

            # Check if any wagon can fit
            if any(
                self.track_capacity.can_add_wagon(track.id, w.length) for w in wagons
            ):
                self.current_track_index = idx
                return track

        return None

    def get_wagons_that_fit(
        self, track: Track, wagons: list[Wagon]
    ) -> tuple[list[Wagon], list[Wagon]]:
        """Determine which wagons fit on track.

        Parameters
        ----------
        track : Track
            Target parking track
        wagons : list[Wagon]
            Wagons to check

        Returns
        -------
        tuple[list[Wagon], list[Wagon]]
            (wagons_that_fit, wagons_that_dont_fit)
        """
        wagons_to_move = []
        remaining_capacity = self.track_capacity.get_available_capacity(track.id)

        for wagon in wagons:
            if remaining_capacity >= wagon.length:
                wagons_to_move.append(wagon)
                remaining_capacity -= wagon.length

        wagons_to_requeue = [w for w in wagons if w not in wagons_to_move]
        return wagons_to_move, wagons_to_requeue

    def advance_to_next_track(self) -> None:
        """Move to next parking track in rotation."""
        self.current_track_index = (self.current_track_index + 1) % len(
            self.parking_tracks
        )
