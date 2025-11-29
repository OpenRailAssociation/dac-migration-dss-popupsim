"""Classification area entity for hump yard operations."""

from dataclasses import dataclass

from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.infrastructure.resources.track_capacity_manager import TrackCapacityManager
from yard_operations.domain.value_objects.classification_decision import ClassificationDecision


@dataclass
class ClassificationArea:  # pylint: disable=too-few-public-methods
    """Hump yard classification area for wagon sorting.

    Parameters
    ----------
    area_id : str
        Unique identifier for classification area
    track_capacity : TrackCapacityManager
        Track capacity manager for collection tracks
    """

    area_id: str
    track_capacity: TrackCapacityManager

    def classify_wagon(self, wagon: Wagon) -> tuple[ClassificationDecision, str | None]:
        """Classify wagon and determine routing.

        Parameters
        ----------
        wagon : Wagon
            Wagon to classify

        Returns
        -------
        tuple[ClassificationDecision, str | None]
            Classification decision and collection track ID (if retrofit)
        """
        # Check if wagon needs retrofit
        if not wagon.needs_retrofit:
            return (ClassificationDecision.BYPASS, None)

        # Try to allocate collection track
        collection_track_id = self.track_capacity.select_collection_track(wagon.length)

        if collection_track_id:
            return (ClassificationDecision.RETROFIT, collection_track_id)

        # No capacity available
        return (ClassificationDecision.REJECT, None)
