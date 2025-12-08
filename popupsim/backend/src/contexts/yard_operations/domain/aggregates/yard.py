"""Yard aggregate - root of yard operations."""

from contexts.yard_operations.domain.entities.classification_area import ClassificationArea
from contexts.yard_operations.domain.entities.parking_area import ParkingArea
from contexts.yard_operations.domain.value_objects.classification_decision import ClassificationDecision
from contexts.yard_operations.domain.value_objects.yard_id import YardId
from shared.domain.entities.wagon import Wagon


class Yard:
    """Yard aggregate - manages classification and parking operations."""

    def __init__(self, yard_id: YardId) -> None:
        self.yard_id = yard_id
        self.classification_area = ClassificationArea()
        self.parking_areas: dict[str, ParkingArea] = {}

    def classify_wagon(self, wagon: Wagon) -> ClassificationDecision:
        """Classify incoming wagon for routing decision."""
        return self.classification_area.classify(wagon)

    def park_wagon(self, wagon: Wagon, area_id: str) -> None:
        """Park wagon in specified area."""
        if area_id in self.parking_areas:
            self.parking_areas[area_id].park_wagon(wagon)

    def pickup_wagons_for_retrofit(self, count: int) -> list[Wagon]:
        """Pick up wagons ready for retrofit."""
        return self.classification_area.get_wagons_for_retrofit(count)

    def add_parking_area(self, area_id: str, parking_area: ParkingArea) -> None:
        """Add parking area to yard."""
        self.parking_areas[area_id] = parking_area
