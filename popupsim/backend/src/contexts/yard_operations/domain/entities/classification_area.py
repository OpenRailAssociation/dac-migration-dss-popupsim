"""Classification area entity."""

from contexts.yard_operations.domain.value_objects.classification_decision import ClassificationDecision
from shared.domain.entities.wagon import CouplerType
from shared.domain.entities.wagon import Wagon


class ClassificationArea:
    """Entity managing wagon classification operations."""

    def __init__(self) -> None:
        self.classified_wagons: list[Wagon] = []
        self.rejected_wagons: list[Wagon] = []

    def classify(self, wagon: Wagon) -> ClassificationDecision:
        """Classify wagon and make routing decision."""
        # Check if wagon needs retrofit (has SCREW coupler)
        if wagon.coupler_type == CouplerType.SCREW:
            self.classified_wagons.append(wagon)
            return ClassificationDecision.accept_for_retrofit('retrofit_track')
        self.rejected_wagons.append(wagon)
        return ClassificationDecision.reject('Already has DAC coupler')

    def get_wagons_for_retrofit(self, count: int) -> list[Wagon]:
        """Get wagons ready for retrofit."""
        wagons = self.classified_wagons[:count]
        self.classified_wagons = self.classified_wagons[count:]
        return wagons

    def get_classified_count(self) -> int:
        """Get count of classified wagons."""
        return len(self.classified_wagons)

    def get_rejected_count(self) -> int:
        """Get count of rejected wagons."""
        return len(self.rejected_wagons)
