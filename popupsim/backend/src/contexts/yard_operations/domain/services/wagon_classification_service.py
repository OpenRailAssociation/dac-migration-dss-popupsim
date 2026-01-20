"""Wagon Classification Domain Service.

Pure business logic for wagon classification - no infrastructure dependencies.
"""

from typing import Any

from contexts.yard_operations.domain.services.hump_yard_service import YardConfiguration
from shared.domain.entities.wagon import Wagon
from shared.domain.entities.wagon import WagonStatus


class ClassificationResult:
    """Value object representing classification outcome."""

    def __init__(self, accepted_wagons: list[Wagon], rejected_wagons: list[Wagon], train_id: str) -> None:
        self.accepted_wagons = accepted_wagons
        self.rejected_wagons = rejected_wagons
        self.train_id = train_id


class WagonClassificationService:
    """Domain service for wagon classification business logic."""

    def __init__(self, hump_yard_service: Any) -> None:
        self._hump_yard_service = hump_yard_service

    def classify_train(
        self, wagons: list[Wagon], train_id: str, yard_config: YardConfiguration, selected_track_id: str
    ) -> ClassificationResult:
        """Classify train wagons using pure business logic."""
        # Use existing hump yard service for classification logic
        classification_result = self._hump_yard_service.classify_wagons(
            wagons,
            yard_config,
            selected_track_id,  # Use provided track ID
        )

        # Enrich wagons with train context
        for wagon in classification_result.accepted_wagons:
            wagon.train_id = train_id
            wagon.status = WagonStatus.TO_BE_RETROFFITED

        for wagon in classification_result.rejected_wagons:
            wagon.train_id = train_id
            wagon.status = WagonStatus.REJECTED
            wagon.rejection_time = 0.0  # Will be set by application service

        return ClassificationResult(
            classification_result.accepted_wagons, classification_result.rejected_wagons, train_id
        )
