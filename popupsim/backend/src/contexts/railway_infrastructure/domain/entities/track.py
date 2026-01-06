"""Track specification and capacity management for railway infrastructure.

This module provides the Track value object representing immutable railway
infrastructure specifications. Runtime occupancy state is managed separately
by the TrackOccupancyManager domain service.
"""

from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class TrackType(Enum):
    """Track types in railway infrastructure.

    Attributes
    ----------
    LOCOPARKING : str
        Locomotive parking track
    COLLECTION : str
        Collection track for classified wagons
    MAINLINE : str
        Main line track
    PARKING : str
        Parking area for completed wagons
    RETROFIT : str
        Retrofit staging track
    RETROFITTED : str
        Track for retrofitted wagons
    WORKSHOP : str
        Workshop area track
    """

    LOCOPARKING = 'loco_parking'
    COLLECTION = 'collection'
    MAINLINE = 'mainline'
    PARKING = 'parking_area'
    RETROFIT = 'retrofit'
    RETROFITTED = 'retrofitted'
    WORKSHOP = 'workshop_area'


@dataclass(frozen=True)
class Track:
    """Immutable track specification.

    Represents physical railway infrastructure (not runtime state).

    Parameters
    ----------
    id : UUID
        Unique track identifier
    name : str
        Human-readable track name
    type : TrackType
        Type of track (collection, retrofit, workshop, etc.)
    total_length : float
        Total track length in meters
    fill_factor : float, optional
        Usable capacity factor (default 0.75 = 75%)
    max_wagons : int | None, optional
        Maximum wagon count for workshop tracks (equals retrofit bays), None for other tracks

    Attributes
    ----------
    capacity : float
        Effective capacity in meters (total_length * fill_factor)

    Examples
    --------
    >>> from uuid import uuid4
    >>> track = Track(uuid4(), 'Collection 1', TrackType.COLLECTION, total_length=150.0, fill_factor=0.75)
    >>> track.capacity
    112.5

    >>> workshop = Track(uuid4(), 'Workshop A', TrackType.WORKSHOP, total_length=100.0, max_wagons=5)
    >>> workshop.max_wagons
    5
    """

    id: UUID
    name: str
    type: TrackType
    total_length: float
    fill_factor: float = 0.75
    max_wagons: int | None = None

    @property
    def capacity(self) -> float:
        """Get effective capacity based on fill factor.

        Returns
        -------
        float
            Effective capacity in meters (total_length * fill_factor)
        """
        return self.total_length * self.fill_factor

    def __eq__(self, other: object) -> bool:
        """Equality based on id.

        Parameters
        ----------
        other : object
            Object to compare with

        Returns
        -------
        bool
            True if other is Track with same id
        """
        if not isinstance(other, Track):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on id for use in sets/dicts.

        Returns
        -------
        int
            Hash value based on id
        """
        return hash(self.id)
