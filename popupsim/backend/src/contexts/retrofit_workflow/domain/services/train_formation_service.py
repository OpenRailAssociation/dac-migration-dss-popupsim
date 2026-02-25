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

    def prepare_train(  # noqa: C901
        self,
        train: TrainMovement,
        process_times: Any,
        current_time: float,
        coupling_event_publisher: Callable[[CouplingEvent], None] | None = None,
    ) -> dict[str, Any]:
        """Prepare train for departure and return operation details.

        Args:
            train: TrainMovement to prepare
            process_times: Process times configuration
            current_time: Current simulation time
            coupling_event_publisher: Optional callback to publish coupling events

        Returns
        -------
            Dict with operation details: {
                'total_time': float,
                'rake_coupling': {'time': float, 'coupler_type': str} or None,
                'loco_coupling': {'time': float, 'coupler_type': str},
                'shunting_prep': float or None,
                'brake_test': float or None,
                'inspection': float or None
            }
        """
        time_offset = 0.0
        operations = {
            'total_time': 0.0,
            'rake_coupling': None,
            'loco_coupling': None,
            'shunting_prep': None,
            'brake_test': None,
            'inspection': None,
        }

        # Step 1: Rake coupling (wagon-to-wagon)
        rake_coupling_time = 0.0
        if train.batch.wagons and len(train.batch.wagons) > 1:
            coupler_type = train.batch.wagons[0].coupler_a.type.value
            rake_coupling_time = self.coupling_service.get_rake_coupling_time(train.batch.wagons)

            operations['rake_coupling'] = {
                'time': rake_coupling_time,
                'coupler_type': coupler_type,
                'location': train.origin,
                'wagon_count': len(train.batch.wagons),
            }

            # Publish coupling events
            if coupling_event_publisher:
                coupling_event_publisher(
                    CouplingEvent(
                        timestamp=current_time,
                        locomotive_id=train.locomotive.id,
                        event_type='RAKE_COUPLING_STARTED',
                        location=train.origin,
                        coupler_type=coupler_type,
                        wagon_count=len(train.batch.wagons),
                        duration=rake_coupling_time,
                        operation_id=train.id,
                    )
                )

                coupling_event_publisher(
                    CouplingEvent(
                        timestamp=current_time + rake_coupling_time,
                        locomotive_id=train.locomotive.id,
                        event_type='RAKE_COUPLING_COMPLETED',
                        location=train.origin,
                        coupler_type=coupler_type,
                        wagon_count=len(train.batch.wagons),
                        duration=rake_coupling_time,
                        operation_id=train.id,
                    )
                )

            time_offset += rake_coupling_time

        # Step 2: Locomotive coupling
        loco_coupling_time = 0.0
        if train.batch.wagons:
            coupler_type = train.batch.wagons[0].coupler_a.type.value
            loco_coupling_time = self.coupling_service.get_loco_coupling_time(train.batch.wagons)

            operations['loco_coupling'] = {
                'time': loco_coupling_time,
                'coupler_type': coupler_type,
            }

            if coupling_event_publisher:
                coupling_event_publisher(
                    CouplingEvent(
                        timestamp=current_time + time_offset,
                        locomotive_id=train.locomotive.id,
                        event_type='LOCO_COUPLING_STARTED',
                        location=train.origin,
                        coupler_type=coupler_type,
                        wagon_count=len(train.batch.wagons),
                        duration=loco_coupling_time,
                        operation_id=train.id,
                    )
                )

                coupling_event_publisher(
                    CouplingEvent(
                        timestamp=current_time + time_offset + loco_coupling_time,
                        locomotive_id=train.locomotive.id,
                        event_type='LOCO_COUPLING_COMPLETED',
                        location=train.origin,
                        coupler_type=coupler_type,
                        wagon_count=len(train.batch.wagons),
                        duration=loco_coupling_time,
                        operation_id=train.id,
                    )
                )
            time_offset += loco_coupling_time

        # Step 3: Shunting preparation (shunting only)
        if train.is_shunting:
            shunting_prep_time = timedelta_to_sim_ticks(process_times.shunting_preparation_time)
            if shunting_prep_time > 0:
                operations['shunting_prep'] = shunting_prep_time
                if coupling_event_publisher and train.batch.wagons:
                    coupling_event_publisher(
                        CouplingEvent(
                            timestamp=current_time + time_offset,
                            locomotive_id=train.locomotive.id,
                            event_type='SHUNTING_PREPARATION',
                            location=train.origin,
                            coupler_type='',
                            wagon_count=len(train.batch.wagons),
                            duration=shunting_prep_time,
                            operation_id=train.id,
                        )
                    )
                time_offset += shunting_prep_time

        # Step 4: Brake test and inspection (mainline only)
        if train.is_mainline:
            train.complete_brake_test()
            train.complete_inspection()

            brake_time = timedelta_to_sim_ticks(process_times.full_brake_test_time)
            inspection_time = timedelta_to_sim_ticks(process_times.technical_inspection_time)

            if brake_time > 0:
                operations['brake_test'] = brake_time
                if coupling_event_publisher and train.batch.wagons:
                    coupling_event_publisher(
                        CouplingEvent(
                            timestamp=current_time + time_offset,
                            locomotive_id=train.locomotive.id,
                            event_type='BRAKE_TEST',
                            location=train.origin,
                            coupler_type='',
                            wagon_count=len(train.batch.wagons),
                            duration=brake_time,
                            operation_id=train.id,
                        )
                    )
                time_offset += brake_time

            if inspection_time > 0:
                operations['inspection'] = inspection_time
                if coupling_event_publisher and train.batch.wagons:
                    coupling_event_publisher(
                        CouplingEvent(
                            timestamp=current_time + time_offset,
                            locomotive_id=train.locomotive.id,
                            event_type='INSPECTION',
                            location=train.origin,
                            coupler_type='',
                            wagon_count=len(train.batch.wagons),
                            duration=inspection_time,
                            operation_id=train.id,
                        )
                    )
                time_offset += inspection_time

        # Mark ready (will validate requirements)
        train.mark_ready_for_departure(current_time)

        operations['total_time'] = time_offset
        return operations

    def dissolve_train(  # pylint: disable=too-many-positional-arguments
        self,
        train: TrainMovement,
        current_time: float,
        coupling_event_publisher: Callable[[CouplingEvent], None] | None = None,
    ) -> dict[str, Any]:
        """Dissolve train and return operation details.

        Args:
            train: TrainMovement to dissolve
            current_time: Current simulation time
            coupling_event_publisher: Optional callback to publish coupling events

        Returns
        -------
            Dict with operation details: {
                'total_time': float,
                'loco_decoupling': {'time': float, 'coupler_type': str},
                'rake_decoupling': {'time': float, 'coupler_type': str} or None
            }
        """
        time_offset = 0.0
        operations = {
            'total_time': 0.0,
            'loco_decoupling': None,
            'rake_decoupling': None,
        }

        # Step 1: Locomotive decoupling
        loco_decoupling_time = self.coupling_service.get_loco_decoupling_time(train.batch.wagons)

        if train.batch.wagons:
            coupler_type = train.batch.wagons[0].coupler_a.type.value

            operations['loco_decoupling'] = {
                'time': loco_decoupling_time,
                'coupler_type': coupler_type,
                'location': train.destination,
            }

            if coupling_event_publisher:
                coupling_event_publisher(
                    CouplingEvent(
                        timestamp=current_time,
                        locomotive_id=train.locomotive.id,
                        event_type='LOCO_DECOUPLING_STARTED',
                        location=train.destination,
                        coupler_type=coupler_type,
                        wagon_count=len(train.batch.wagons),
                        duration=loco_decoupling_time,
                        operation_id=train.id,
                    )
                )

                coupling_event_publisher(
                    CouplingEvent(
                        timestamp=current_time + loco_decoupling_time,
                        locomotive_id=train.locomotive.id,
                        event_type='LOCO_DECOUPLING_COMPLETED',
                        location=train.destination,
                        coupler_type=coupler_type,
                        wagon_count=len(train.batch.wagons),
                        duration=loco_decoupling_time,
                        operation_id=train.id,
                    )
                )
            time_offset += loco_decoupling_time

        # Step 2: Rake decoupling (wagon-to-wagon)
        rake_decoupling_time = 0.0
        if train.batch.wagons and len(train.batch.wagons) > 1:
            coupler_type = train.batch.wagons[0].coupler_a.type.value
            rake_decoupling_time = self.coupling_service.get_rake_decoupling_time(train.batch.wagons)

            operations['rake_decoupling'] = {
                'time': rake_decoupling_time,
                'coupler_type': coupler_type,
                'location': train.destination,
                'wagon_count': len(train.batch.wagons),
            }

            if coupling_event_publisher:
                coupling_event_publisher(
                    CouplingEvent(
                        timestamp=current_time + time_offset,
                        locomotive_id=train.locomotive.id,
                        event_type='RAKE_DECOUPLING_STARTED',
                        location=train.destination,
                        coupler_type=coupler_type,
                        wagon_count=len(train.batch.wagons),
                        duration=rake_decoupling_time,
                        operation_id=train.id,
                    )
                )

                coupling_event_publisher(
                    CouplingEvent(
                        timestamp=current_time + time_offset + rake_decoupling_time,
                        locomotive_id=train.locomotive.id,
                        event_type='RAKE_DECOUPLING_COMPLETED',
                        location=train.destination,
                        coupler_type=coupler_type,
                        wagon_count=len(train.batch.wagons),
                        duration=rake_decoupling_time,
                        operation_id=train.id,
                    )
                )

            time_offset += rake_decoupling_time

        operations['total_time'] = time_offset
        return operations

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
