"""Yard aggregate - unified facility with multiple operational areas."""

from workshop_operations.domain.entities.locomotive import Locomotive
from yard_operations.domain.entities.yard_area import AreaType
from yard_operations.domain.entities.yard_area import YardArea


class Yard:
    """Main yard aggregate representing a unified railway facility.

    Parameters
    ----------
    yard_id : str
        Unique identifier for the yard
    name : str
        Human-readable name of the yard
    areas : dict[str, YardArea]
        Operational areas within the yard (classification, parking, etc.)
    shared_locomotives : list[Locomotive]
        Locomotives shared across all areas in the yard
    """

    def __init__(
        self,
        yard_id: str,
        name: str,
        areas: dict[str, YardArea] | None = None,
        shared_locomotives: list[Locomotive] | None = None,
    ) -> None:
        self.yard_id = yard_id
        self.name = name
        self.areas = areas or {}
        self.shared_locomotives = shared_locomotives or []

    def add_area(self, area_id: str, area: YardArea) -> None:
        """Add operational area to yard.

        Parameters
        ----------
        area_id : str
            Identifier for the area
        area : YardArea
            Area to add
        """
        self.areas[area_id] = area

    def get_area(self, area_id: str) -> YardArea | None:
        """Get operational area by ID.

        Parameters
        ----------
        area_id : str
            Area identifier

        Returns
        -------
        YardArea | None
            Area if found, None otherwise
        """
        return self.areas.get(area_id)

    def get_areas_by_type(self, area_type: AreaType) -> list[YardArea]:
        """Get all areas of a specific type.

        Parameters
        ----------
        area_type : AreaType
            Type of area to retrieve

        Returns
        -------
        list[YardArea]
            List of areas matching the type
        """
        return [area for area in self.areas.values() if area.area_type == area_type]

    def has_area_type(self, area_type: AreaType) -> bool:
        """Check if yard has area of specific type.

        Parameters
        ----------
        area_type : AreaType
            Type to check for

        Returns
        -------
        bool
            True if yard has area of this type
        """
        return any(area.area_type == area_type for area in self.areas.values())

    def get_total_areas(self) -> int:
        """Get total number of operational areas.

        Returns
        -------
        int
            Number of areas in yard
        """
        return len(self.areas)
