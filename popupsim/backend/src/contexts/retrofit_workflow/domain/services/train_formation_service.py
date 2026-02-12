"""Train Formation Service - creates TrainMovement aggregates for transport."""

from typing import Any

from contexts.configuration.application.dtos.route_input_dto import RouteType
from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.aggregates.train_movement_aggregate import TrainMovement
from contexts.retrofit_workflow.domain.aggregates.train_movement_aggregate import TrainType
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.services.coupling_service import CouplingService


class TrainFormationService:
    """Domain service for forming trains (locomotive + rake) for transport.

    Handles both mainline and shunting operations with appropriate preparation times.
    """

    def __init__(self, coupling_service: CouplingService) -> None:
        """Initialize train formation service.

        Args:
            coupling_service: Service for calculating coupling/decoupling times
        """
        self.train_counter = 0
        self.coupling_service = coupling_service

    def form_train(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        locomotive: Locomotive,
        batch: BatchAggregate,
        origin: str,
        destination: str,
        route_type: RouteType,
    ) -> TrainMovement:
        """Form a train movement from locomotive and batch.

        Parameters
        ----------
            locomotive: Locomotive
                Locomotive to pull the train
            batch: BatchAggregate
                BatchAggregate (rake of wagons)
            origin: str
                Starting location
            destination: str
                Target location
            route_type: RouteType
                MAINLINE or SHUNTING

        Returns
        -------
            TrainMovement aggregate
        """
        self.train_counter += 1
        train_id = f'TRAIN-{origin.upper()}-{destination.upper()}-{self.train_counter}'

        # Convert RouteType to TrainType
        train_type = TrainType.MAINLINE if route_type == RouteType.MAINLINE else TrainType.SHUNTING

        return TrainMovement(
            id=train_id,
            locomotive=locomotive,
            batch=batch,
            train_type=train_type,
            origin=origin,
            destination=destination,
        )

    def prepare_train(self, train: TrainMovement, process_times: Any, current_time: float) -> float:
        """Prepare train for departure and return preparation time.

        For mainline trains: couples loco, performs brake test and inspection
        For shunting: couples loco only

        Args:
            train: TrainMovement to prepare
            process_times: Process times configuration
            current_time: Current simulation time

        Returns
        -------
            Preparation time in simulation ticks
        """
        if train.is_mainline:
            # Mainline: complete brake test and inspection
            train.complete_brake_test()
            train.complete_inspection()

        # Mark ready (will validate requirements)
        train.mark_ready_for_departure(current_time)

        return train.get_preparation_time(process_times, self.coupling_service)

    def dissolve_train(self, train: TrainMovement) -> float:
        """Dissolve train and return loco decoupling time.

        Args:
            train: TrainMovement to dissolve

        Returns
        -------
            Loco decoupling time in simulation ticks
        """
        return self.coupling_service.get_loco_decoupling_time(train.batch.wagons)

    def can_form_train(self, locomotive: Locomotive, batch: BatchAggregate) -> tuple[bool, str | None]:
        """Validate if train can be formed.

        Args:
            locomotive: Locomotive to check
            batch: Batch to check

        Returns
        -------
            Tuple of (can_form, error_message)
        """
        if not locomotive:
            return False, 'No locomotive provided'

        if not batch:
            return False, 'No batch provided'

        if batch.wagon_count == 0:
            return False, 'Batch has no wagons'

        # Could add more validation (coupler compatibility, etc.)
        return True, None
