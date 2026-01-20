"""Rake Aggregate - references wagons, doesn't own them."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class RakeType(Enum):
    """Rake type enum."""

    WORKSHOP_RAKE = 'WORKSHOP_RAKE'
    RETROFITTED_RAKE = 'RETROFITTED_RAKE'
    PARKING_RAKE = 'PARKING_RAKE'


@dataclass
class Rake:
    """Rake Aggregate Root.

    A rake REFERENCES wagons but doesn't own them.
    Wagons are independent entities that can be grouped into rakes
    for transport purposes.

    This is a temporary grouping - rake can be dissolved after transport.

    Attributes
    ----------
        id: Unique rake identifier
        wagon_ids: List of wagon IDs (references, not ownership)
        rake_type: Type of rake
        formation_track: Track where rake was formed
        target_track: Target track for transport
        formation_time: Time when rake was formed
    """

    id: str
    wagon_ids: list[str]  # References, not ownership!
    rake_type: RakeType
    formation_track: str
    target_track: str
    formation_time: float

    # Cached total length (set during formation)
    _total_length: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """Validate rake."""
        if not self.wagon_ids:
            raise ValueError(f'Rake {self.id} must have at least one wagon')

    @property
    def wagon_count(self) -> int:
        """Get number of wagons in rake."""
        return len(self.wagon_ids)

    @property
    def total_length(self) -> float:
        """Get total length in meters (cached)."""
        return self._total_length

    def set_total_length(self, length: float) -> None:
        """Set total length (called during formation).

        Args:
            length: Total length in meters
        """
        self._total_length = length

    def add_wagon_reference(self, wagon_id: str) -> None:
        """Add wagon reference to rake.

        Args:
            wagon_id: Wagon to add
        """
        if wagon_id not in self.wagon_ids:
            self.wagon_ids.append(wagon_id)

    def remove_wagon_reference(self, wagon_id: str) -> None:
        """Remove wagon reference from rake.

        Args:
            wagon_id: Wagon to remove
        """
        if wagon_id in self.wagon_ids:
            self.wagon_ids.remove(wagon_id)

    def get_coupling_coupler_type(self, wagon_repository) -> str:
        """Get coupler type for locomotive coupling.

        Args:
            wagon_repository: Repository to resolve wagon entities

        Returns
        -------
            Coupler type of first wagon for locomotive coupling
        """
        if not self.wagon_ids:
            raise ValueError(f'Rake {self.id} has no wagons')

        first_wagon = wagon_repository.get_by_id(self.wagon_ids[0])
        return first_wagon.coupler_a.type.value

    def get_first_wagon(self, wagon_repository) -> Wagon:
        """Get first wagon entity for coupling validation.

        Args:
            wagon_repository: Repository to resolve wagon entities

        Returns
        -------
            First wagon entity in the rake
        """
        if not self.wagon_ids:
            raise ValueError(f'Rake {self.id} has no wagons')

        return wagon_repository.get_by_id(self.wagon_ids[0])

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f'Rake(id={self.id}, type={self.rake_type.value}, '
            f'wagons={self.wagon_count}, length={self.total_length:.1f}m)'
        )
