"""Rake entity for railway operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon
    from shared.domain.value_objects.rake_type import RakeType


@dataclass
class Rake:  # pylint: disable=too-many-instance-attributes
    """A set of wagons coupled together for movement/operation."""

    rake_id: str
    wagons: list[Wagon]
    rake_type: RakeType
    formation_time: float
    formation_track: str
    target_track: str = ''
    locomotive_id: str = ''
    status: str = 'FORMED'

    @property
    def total_length(self) -> float:
        """Calculate total length of all wagons in rake."""
        return sum(wagon.length for wagon in self.wagons)

    @property
    def wagon_count(self) -> int:
        """Get number of wagons in rake."""
        return len(self.wagons)

    @property
    def wagon_ids(self) -> list[str]:
        """Get list of wagon IDs in rake."""
        return [wagon.id for wagon in self.wagons]

    def assign_to_wagons(self) -> None:
        """Assign rake_id to all wagons in this rake."""
        for wagon in self.wagons:
            wagon.rake_id = self.rake_id

    def update_wagon_tracks(self, track_id: str) -> None:
        """Update track for all wagons in rake."""
        for wagon in self.wagons:
            wagon.track = track_id
