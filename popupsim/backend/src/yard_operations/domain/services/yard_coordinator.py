"""Yard coordinator service for cross-area operations."""

from workshop_operations.domain.entities.wagon import Wagon
from yard_operations.domain.aggregates.yard import Yard
from yard_operations.domain.entities.yard_area import AreaType
from yard_operations.domain.entities.yard_area import YardArea
from yard_operations.domain.value_objects.classification_decision import ClassificationDecision


class YardCoordinator:
    """Service for coordinating operations across yard areas.

    Parameters
    ----------
    yard : Yard
        Yard to coordinate operations for
    """

    def __init__(self, yard: Yard) -> None:
        self.yard = yard

    def route_wagon_to_area(self, wagon: Wagon, decision: ClassificationDecision) -> YardArea | None:  # pylint: disable=unused-argument
        """Route wagon to appropriate area based on classification decision.

        Parameters
        ----------
        wagon : Wagon
            Wagon to route (reserved for future use)
        decision : ClassificationDecision
            Classification decision for wagon

        Returns
        -------
        YardArea | None
            Target area for wagon, None if no suitable area found
        """
        if decision == ClassificationDecision.RETROFIT:
            # Route to retrofitting area if available
            retrofit_areas = self.yard.get_areas_by_type(AreaType.RETROFITTING)
            return retrofit_areas[0] if retrofit_areas else None

        if decision == ClassificationDecision.BYPASS:
            # Route to parking area for bypass wagons
            parking_areas = self.yard.get_areas_by_type(AreaType.PARKING)
            return parking_areas[0] if parking_areas else None

        if decision == ClassificationDecision.MAINTENANCE:
            # Route to maintenance area
            maintenance_areas = self.yard.get_areas_by_type(AreaType.MAINTENANCE)
            return maintenance_areas[0] if maintenance_areas else None

        # REJECT - no routing needed
        return None

    def get_classification_area(self) -> YardArea | None:
        """Get classification area from yard.

        Returns
        -------
        YardArea | None
            Classification area if exists
        """
        classification_areas = self.yard.get_areas_by_type(AreaType.CLASSIFICATION)
        return classification_areas[0] if classification_areas else None

    def get_parking_area(self) -> YardArea | None:
        """Get parking area from yard.

        Returns
        -------
        YardArea | None
            Parking area if exists
        """
        parking_areas = self.yard.get_areas_by_type(AreaType.PARKING)
        return parking_areas[0] if parking_areas else None

    def has_capacity_for_wagon(self, area_type: AreaType) -> bool:
        """Check if yard has capacity in specific area type.

        Parameters
        ----------
        area_type : AreaType
            Type of area to check

        Returns
        -------
        bool
            True if area has capacity
        """
        areas = self.yard.get_areas_by_type(area_type)
        return any(area.has_capacity() for area in areas)
