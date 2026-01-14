"""Yard Operations Context - application layer.

Todo
----
    Remove the pickup planning. The logic is easier:
        - Check capacity on retrofit tracks
        - Choose distributon strategy (Most empty, Round robin, ...)
        - Create rakes. Compute distribution of wagons onto the retrofit tracks.
          But take care to create rake from head
        - Execute rakes
        - Shedule remaining wagons (current implementation is still odd)
"""
# pylint: disable=too-many-lines
# ruff: noqa: C901, PLR0912, PLR0915
# TODO: Refactoring is needed here. This is just for the MVP to get it running

from collections.abc import Generator
import time
from typing import Any

from contexts.railway_infrastructure.domain.services.track_selection_service import SelectionStrategy
from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
from contexts.yard_operations.domain.aggregates.yard import Yard
from contexts.yard_operations.domain.events.yard_events import WagonDistributedEvent
from contexts.yard_operations.domain.events.yard_events import WagonParkedEvent
from contexts.yard_operations.domain.services.hump_yard_service import HumpYardService
from contexts.yard_operations.domain.services.hump_yard_service import YardConfiguration
from contexts.yard_operations.domain.services.hump_yard_service import YardType
from contexts.yard_operations.domain.services.step_planners import CollectionToRetrofitPlanner
from contexts.yard_operations.domain.services.step_planners import RetrofittedToParkingPlanner
from contexts.yard_operations.domain.services.step_planners import RetrofitToWorkshopPlanner
from contexts.yard_operations.domain.services.step_planners import WorkshopToRetrofittedPlanner
from contexts.yard_operations.domain.services.wagon_classification_service import WagonClassificationService
from contexts.yard_operations.domain.services.wagon_pickup_service import WagonPickupService
from contexts.yard_operations.domain.services.workshop_batching_service import WorkshopBatchingService
from contexts.yard_operations.domain.value_objects.yard_id import YardId
from infrastructure.logging import get_process_logger
from shared.domain.entities.rake import Rake
from shared.domain.entities.wagon import Wagon
from shared.domain.entities.wagon import WagonStatus
from shared.domain.events.rake_events import RakeFormedEvent
from shared.domain.events.rake_events import RakeTransportRequestedEvent
from shared.domain.events.wagon_lifecycle_events import TrainArrivedEvent
from shared.domain.events.wagon_lifecycle_events import TrainDepartedEvent
from shared.domain.events.wagon_lifecycle_events import WagonReadyForRetrofitEvent
from shared.domain.events.wagon_lifecycle_events import WagonRetrofitCompletedEvent
from shared.domain.events.wagon_lifecycle_events import WagonsClassifiedEvent
from shared.domain.events.wagon_lifecycle_events import WagonsReadyForPickupEvent
from shared.domain.events.wagon_movement_events import WagonMovedEvent
from shared.domain.services.railway_capacity_service import RailwayCapacityService
from shared.domain.services.rake_registry import RakeRegistry
from shared.domain.value_objects.rake_type import RakeType
from shared.infrastructure.simulation.coordination.simulation_infrastructure import SimulationInfrastructure


