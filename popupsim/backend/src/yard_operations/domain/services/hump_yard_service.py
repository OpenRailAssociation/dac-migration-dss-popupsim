"""Hump yard service for wagon classification operations."""

from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.wagon import WagonStatus
from workshop_operations.domain.services.wagon_operations import WagonSelector
from workshop_operations.domain.services.wagon_operations import WagonStateManager
from yard_operations.domain.entities.classification_area import ClassificationArea
from yard_operations.domain.value_objects.classification_decision import ClassificationDecision


class HumpYardService:  # pylint: disable=too-few-public-methods
    """Service for hump yard wagon classification operations.

    Parameters
    ----------
    classification_area : ClassificationArea
        Classification area for wagon sorting
    wagon_state : WagonStateManager
        Service for managing wagon state transitions
    """

    def __init__(
        self, classification_area: ClassificationArea, wagon_state: WagonStateManager, wagon_selector: WagonSelector
    ) -> None:
        self.classification_area = classification_area
        self.wagon_state = wagon_state
        self.wagon_selector = wagon_selector

    def process_wagon(
        self, wagon: Wagon, wagons_queue: list[Wagon], rejected_queue: list[Wagon]
    ) -> ClassificationDecision:
        """Process wagon through hump yard classification.

        Parameters
        ----------
        wagon : Wagon
            Wagon to process
        wagons_queue : list[Wagon]
            Queue for wagons selected for retrofit
        rejected_queue : list[Wagon]
            Queue for rejected wagons

        Returns
        -------
        ClassificationDecision
            Classification decision made for wagon
        """
        wagon.status = WagonStatus.SELECTING

        decision, collection_track_id = self.classification_area.classify_wagon(wagon)

        if decision == ClassificationDecision.RETROFIT and collection_track_id:
            self.classification_area.track_capacity.add_wagon(collection_track_id, wagon.length)
            self.wagon_state.select_for_retrofit(wagon, collection_track_id)
            wagons_queue.append(wagon)
        elif decision == ClassificationDecision.BYPASS:
            # Wagon already has DAC, bypass retrofit
            self.wagon_state.reject_wagon(wagon)
            rejected_queue.append(wagon)
        else:
            # Reject wagon (no capacity or other reason)
            self.wagon_state.reject_wagon(wagon)
            rejected_queue.append(wagon)

        return decision
