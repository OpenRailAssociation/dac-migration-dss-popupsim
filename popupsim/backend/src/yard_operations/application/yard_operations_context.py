"""Yard Operations Context - Main entry point."""

from workshop_operations.domain.services.wagon_operations import WagonStateManager
from workshop_operations.infrastructure.resources.track_capacity_manager import TrackCapacityManager
from yard_operations.domain.entities.classification_area import ClassificationArea
from yard_operations.domain.services.hump_yard_service import HumpYardService


class YardOperationsContext:  # pylint: disable=too-few-public-methods
    """Main context for yard operations.

    Provides access to yard operational areas and services.

    Parameters
    ----------
    track_capacity : TrackCapacityManager
        Track capacity manager for yard
    wagon_state : WagonStateManager
        Service for wagon state management
    """

    def __init__(self, track_capacity: TrackCapacityManager, wagon_state: WagonStateManager) -> None:
        self.track_capacity = track_capacity
        self.wagon_state = wagon_state

        # Create classification area
        self.classification_area = ClassificationArea(area_id='hump_classification', track_capacity=track_capacity)

        # Create hump yard service
        self.hump_yard_service = HumpYardService(classification_area=self.classification_area, wagon_state=wagon_state)

    def get_hump_yard_service(self) -> HumpYardService:
        """Get hump yard service for wagon classification.

        Returns
        -------
        HumpYardService
            Service for hump yard operations
        """
        return self.hump_yard_service