class YardOperationsContext:  # pylint: disable=too-many-instance-attributes
    """Yard Operations bounded context - application layer."""

    def __init__(self, infra: Any, rake_registry: RakeRegistry | None = None) -> None:
        self.yard = Yard(YardId('main_yard'))
        self.infra = infra

        # Domain services - pure business logic
        self.wagon_pickup_service = WagonPickupService()
        self.wagon_classification_service: WagonClassificationService
        self.workshop_batching_service: WorkshopBatchingService

        # Railway capacity service will be injected during initialization
        self.hump_yard_service: HumpYardService | None = None
        self.railway_capacity_service: RailwayCapacityService | None = None
        # Remove local yard_config as we'll use railway infrastructure
        self.yard_config: YardConfiguration | None = None
        self.scenario: SimulationInfrastructure | None = None
        self.wagons: list[Any] = []
        self.rejected_wagons: list[Any] = []
        self.train_processed_event = None
        # Track wagons managed through Railway Context only - no local tracking
        # Rake services

        self.rake_registry = rake_registry or RakeRegistry()
        # Track wagons waiting at retrofit track for each workshop
        self._waiting_at_retrofit: dict[str, list[Any]] = {}
        # Get railway infrastructure context for capacity management
        self.railway_context: Any = None  # Set in initialize() - always called before other methods
        # Step-specific planners
        self.collection_to_retrofit_planner: CollectionToRetrofitPlanner
        self.retrofit_to_workshop_planner: RetrofitToWorkshopPlanner
        self.workshop_to_retrofitted_planner: WorkshopToRetrofittedPlanner
        self.retrofitted_to_parking_planner: RetrofittedToParkingPlanner
        self.all_wagons: list[Wagon] = []
        self._retrofitted_accumulator: list[Wagon] = []

    def initialize(self, infrastructure: Any, scenario: Any) -> None:
        """Initialize with infrastructure and scenario."""
        self.infra = infrastructure
        self.scenario = scenario
        self.train_processed_event = self.infra.engine.create_event()

        # Get railway infrastructure context for capacity management
        self.railway_context = self.infra.contexts['railway']
        self.railway_capacity_service = RailwayCapacityService(self.railway_context)  # type: ignore[arg-type]

        # Initialize hump yard service with railway capacity service
        self.hump_yard_service = HumpYardService(self.railway_capacity_service)  # type: ignore[arg-type]

        # Initialize domain services
        self.wagon_classification_service = WagonClassificationService(self.hump_yard_service)
        self.workshop_batching_service = WorkshopBatchingService()

        # Initialize step-specific planners
        self.collection_to_retrofit_planner = CollectionToRetrofitPlanner(self.railway_context)
        self.retrofit_to_workshop_planner = RetrofitToWorkshopPlanner(self.railway_context)
        self.workshop_to_retrofitted_planner = WorkshopToRetrofittedPlanner(self.railway_context)
        self.retrofitted_to_parking_planner = RetrofittedToParkingPlanner(self.railway_context)

        # Initialize yard configuration using railway infrastructure capacity
        track_selection_service = self.railway_context.get_track_selection_service()
        collection_tracks = track_selection_service.get_tracks_by_type('collection')
        if not collection_tracks:
            raise RuntimeError('CONFIGURATION ERROR: No collection tracks found in scenario')

        collection_capacity = self.railway_context.get_track_capacity(collection_tracks[0].id)
        if collection_capacity <= 0:
            raise RuntimeError(f'CONFIGURATION ERROR: Collection track {collection_tracks[0].id} has no capacity')

        # Get all collection track IDs
        collection_track_ids = track_selection_service.get_track_ids_by_type('collection')

        self.yard_config = YardConfiguration(
            yard_id='main_yard',
            yard_type=YardType.HUMP_YARD,
            has_hump=True,
            classification_tracks=collection_track_ids,
            collection_track_capacity=collection_capacity,
            current_collection_count=0,
        )

        # Track occupancy managed by Railway Context - no local initialization needed

    def start_processes(self) -> None:
        """Start yard operation processes."""
        # Subscribe to events
        self.infra.event_bus.subscribe(TrainArrivedEvent, self._handle_train_arrived)
        self.infra.event_bus.subscribe(WagonRetrofitCompletedEvent, self._handle_wagon_retrofit_completed)
        self.infra.event_bus.subscribe(WagonsReadyForPickupEvent, self._handle_wagons_ready_for_pickup)

        self.infra.engine.schedule_process(self._trigger_initial_movement())  # For test compatibility

        # Subscribe to wagon classification events for rake formation
        self.infra.event_bus.subscribe(WagonsClassifiedEvent, self._handle_wagons_classified_for_rakes)
        # Subscribe to rake transport events
        self.infra.event_bus.subscribe(RakeTransportRequestedEvent, self._handle_rake_transport_request)

    def _handle_wagons_ready_for_pickup(self, event: WagonsReadyForPickupEvent) -> None:
        """Handle wagons ready for pickup event."""
        self.infra.engine.schedule_process(self._pickup_wagons_from_track(event.track_id))

    def _get_wagons_on_track(self, track_id: str) -> list[Any]:
        """Get wagons currently on track from railway context."""
        occupancy_repo = self.railway_context.get_occupancy_repository()  # type: ignore[attr-defined]
        track_occupancy = occupancy_repo.get(track_id)
        if not track_occupancy:
            return []

        # Extract wagon objects from occupants
        wagons = []
        for occupant in track_occupancy.get_occupants():
            if occupant.type.value == 'wagon':
                # Find wagon object by ID in all_wagons
                for wagon in self.all_wagons:
                    if wagon.id == occupant.id:
                        wagons.append(wagon)
                        break
        return wagons

    def _add_wagons_to_track(self, wagons: list[Any], track_id: str) -> tuple[list[Any], list[Any]]:
        """Add wagons to track via railway context. Returns (accepted, rejected) wagons."""
        occupancy_repo = self.railway_context.get_occupancy_repository()  # type: ignore[attr-defined]
        track = self.railway_context.get_track(track_id)  # type: ignore[attr-defined]
        if not track:
            return [], wagons

        track_occupancy = occupancy_repo.get_or_create(track)
        current_time = self.infra.engine.current_time()

        accepted_wagons = []
        rejected_wagons = []

        for wagon in wagons:
            wagon_length = wagon.length
            optimal_position = track_occupancy.find_optimal_position(wagon_length)

            if optimal_position is None:
                # Track is full - reject this wagon
                wagon.status = WagonStatus.REJECTED
                wagon.rejection_reason = f'{track_id}_FULL'
                wagon.detailed_rejection_reason = f'Track {track_id} has no space for wagon {wagon.id}'
                rejected_wagons.append(wagon)
                continue

            occupant = TrackOccupant(
                id=wagon.id,
                type=OccupantType.WAGON,
                length=wagon_length,
                position_start=optimal_position,
            )
            track_occupancy.add_occupant(occupant, current_time)
            accepted_wagons.append(wagon)

        return accepted_wagons, rejected_wagons

    def _remove_wagons_from_track(self, wagon_ids: list[str], track_id: str) -> None:
        """Remove wagons from track via railway context."""
        occupancy_repo = self.railway_context.get_occupancy_repository()  # type: ignore[attr-defined]
        track_occupancy = occupancy_repo.get(track_id)
        if track_occupancy:
            current_time = self.infra.engine.current_time()
            for wagon_id in wagon_ids:
                track_occupancy.remove_occupant(wagon_id, current_time)

    def _pickup_wagons_from_track(self, track_id: str) -> Generator[Any, Any]:
        """Process for picking up wagons from a specific collection track."""
        current_time = self.infra.engine.current_time()
        wagons_to_pickup = self._get_wagons_on_track(track_id)

        if not wagons_to_pickup:
            return

        # Log pickup from collection track
        try:
            plog = get_process_logger()
            wagon_id_list = ', '.join([w.id for w in wagons_to_pickup])
            plog.log(f'PICKUP: {len(wagons_to_pickup)} wagons from {track_id} [{wagon_id_list}]', sim_time=current_time)

        except RuntimeError:
            pass

        # Use step-specific planner for capacity-aware rake formation
        plan = self.collection_to_retrofit_planner.plan_transport(wagons_to_pickup, track_id)

        if not plan:
            try:
                plog = get_process_logger()
                plog.log(
                    f'NO CAPACITY: No retrofit track capacity available for {len(wagons_to_pickup)} wagons',
                    sim_time=current_time,
                )
            except RuntimeError:
                pass
            return

        # Execute transport plan (wagon moved events will be published by shunting context)
        yield from self._execute_transport_plan(plan)

        # Log capacity status after pickup
        if self.railway_capacity_service:
            self.railway_capacity_service.get_capacity_info(track_id)

        # Log remaining wagons on this collection track
        remaining_wagons = self._get_wagons_on_track(track_id)
        if remaining_wagons:
            try:
                plog = get_process_logger()
                current_time = self.infra.engine.current_time()
                plog.log(f'WAITING: {len(remaining_wagons)} wagons still on {track_id}', sim_time=current_time)
            except RuntimeError:
                pass

    def _execute_transport_plan(self, transport_plan: Any) -> Generator[Any, Any]:
        """Execute transport plan using capacity-validated rake."""
        # Form rake from transport plan
        rake = Rake(
            rake_id=f'transport_rake_{transport_plan.from_track}_{transport_plan.to_track}_{int(time.time())}',
            wagons=transport_plan.wagons,
            rake_type=RakeType.TRANSPORT_RAKE,
            formation_time=time.time(),
            formation_track=transport_plan.from_track,
            target_track=transport_plan.to_track,
        )
        rake.assign_to_wagons()
        self.rake_registry.register_rake(rake)

        # Publish rake formed event
        rake_event = RakeFormedEvent(rake=rake)
        self.infra.event_bus.publish(rake_event)

        # Request transport
        transport_event = RakeTransportRequestedEvent(
            rake_id=rake.rake_id,
            from_track=transport_plan.from_track,
            to_track=transport_plan.to_track,
            rake_type=rake.rake_type,
        )
        self.infra.event_bus.publish(transport_event)

        yield from self.infra.engine.delay(0.1)  # Small delay for processing

    def _handle_train_arrived(self, event: TrainArrivedEvent) -> None:
        """Handle train arrived event - start classification process."""
        self.infra.engine.current_time()

        # Store wagons for access
        self.all_wagons.extend(event.wagons)

        # Schedule classification process
        self.infra.engine.schedule_process(
            self._classify_train_wagons(
                event.wagons,
                event.train_id,
            )
        )  # type: ignore[func-returns-value]

    def _classify_train_wagons(self, wagons: list[Wagon], train_id: str) -> Generator:  # pylint: disable=too-many-locals,too-many-branches,too-many-statements,too-many-lines
        """Classify train wagons through hump yard with timing using domain service."""
        if not self.yard_config:
            raise RuntimeError('Yard configuration not initialized')

        # Calculate processing schedule using domain service
        process_times = self.scenario.process_times  # type: ignore[attr-defined, union-attr]
        schedule = self.hump_yard_service.calculate_processing_schedule(  # type: ignore[attr-defined, union-attr]
            len(wagons),
            process_times,
            self.yard_config,
        )

        # 1. Delay from train arrival to hump yard
        if schedule.train_to_hump_delay > 0:
            yield from self.infra.engine.delay(schedule.train_to_hump_delay)

        # 2. Select collection track using strategy and classify wagons
        selected_track = self._select_track_by_type('collection')
        collection_track_id = selected_track.id if selected_track else 'collection'

        # Use domain service for classification
        classification_result = self.wagon_classification_service.classify_train(
            wagons,
            train_id,
            self.yard_config,
            collection_track_id,  # type: ignore[arg-type]
        )
        # 3. Process each wagon with timing intervals
        for i, wagon in enumerate(classification_result.accepted_wagons):
            self.wagons.append(wagon)

            # Apply timing interval for this wagon
            if i < len(schedule.wagon_intervals) and schedule.wagon_intervals[i] > 0:
                yield from self.infra.engine.delay(schedule.wagon_intervals[i])

        # 4. Add all train wagons to the selected collection track via Railway Context
        if classification_result.accepted_wagons:
            final_accepted, track_rejected = self._add_wagons_to_track(
                classification_result.accepted_wagons, collection_track_id
            )

            # Update classification result with track capacity rejections
            classification_result.accepted_wagons = final_accepted
            classification_result.rejected_wagons.extend(track_rejected)

            # Publish event to trigger pickup process
            if final_accepted:
                pickup_event = WagonsReadyForPickupEvent(
                    track_id=collection_track_id,
                    wagon_count=len(final_accepted),
                    event_timestamp=self.infra.engine.current_time(),
                )
                self.infra.event_bus.publish(pickup_event)

        # 5. Update rejected wagons and log rejections
        if classification_result.rejected_wagons:
            try:
                plog = get_process_logger()
                current_time = self.infra.engine.current_time()
                for wagon in classification_result.rejected_wagons:
                    # Add train_id, rejection_time, and collection_track_id for export
                    wagon.train_id = train_id
                    wagon.rejection_time = current_time
                    wagon.collection_track_id = collection_track_id

                    reason = wagon.rejection_reason or ''
                    detailed_reason = wagon.detailed_rejection_reason

                    if '_FULL' in reason:
                        track_name = reason.replace('_FULL', '')
                        reason_text = f'{track_name} full'
                    elif detailed_reason:
                        reason_text = detailed_reason
                    else:
                        reason_text = 'Classification rejected'

                    plog.log(
                        f'REJECTED: Wagon {wagon.id} from {train_id} at {current_time:.1f}min - {reason_text}',
                        sim_time=current_time,
                    )
            except RuntimeError:
                pass
        self.rejected_wagons.extend(classification_result.rejected_wagons)

        # Log capacity status using railway infrastructure
        if self.railway_capacity_service:
            self.railway_capacity_service.get_capacity_info(collection_track_id)

        # 6. Publish classification complete event
        current_time = self.infra.engine.current_time()
        classification_event = WagonsClassifiedEvent(
            train_id=train_id,
            accepted_wagons=classification_result.accepted_wagons,
            rejected_wagons=classification_result.rejected_wagons,
        )
        self.infra.event_bus.publish(classification_event)

        # 7. Publish train departed event
        departure_event = TrainDepartedEvent(train_id=train_id, departure_time=current_time, wagon_count=len(wagons))
        self.infra.event_bus.publish(departure_event)

        # 8. Train processing complete

    def _handle_wagon_retrofit_completed(self, event: WagonRetrofitCompletedEvent) -> None:
        """Handle wagon retrofit completed event - batch wagons completing at same time.

        BATCHING LOGIC:
        ===============
        Problem: Multiple wagons may complete retrofit at SAME simulation time
        Solution: Accumulate all simultaneous completions into ONE batch

        FLOW:
        =====
        1. Wagon completes retrofit in workshop
        2. Add wagon to workshop_batching_service accumulator
        3. If FIRST wagon: Schedule batch creation with delay(0)
        4. If NOT first: Just accumulate, batch creation already scheduled
        5. After delay(0): ALL simultaneous completions accumulated
        6. Create batch with all accumulated wagons
        7. Transport batch: Workshop → Retrofitted → Parking

        WHY delay(0)?
        =============
        - Allows SimPy to process all events at current time
        - Ensures all wagons completing at t=15.0 are in same batch
        - Without delay: Only first wagon would be in batch

        EXAMPLE:
        ========
        t=15.0: W01 completes (is_first=True) → Schedule batch creation
        t=15.0: W02 completes (is_first=False) → Just accumulate
        t=15.0: [delay(0) expires]
        t=15.0: Create batch with [W01, W02]
        """
        # Find the wagon
        wagon = None
        for w in self.wagons:
            if w.id == event.wagon_id:
                wagon = w
                break

        if not wagon:
            return

        # Add to batch - returns True if this is the first wagon
        is_first = self.workshop_batching_service.add_completed_wagon(wagon, event.workshop_id)

        try:
            plog = get_process_logger()
            current_time = self.infra.engine.current_time()
            plog.log(
                f'RETROFIT_COMPLETE: Wagon {wagon.id} completed at {event.workshop_id}, is_first={is_first}',
                sim_time=current_time,
            )
        except RuntimeError:
            pass

        if is_first:
            # Schedule batch creation after delay to collect all simultaneous completions
            try:
                plog = get_process_logger()
                current_time = self.infra.engine.current_time()
                plog.log(
                    f'TASK_SCHEDULED: create_and_transport_batch for {event.workshop_id} at {current_time:.1f}min',
                    sim_time=current_time,
                )
            except RuntimeError:
                pass
            self.infra.engine.schedule_process(self._create_and_transport_batch(event.workshop_id))

    def _create_and_transport_batch(self, workshop_id: str) -> Generator[Any, Any]:
        """Create batch after delay and transport it."""
        # Delay to allow all simultaneous completions to be added
        yield from self.infra.engine.delay(0)

        # Now create the batch with all accumulated wagons
        batch = self.workshop_batching_service.create_batch(workshop_id)

        try:
            plog = get_process_logger()
            current_time = self.infra.engine.current_time()
            if batch:
                wagon_ids = [w.id for w in batch.wagons]
                plog.log(
                    f'BATCH_CREATED: {len(batch.wagons)} wagons {wagon_ids} from {workshop_id}', sim_time=current_time
                )
            else:
                plog.log(f'BATCH_EMPTY: No wagons to batch from {workshop_id}', sim_time=current_time)
        except RuntimeError:
            pass

        if batch:
            yield from self._transport_batch(batch)

    def _get_workshop_capacity_for_batching(self, workshop_id: str) -> int:
        """Get workshop capacity for determining batch size."""
        for workshop in self.scenario.workshops:  # type: ignore[attr-defined, union-attr]
            if workshop.id == workshop_id:
                return workshop.retrofit_stations  # type: ignore[no-any-return]
        return 0

    def _transport_batch(self, batch: Any) -> Generator[Any, Any]:
        """Transport batch using step planners."""
        # Small yield to ensure this is a generator
        yield from self.infra.engine.delay(0)

        try:
            plog = get_process_logger()
            current_time = self.infra.engine.current_time()
            wagon_ids = [w.id for w in batch.wagons]
            plog.log(
                f'TRANSPORT_BATCH: Starting transport of {len(batch.wagons)} wagons {wagon_ids} '
                f'from {batch.workshop_id}',
                sim_time=current_time,
            )
        except RuntimeError:
            pass

        # Use step planners for capacity-aware transport planning
        transport_plan = self.workshop_to_retrofitted_planner.plan_transport(batch.wagons, batch.workshop_id)

        if transport_plan:
            # Form rake using direct Rake construction
            rake = Rake(
                rake_id=f'transport_rake_{transport_plan.from_track}_{transport_plan.to_track}_{int(time.time())}',
                wagons=transport_plan.wagons,
                rake_type=RakeType.TRANSPORT_RAKE,
                formation_time=time.time(),
                formation_track=transport_plan.from_track,
                target_track=transport_plan.to_track,
            )
            rake.assign_to_wagons()
            self.rake_registry.register_rake(rake)

            # Publish rake formed event
            rake_event = RakeFormedEvent(rake=rake)
            self.infra.event_bus.publish(rake_event)

            # Request transport: workshop -> retrofitted -> parking
            transport_event = RakeTransportRequestedEvent(
                rake_id=rake.rake_id,
                from_track=transport_plan.from_track,
                to_track=transport_plan.to_track,
                rake_type=rake.rake_type,
            )
            self.infra.event_bus.publish(transport_event)

        # Check if there are wagons waiting on collection tracks
        collection_tracks = self.railway_context.get_track_selection_service().get_tracks_by_type('collection')
        for track in collection_tracks:
            wagons_on_track = self._get_wagons_on_track(track.id)
            if wagons_on_track:
                try:
                    plog = get_process_logger()
                    current_time = self.infra.engine.current_time()
                    wagon_ids = [w.id for w in wagons_on_track]
                    plog.log(
                        f'TRIGGER_PICKUP: Found {len(wagons_on_track)} wagons {wagon_ids} waiting on {track.id}',
                        sim_time=current_time,
                    )
                except RuntimeError:
                    pass
                pickup_event = WagonsReadyForPickupEvent(
                    track_id=track.id,
                    wagon_count=len(wagons_on_track),
                    event_timestamp=self.infra.engine.current_time(),
                )
                self.infra.event_bus.publish(pickup_event)
                break  # Only trigger one pickup at a time

    def _bring_next_batch_from_retrofit(self, wagons: list[Any], workshop_id: str) -> Generator[Any, Any]:
        """Bring next batch of wagons from retrofit track to workshop."""
        if not wagons:
            return

        try:
            plog = get_process_logger()
            current_time = self.infra.engine.current_time()
            wagon_ids = [w.id for w in wagons]
            plog.log(
                f'BRING_NEXT_BATCH: Transporting {len(wagons)} wagons {wagon_ids} to {workshop_id}',
                sim_time=current_time,
            )
        except RuntimeError:
            pass

        shunting_context = self.infra.shunting_context
        if not shunting_context:
            return

        yield from self._transport_wagon_batch_to_workshop(wagons, workshop_id, shunting_context)

    def _are_all_workshops_idle(self) -> bool:
        """Check if all workshops are idle (no wagons being retrofitted or waiting to be picked up)."""
        for wagon in self.all_wagons:
            if wagon.status == WagonStatus.RETROFITTING:
                return False

        workshop_ids = (
            [w.id for w in self.scenario.workshops] if self.scenario and hasattr(self.scenario, 'workshops') else []
        )
        for wagon in self.all_wagons:
            if wagon.status == WagonStatus.RETROFITTED and wagon.track in workshop_ids:
                return False

        return True

    def _transport_retrofitted_rake(self, rake: Any) -> Generator[Any, Any]:  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        """Transport retrofitted rake: workshop -> retrofitted -> parking."""
        try:
            shunting_context = self.infra.shunting_context
            if not shunting_context:
                return

            # Step 1: workshop -> retrofitted
            loco = yield from shunting_context.allocate_locomotive(self)
            try:
                # Select retrofitted track
                selected_retrofitted = self._select_track_by_type('retrofitted')
                retrofitted_track_id = selected_retrofitted.id if selected_retrofitted else 'retrofitted'

                yield from shunting_context.move_locomotive(self, loco, loco.current_track, rake.formation_track)
                yield from shunting_context.couple_wagons(self, rake.wagon_count, 'DAC')
                yield from shunting_context.move_locomotive(self, loco, rake.formation_track, retrofitted_track_id)
                yield from shunting_context.decouple_wagons(self, rake.wagon_count, 'DAC')

                # Update wagon locations and publish distributed events
                current_time = self.infra.engine.current_time()
                for wagon in rake.wagons:
                    old_track = wagon.track
                    wagon.move_to_track(retrofitted_track_id)

                    # Publish wagon moved event for track occupancy sync
                    moved_event = WagonMovedEvent(
                        wagon_id=wagon.id,
                        from_track=old_track,
                        to_track=retrofitted_track_id,
                        timestamp=current_time,
                        movement_type='shunting',
                    )
                    self.infra.event_bus.publish(moved_event)

                    # Release workshop resource after pickup
                    # TODO:  This is still the hack of the MVP.
                    if hasattr(wagon, '_workshop_resource') and hasattr(wagon, '_workshop_request'):  # pylint: disable=protected-access
                        wagon._workshop_resource.release(wagon._workshop_request)  # pylint: disable=protected-access
                        delattr(wagon, '_workshop_resource')
                        delattr(wagon, '_workshop_request')

                    distributed_event = WagonDistributedEvent(
                        wagon_id=wagon.id, workshop_id=retrofitted_track_id, batch_id=rake.rake_id
                    )
                    distributed_event.track_id = retrofitted_track_id  # type: ignore[assignment]
                    distributed_event.event_timestamp = current_time
                    self.infra.event_bus.publish(distributed_event)

                yield from shunting_context.move_locomotive(self, loco, retrofitted_track_id, loco.home_track)
                yield from shunting_context.release_locomotive(self, loco)
            except GeneratorExit:  # pylint: disable=try-except-raise
                raise

            self._retrofitted_accumulator.extend(rake.wagons)

            # MVP Logic: Always park wagons immediately when they arrive on retrofitted track
            wagons_to_park = self._retrofitted_accumulator[:]
            self._retrofitted_accumulator = []

            # Use step planner for retrofitted -> parking transport
            parking_plan = self.retrofitted_to_parking_planner.plan_transport(wagons_to_park, retrofitted_track_id)
            if not parking_plan:
                raise RuntimeError(
                    f'CAPACITY EXCEEDED: No parking tracks available. '
                    f'Yard layout cannot handle the wagon volume. '
                    f'{len(wagons_to_park)} wagons cannot be parked.'
                )

            parking_track_id = parking_plan.to_track

            loco2 = yield from shunting_context.allocate_locomotive(self)
            try:
                yield from shunting_context.move_locomotive(self, loco2, loco2.current_track, parking_plan.from_track)
                yield from shunting_context.couple_wagons(self, len(wagons_to_park), 'DAC')
                yield from shunting_context.move_locomotive(self, loco2, parking_plan.from_track, parking_track_id)
                yield from shunting_context.decouple_wagons(self, len(wagons_to_park), 'DAC')

                current_time = self.infra.engine.current_time()
                for wagon in wagons_to_park:
                    wagon.status = WagonStatus.PARKING
                    wagon.move_to_track(parking_track_id)
                    parked_event = WagonParkedEvent(wagon_id=wagon.id, parking_area_id=parking_track_id)
                    parked_event.event_timestamp = current_time
                    self.infra.event_bus.publish(parked_event)

                    # Publish wagon moved event for track occupancy sync
                    moved_event = WagonMovedEvent(
                        wagon_id=wagon.id,
                        from_track=retrofitted_track_id,
                        to_track=parking_track_id,
                        timestamp=current_time,
                        movement_type='shunting',
                    )
                    self.infra.event_bus.publish(moved_event)

                yield from shunting_context.move_locomotive(self, loco2, parking_track_id, loco2.home_track)

                # MVP Logic: Before releasing locomotive, check if all workshops are idle and schedule next batch
                # This ensures the task is scheduled with higher priority
                workshops_idle = self._are_all_workshops_idle()

                try:
                    plog = get_process_logger()
                    current_time = self.infra.engine.current_time()
                    plog.log(
                        f'WORKSHOP_STATUS: workshops_idle={workshops_idle} at {current_time:.1f}min',
                        sim_time=current_time,
                    )
                except RuntimeError:
                    pass

                if workshops_idle:
                    workshop_id = rake.formation_track
                    if self._waiting_at_retrofit.get(workshop_id):
                        workshop_capacity = self._get_workshop_capacity_for_batching(workshop_id)
                        waiting_count = len(self._waiting_at_retrofit[workshop_id])
                        next_batch_size = min(workshop_capacity, waiting_count)
                        next_batch = self._waiting_at_retrofit[workshop_id][:next_batch_size]
                        self._waiting_at_retrofit[workshop_id] = self._waiting_at_retrofit[workshop_id][
                            next_batch_size:
                        ]

                        try:
                            plog = get_process_logger()
                            current_time = self.infra.engine.current_time()
                            wagon_ids = [w.id for w in next_batch]
                            plog.log(
                                f'TASK_SCHEDULED: bring_next_batch for {workshop_id} - '
                                f'{len(next_batch)} wagons {wagon_ids} at {current_time:.1f}min',
                                sim_time=current_time,
                            )
                        except RuntimeError:
                            pass

                        # Schedule immediately - all workshops are idle, this has priority
                        self.infra.engine.schedule_process(
                            self._bring_next_batch_from_retrofit(next_batch, workshop_id)
                        )
            finally:
                yield from shunting_context.release_locomotive(self, loco2)
        except GeneratorExit:  # pylint: disable=try-except-raise
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get yard operations metrics."""
        track_util = self._calculate_track_utilization()

        # Count wagons by status
        wagons_on_retrofitted = sum(1 for w in self.wagons if w.status == WagonStatus.RETROFITTED)
        wagons_on_retrofit = sum(1 for w in self.wagons if w.status == WagonStatus.TO_BE_RETROFFITED)
        wagons_on_collection = sum(1 for w in self.wagons if w.status == WagonStatus.TO_BE_RETROFFITED)
        wagons_parked = sum(1 for w in self.wagons if w.status == WagonStatus.PARKING)

        return {
            'classified_wagons': len(self.wagons),
            'rejected_wagons': len(self.rejected_wagons),
            'parking_areas': 1,
            'total_rakes_formed': len(self.rake_registry.get_all_rakes()),
            'track_utilization': track_util,
            'wagons_on_retrofitted': wagons_on_retrofitted,
            'wagons_on_retrofit': wagons_on_retrofit,
            'wagons_parked': wagons_parked,
            'wagons_on_collection': wagons_on_collection,
        }

    def _calculate_track_utilization(self) -> dict[str, float]:
        """Calculate track utilization based on wagon occupancy."""
        if not self.infra or not hasattr(self, 'scenario'):
            return {}

        total_time = self.infra.engine.current_time()
        if total_time == 0:
            return {}

        track_util = {}

        # Calculate utilization for collection tracks using Railway Context
        collection_tracks = self.railway_context.get_track_selection_service().get_tracks_by_type('collection')
        for track in collection_tracks:
            available_capacity = self.railway_context.get_available_capacity(track.id)  # type: ignore[attr-defined]
            total_capacity = self.railway_context.get_total_capacity(track.id)  # type: ignore[attr-defined]
            if total_capacity > 0:
                utilization = ((total_capacity - available_capacity) / total_capacity) * 100.0
                track_util[track.id] = utilization

        return track_util

    def _handle_wagons_classified_for_rakes(self, event: WagonsClassifiedEvent) -> None:
        """Handle wagons classified event by forming workshop rakes.

        Note
        ----
            Rakes are now formed in _pickup_wagons_to_retrofit for better timing
        """

    def _handle_rake_transport_request(self, event: RakeTransportRequestedEvent) -> None:
        """Handle rake transport request by scheduling shunting operations."""
        # Get rake from registry
        rake = self.rake_registry.get_rake(event.rake_id)
        if not rake:
            return

        # Route based on rake type and destination
        # Check if destination is a retrofitted track (by type, not hardcoded name)
        is_retrofitted_destination = False
        if event.to_track:
            retrofitted_tracks = self.railway_context.get_track_selection_service().get_tracks_by_type('retrofitted')
            for track in retrofitted_tracks:
                if track.id == event.to_track:
                    is_retrofitted_destination = True
                    break
            # Also check hardcoded name for backward compatibility
            if event.to_track == 'retrofitted':
                is_retrofitted_destination = True

        if is_retrofitted_destination:
            # Retrofitted rake: workshop -> retrofitted -> parking
            self.infra.engine.schedule_process(self._transport_retrofitted_rake(rake))
        else:
            # Workshop rake: collection -> retrofit -> workshop
            self.infra.engine.schedule_process(self._transport_rake_to_workshop(rake))

    def _transport_rake_to_workshop(self, rake: Any) -> Generator[Any, Any]:
        """Transport rake following professional process: collection → retrofit → workshop.

        PROCESS FLOW:
        =============
        STEP 1: COLLECTION → RETROFIT (All wagons together)
            - Allocate locomotive from pool
            - Move locomotive to collection track
            - Couple ALL wagons with screw couplers
            - Transport entire rake to retrofit staging track
            - Decouple all wagons
            - Release locomotive back to pool
            - Publish wagon moved events for track occupancy

        STEP 2: ASSIGN WORKSHOPS (Sequential block distribution)
            - Get workshop capacities from scenario config
            - Assign wagons in SEQUENTIAL BLOCKS by capacity:
              Example: 6 wagons, 2 workshops (WS1=2, WS2=2)
                * W01, W02 → WS1
                * W03, W04 → WS2
                * W05, W06 → WS1 (overflow)

        STEP 3: STORE WAITING WAGONS (Before transporting first batch)
            - For each workshop:
              * Split wagons into first_batch (up to capacity)
              * Store remaining wagons in _waiting_at_retrofit[workshop_id]
            - This ensures wagons are queued BEFORE any transport starts

        STEP 4: TRANSPORT FIRST BATCHES (One batch per workshop)
            - For each workshop:
              * Transport only the FIRST BATCH (up to capacity)
              * Remaining wagons stay on retrofit track
              * Will be picked up when workshop becomes idle

        WORKSHOP IDLE DETECTION:
        ========================
        - Happens in _transport_retrofitted_rake() after parking
        - Checks _are_all_workshops_idle()
        - If idle AND wagons waiting: schedules bring_next_batch

        WAGON DISTRIBUTION STRATEGY:
        ===========================
        - NOT round-robin (W01→WS1, W02→WS2, W03→WS1...)
        - SEQUENTIAL BLOCKS (W01,W02→WS1, W03,W04→WS2...)
        - Matches physical wagon order on track
        """
        try:
            shunting_context = self.infra.shunting_context
            if not shunting_context:
                return

            # Step 1: Move ALL wagons from collection to retrofit staging track
            loco = yield from shunting_context.allocate_locomotive(self)
            try:
                yield from shunting_context.move_locomotive(self, loco, loco.current_track, rake.formation_track)
                yield from shunting_context.couple_wagons(self, rake.wagon_count, 'SCREW', [])
                yield from shunting_context.move_locomotive(self, loco, rake.formation_track, rake.target_track)
                yield from shunting_context.decouple_wagons(self, rake.wagon_count, 'SCREW')

                # Publish wagon moved events after transport completes
                current_time = self.infra.engine.current_time()

                for wagon in rake.wagons:
                    moved_event = WagonMovedEvent(
                        wagon_id=wagon.id,
                        from_track=rake.formation_track,
                        to_track=rake.target_track,
                        timestamp=current_time,
                        movement_type='shunting',
                    )
                    self.infra.event_bus.publish(moved_event)

                yield from shunting_context.move_locomotive(self, loco, rake.target_track, loco.home_track)
            finally:
                yield from shunting_context.release_locomotive(self, loco)

            # Step 2: Transport FIRST batch only from retrofit to workshops in SEQUENCE order
            # Remaining wagons stay on retrofit track and are picked up when workshop capacity frees

            # Get workshop capacities using scenario workshops (not track IDs)
            scenario_workshop_ids = (
                [w.id for w in self.scenario.workshops]
                if self.scenario and hasattr(self.scenario, 'workshops')
                else ['WS1']
            )
            workshop_capacities = {
                ws_id: self._get_workshop_capacity_for_batching(ws_id) for ws_id in scenario_workshop_ids
            }

            # Distribute wagons using workshop-specific strategy
            strategy = self.scenario.workshop_selection_strategy  # type: ignore[union-attr]
            if hasattr(strategy, 'value'):
                strategy = strategy.value

            # Assign workshops to wagons in sequential blocks by capacity
            wagon_index = 0
            for workshop_id in scenario_workshop_ids:
                capacity = workshop_capacities[workshop_id]
                for _ in range(capacity):
                    if wagon_index < len(rake.wagons):
                        rake.wagons[wagon_index].workshop_id = workshop_id
                        wagon_index += 1

            # Handle any remaining wagons (if total wagons > total capacity)
            while wagon_index < len(rake.wagons):
                # Assign to first workshop for overflow
                rake.wagons[wagon_index].workshop_id = scenario_workshop_ids[0]
                wagon_index += 1

            # Group wagons by assigned workshop
            workshop_batches: dict[str, list[Wagon]] = {ws_id: [] for ws_id in scenario_workshop_ids}
            for wagon in rake.wagons:
                workshop_batches[wagon.workshop_id].append(wagon)

            # Store remaining wagons in waiting list BEFORE transporting first batch
            for workshop_id in scenario_workshop_ids:
                batch_wagons = workshop_batches[workshop_id]
                if not batch_wagons:
                    continue

                batch_size = workshop_capacities[workshop_id]
                first_batch = batch_wagons[:batch_size]
                remaining = batch_wagons[batch_size:]

                try:
                    plog = get_process_logger()
                    current_time = self.infra.engine.current_time()
                    first_ids = [w.id for w in first_batch]
                    plog.log(
                        f'BATCH_SPLIT: {workshop_id} - first_batch={len(first_batch)} {first_ids}, '
                        f'remaining={len(remaining)}',
                        sim_time=current_time,
                    )
                except RuntimeError:
                    pass

                # Store remaining wagons for this workshop FIRST
                if remaining:
                    if workshop_id not in self._waiting_at_retrofit:
                        self._waiting_at_retrofit[workshop_id] = []
                    self._waiting_at_retrofit[workshop_id].extend(remaining)

                    try:
                        plog = get_process_logger()
                        current_time = self.infra.engine.current_time()
                        wagon_ids = [w.id for w in remaining]
                        plog.log(
                            f'STORE_WAITING: Stored {len(remaining)} wagons {wagon_ids} for {workshop_id}',
                            sim_time=current_time,
                        )
                    except RuntimeError:
                        pass

            # Transport first batch to each workshop
            for workshop_id in scenario_workshop_ids:
                batch_wagons = workshop_batches[workshop_id]
                if not batch_wagons:
                    continue

                batch_size = workshop_capacities[workshop_id]
                first_batch = batch_wagons[:batch_size]

                try:
                    plog = get_process_logger()
                    current_time = self.infra.engine.current_time()
                    wagon_ids = [w.id for w in first_batch]
                    plog.log(
                        f'TRANSPORT_FIRST_BATCH: {len(first_batch)} wagons {wagon_ids} to {workshop_id}',
                        sim_time=current_time,
                    )
                except RuntimeError:
                    pass

                # Transport first batch
                yield from self._transport_wagon_batch_to_workshop(first_batch, workshop_id, shunting_context)
        except GeneratorExit:  # pylint: disable=try-except-raise
            return

    def _transport_wagon_batch_to_workshop(
        self, wagons: list[Any], workshop_id: str, shunting_context: Any
    ) -> Generator[Any, Any]:
        """Transport a batch of wagons from retrofit to workshop using step planner."""
        try:
            plog = get_process_logger()
            current_time = self.infra.engine.current_time()
            wagon_ids = [w.id for w in wagons]
            plog.log(f'TRANSPORT_TO_WORKSHOP: {len(wagons)} wagons {wagon_ids} to {workshop_id}', sim_time=current_time)
        except RuntimeError:
            pass

        # Use step planner for capacity-aware transport planning
        transport_plan = self.retrofit_to_workshop_planner.plan_transport(wagons, 'retrofit')

        if not transport_plan:
            try:
                plog = get_process_logger()
                current_time = self.infra.engine.current_time()
                plog.log(
                    f'TRANSPORT_FAILED: No transport plan for {len(wagons)} wagons to {workshop_id}',
                    sim_time=current_time,
                )
            except RuntimeError:
                pass
            return

        loco = yield from shunting_context.allocate_locomotive(self)
        try:
            yield from shunting_context.move_locomotive(self, loco, loco.current_track, transport_plan.from_track)
            wagon_ids = [w.id for w in wagons]
            yield from shunting_context.couple_wagons(self, len(wagons), 'SCREW', wagon_ids)
            yield from shunting_context.move_locomotive(self, loco, transport_plan.from_track, workshop_id, wagon_ids)
            yield from shunting_context.decouple_wagons(self, len(wagons), 'SCREW', wagon_ids)

            # Publish wagon moved events and ready events
            current_time = self.infra.engine.current_time()

            for wagon in wagons:
                old_track = wagon.track
                wagon.workshop_id = workshop_id
                wagon.move_to_track(workshop_id)

                try:
                    plog = get_process_logger()
                    plog.log(
                        f'WAGON_STATE: {wagon.id} moved {old_track} → {workshop_id}, status={wagon.status.value}',
                        sim_time=current_time,
                    )
                except RuntimeError:
                    pass

                # Publish wagon moved event for track occupancy sync
                moved_event = WagonMovedEvent(
                    wagon_id=wagon.id,
                    from_track=old_track,
                    to_track=workshop_id,
                    timestamp=current_time,
                    movement_type='shunting',
                )
                self.infra.event_bus.publish(moved_event)

                event = WagonReadyForRetrofitEvent(wagon=wagon, workshop_id=workshop_id)
                self.infra.event_bus.publish(event)

            yield from shunting_context.move_locomotive(self, loco, workshop_id, loco.home_track)
        finally:
            yield from shunting_context.release_locomotive(self, loco)

    def _select_track_by_type(self, track_type: str, strategy: str | None = None) -> Any | None:
        """Select track by type using railway context's track selection service."""
        # Use scenario strategy if not specified
        if strategy is None:
            if track_type == 'parking':
                strategy = self.scenario.parking_selection_strategy  # type: ignore[union-attr]
            else:
                strategy = self.scenario.track_selection_strategy  # type: ignore[union-attr]
            if hasattr(strategy, 'value'):
                strategy = strategy.value

        # Map string strategy to enum
        strategy_mapping = {
            'round_robin': SelectionStrategy.ROUND_ROBIN,
            'least_occupied': SelectionStrategy.LEAST_OCCUPIED,
            'most_available': SelectionStrategy.MOST_AVAILABLE,
        }
        strategy_enum = strategy_mapping[strategy]

        # Use railway context's track selection service (centralized implementation)
        return self.railway_context.get_track_selection_service().select_track(track_type, strategy_enum)

    def _trigger_initial_movement(self) -> Any:
        """Trigger initial locomotive movement for test compatibility."""
        yield from self.infra.engine.delay(0)

    def get_status(self) -> dict[str, Any]:
        """Get status."""
        return {'status': 'ready'}

    def cleanup(self) -> None:
        """Cleanup."""

    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed."""
