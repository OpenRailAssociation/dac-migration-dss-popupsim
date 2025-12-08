"""Hump yard service for wagon classification operations."""

from MVP.workshop_operations.domain.entities.wagon import (
    Wagon,
    WagonStatus,
)
from MVP.workshop_operations.domain.services.wagon_operations import (
    WagonSelector,
    WagonStateManager,
)
from MVP.yard_operations.domain.entities.classification_area import (
    ClassificationArea,
)
from MVP.yard_operations.domain.value_objects.classification_decision import (
    ClassificationDecision,
)
from MVP.yard_operations.domain.value_objects.rejection_reason import (
    RejectionReason,
    RejectionStats,
)


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
        self,
        classification_area: ClassificationArea,
        wagon_state: WagonStateManager,
        wagon_selector: WagonSelector,
    ) -> None:
        self.classification_area = classification_area
        self.wagon_state = wagon_state
        self.wagon_selector = wagon_selector
        self.rejection_stats = RejectionStats()

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
            self.classification_area.track_capacity.add_wagon(
                collection_track_id, wagon.length
            )
            self.wagon_state.select_for_retrofit(wagon, collection_track_id)
            wagons_queue.append(wagon)
        elif decision == ClassificationDecision.BYPASS:
            # Wagon already has DAC, bypass retrofit
            self.wagon_state.reject_wagon(wagon)
            rejected_queue.append(wagon)
            # No rejection reason needed for bypass (not a failure)
        else:
            # Reject wagon - determine reason
            rejection_reason = self._determine_rejection_reason(
                wagon, collection_track_id
            )
            self.rejection_stats.add_rejection(rejection_reason)
            self.wagon_state.reject_wagon(wagon)
            rejected_queue.append(wagon)

        return decision

    def _determine_rejection_reason(
        self, wagon: Wagon, collection_track_id: str | None
    ) -> RejectionReason:
        """Determine why a wagon was rejected."""
        if collection_track_id is None:
            return RejectionReason.NO_SUITABLE_TRACK

        # Check if track capacity is full
        if not self.classification_area.track_capacity.can_add_wagon(
            collection_track_id, wagon.length
        ):
            return RejectionReason.TRACK_CAPACITY_FULL

        # Check wagon length
        if wagon.length > 25.0:  # Assume max wagon length
            return RejectionReason.WAGON_TOO_LONG

        # Default to technical issue if no other reason found
        return RejectionReason.TECHNICAL_ISSUE

    def get_rejection_stats(self) -> RejectionStats:
        """Get current rejection statistics."""
        return self.rejection_stats
