"""Train Formation Service - creates TrainMovement aggregates for transport."""

from collections.abc import Callable
from typing import Any

from contexts.configuration.application.dtos.route_input_dto import RouteType
from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.aggregates.train_movement_aggregate import TrainMovement
from contexts.retrofit_workflow.domain.aggregates.train_movement_aggregate import TrainType
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.events import CouplingEvent
from contexts.retrofit_workflow.domain.services.coupling_service import CouplingService
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks


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

    def prepare_train(
        self,
        train: TrainMovement,
        process_times: Any,
        current_time: float,
        coupling_event_publisher: Callable[[CouplingEvent], None] | None = None,
    ) -> float:
        """Prepare train for departure and return preparation time.

        For mainline trains: couples loco, performs brake test and inspection
        For shunting: couples loco only

        Args:
            train: TrainMovement to prepare
            process_times: Process times configuration
            current_time: Current simulation time
            coupling_event_publisher: Optional callback to publish coupling events

        Returns
        -------
            Preparation time in simulation ticks
        """
        # Emit loco coupling event
        coupling_time = 0.0
        if coupling_event_publisher and train.batch.wagons:
            coupler_type = train.batch.wagons[0].coupler_a.type.value
            coupling_time = self.coupling_service.get_loco_coupling_time(train.batch.wagons)

            coupling_event_publisher(
                CouplingEvent(
                    timestamp=current_time,
                    locomotive_id=train.locomotive.id,
                    event_type='COUPLING_STARTED',
                    location=train.origin,
                    coupler_type=coupler_type,
                    wagon_count=len(train.batch.wagons),
                    duration=coupling_time,
                    operation_id=train.id,
                )
            )

            coupling_event_publisher(
                CouplingEvent(
                    timestamp=current_time + coupling_time,
                    locomotive_id=train.locomotive.id,
                    event_type='COUPLING_COMPLETED',
                    location=train.origin,
                    coupler_type=coupler_type,
                    wagon_count=len(train.batch.wagons),
                    duration=coupling_time,
                    operation_id=train.id,
                )
            )

        if train.is_mainline:
            # Mainline: complete brake test and inspection
            train.complete_brake_test()
            train.complete_inspection()

            # Emit separate brake test and inspection events
            if coupling_event_publisher and train.batch.wagons:
                brake_time = timedelta_to_sim_ticks(process_times.full_brake_test_time)
                inspection_time = timedelta_to_sim_ticks(process_times.technical_inspection_time)

                if brake_time > 0:
                    coupling_event_publisher(
                        CouplingEvent(
                            timestamp=current_time + coupling_time,
                            locomotive_id=train.locomotive.id,
                            event_type='BRAKE_TEST',
                            location=train.origin,
                            coupler_type='',
                            wagon_count=len(train.batch.wagons),
                            duration=brake_time,
                            operation_id=train.id,
                        )
                    )

                if inspection_time > 0:
                    coupling_event_publisher(
                        CouplingEvent(
                            timestamp=current_time + coupling_time + brake_time,
                            locomotive_id=train.locomotive.id,
                            event_type='INSPECTION',
                            location=train.origin,
                            coupler_type='',
                            wagon_count=len(train.batch.wagons),
                            duration=inspection_time,
                            operation_id=train.id,
                        )
                    )

        # Mark ready (will validate requirements)
        train.mark_ready_for_departure(current_time)

        total_prep_time = train.get_preparation_time(process_times, self.coupling_service)
        return total_prep_time

    def dissolve_train(
        self,
        train: TrainMovement,
        current_time: float,
        coupling_event_publisher: Callable[[CouplingEvent], None] | None = None,
    ) -> float:
        """Dissolve train and return loco decoupling time.

        Args:
            train: TrainMovement to dissolve
            current_time: Current simulation time
            coupling_event_publisher: Optional callback to publish coupling events

        Returns
        -------
            Loco decoupling time in simulation ticks
        """
        decoupling_time = self.coupling_service.get_loco_decoupling_time(train.batch.wagons)

        # Emit loco decoupling event
        if coupling_event_publisher and train.batch.wagons:
            coupler_type = train.batch.wagons[0].coupler_a.type.value

            coupling_event_publisher(
                CouplingEvent(
                    timestamp=current_time,
                    locomotive_id=train.locomotive.id,
                    event_type='DECOUPLING_STARTED',
                    location=train.destination,
                    coupler_type=coupler_type,
                    wagon_count=len(train.batch.wagons),
                    duration=decoupling_time,
                    operation_id=train.id,
                )
            )

            coupling_event_publisher(
                CouplingEvent(
                    timestamp=current_time + decoupling_time,
                    locomotive_id=train.locomotive.id,
                    event_type='DECOUPLING_COMPLETED',
                    location=train.destination,
                    coupler_type=coupler_type,
                    wagon_count=len(train.batch.wagons),
                    duration=decoupling_time,
                    operation_id=train.id,
                )
            )

        return decoupling_time

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
