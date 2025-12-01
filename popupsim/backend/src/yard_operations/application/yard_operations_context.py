"""Yard Operations Context - Main entry point."""

from yard_operations.application.yard_operations_config import YardOperationsConfig
from yard_operations.domain.entities.classification_area import ClassificationArea
from yard_operations.domain.entities.parking_area import ParkingArea
from yard_operations.domain.services.hump_yard_service import HumpYardService


class YardOperationsContext:  # pylint: disable=R0903
    """Main context for yard operations including classification and parking.

    Parameters
    ----------
    config : YardOperationsConfig
        Configuration for yard operations
    """

    def __init__(self, config: YardOperationsConfig) -> None:
        self.config = config

        # Initialize classification area
        self.classification_area = ClassificationArea(
            area_id='main_classification',
            track_capacity=config.track_capacity,
            workshop_capacity=config.workshop_capacity,
        )

        # Initialize parking area
        self.parking_area = ParkingArea(parking_tracks=config.parking_tracks, track_capacity=config.track_capacity)

        # Initialize hump yard service
        self.hump_yard_service = HumpYardService(
            classification_area=self.classification_area,
            wagon_state=config.wagon_state,
            wagon_selector=config.wagon_selector,
        )

    def get_hump_yard_service(self) -> HumpYardService:
        """Get hump yard service for wagon classification.

        Returns
        -------
        HumpYardService
            Service for hump yard operations
        """
        return self.hump_yard_service
