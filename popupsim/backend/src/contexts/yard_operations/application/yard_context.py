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
# ruff: noqa: C901, PLR0911, PLR0912, PLR0915
# TODO: Refactoring is needed here. This is just for the MVP to get it running

from collections.abc import Generator
from typing import Any

from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
from contexts.yard_operations.domain.aggregates.yard import Yard
from contexts.yard_operations.domain.events.yard_events import WagonDistributedEvent
from contexts.yard_operations.domain.events.yard_events import WagonParkedEvent
from contexts.yard_operations.domain.services.hump_yard_service import HumpYardService
from contexts.yard_operations.domain.services.hump_yard_service import YardConfiguration
from contexts.yard_operations.domain.services.hump_yard_service import YardType
from contexts.yard_operations.domain.services.wagon_distribution_service import WagonDistributionService
from contexts.yard_operations.domain.services.wagon_pickup_service import WagonPickupService
from contexts.yard_operations.domain.value_objects.yard_id import YardId
from infrastructure.logging import get_process_logger
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
from shared.domain.services.railway_capacity_service import RailwayCapacityService
from shared.domain.services.rake_formation_service import RakeFormationService
from shared.domain.services.rake_registry import RakeRegistry
from shared.infrastructure.simulation.coordination.simulation_infrastructure import SimulationInfrastructure


class YardOperationsContext:  # pylint: disable=too-many-instance-attributes
    """Yard Operations bounded context - application layer."""

    def __init__(self, infra: Any, rake_registry: RakeRegistry | None = None) -> None:
        self.yard = Yard(YardId('main_yard'))
        self.infra = infra
        self.distribution_service = WagonDistributionService()
        # Domain services - pure business logic
        self.wagon_pickup_service = WagonPickupService()
        # Railway capacity service will be injected during initialization
        self.hump_yard_service: HumpYardService | None = None
        self.railway_capacity_service: RailwayCapacityService | None = None
        # Remove local yard_config as we'll use railway infrastructure
        self.yard_config: YardConfiguration | None = None
        self.scenario: SimulationInfrastructure | None = None
        self.wagons: list[Any] = []
        self.rejected_wagons: list[Any] = []
        self.train_processed_event = None
        # Track wagon lists - managed through Railway Context
        self._track_wagons: dict[str, list[Any]] = {}
        # Rake services
        self._rake_formation_service = RakeFormationService()
        self.rake_registry = rake_registry or RakeRegistry()
        self._event_handlers: list = []
        # Batch tracking for retrofitted wagons
        self._retrofitted_batches: dict[str, list[Any]] = {}
        # Track wagons waiting at retrofit track for each workshop
        self._waiting_at_retrofit: dict[str, list[Any]] = {}
        # Track pending transport checks to avoid duplicate transports
        self._pending_transport_checks: dict[str, bool] = {}
        # Build track index by type and initialize selectors
        self._tracks_by_type: dict[str, list[Any]] = {}
        self._track_selectors: dict[str, Any] = {}
        self._round_robin_index: dict[str, int] = {}
        # Get railway infrastructure context for capacity management

        self.railway_context = None  # Set in initialize() - always called before other methods
        self.railway_capacity_service = None  # Set in initialize() - always called before other methods
        self._expected_wagon_count = 0
        self.all_wagons: list[Wagon] = []
        self._retrofitted_accumulator: list[Wagon] = []
        self._track_occupancy_m: dict[str, float] = {}
        self._workshop_round_robin_index: int = 0
        self._workshop_wagon_counts: dict[str, int] = {}

    def initialize(self, infrastructure: Any, scenario: Any) -> None:
        """Initialize with infrastructure and scenario."""
        self.infra = infrastructure
        self.scenario = scenario
        self.train_processed_event = self.infra.engine.create_event()

        if scenario and hasattr(scenario, 'tracks') and scenario.tracks:
            for track in scenario.tracks:
                track_type = getattr(track, 'type', 'unknown')
                if track_type not in self._tracks_by_type:
                    self._tracks_by_type[track_type] = []
                    self._round_robin_index[track_type] = 0
                self._tracks_by_type[track_type].append(track)

        # Get railway infrastructure context for capacity management
        # railway_context = getattr(self.infra, 'contexts', {}).get('railway')
        self.railway_context = self.infra.contexts['railway']
        self.railway_capacity_service = RailwayCapacityService(self.railway_context)  # type: ignore[arg-type]

        # Initialize hump yard service with railway capacity service
        self.hump_yard_service = HumpYardService(self.railway_capacity_service)  # type: ignore[arg-type]

        # Initialize yard configuration using railway infrastructure capacity
        # Get collection track capacity from railway infrastructure
        collection_capacity = 50  # Default
        collection_tracks = self._tracks_by_type.get('collection', [])
        if self.railway_context and collection_tracks:
            collection_capacity = self.railway_context.get_track_capacity(collection_tracks[0].id)
            if collection_capacity == 0:  # Track not found, use default
                collection_capacity = 50

        # Get all collection track IDs
        collection_track_ids = [t.id for t in self._tracks_by_type.get('collection', [])]

        self.yard_config = YardConfiguration(
            yard_id='main_yard',
            yard_type=YardType.HUMP_YARD,
            has_hump=True,
            classification_tracks=collection_track_ids if collection_track_ids else ['collection'],
            collection_track_capacity=collection_capacity,
            current_collection_count=0,
        )

        # Initialize track wagon lists
        for track_type in ['collection', 'retrofit', 'retrofitted']:
            tracks = self._tracks_by_type.get(track_type, [])
            if tracks:
                for track in tracks:
                    self._track_wagons[track.id] = []
            else:
                # Create default track for backward compatibility
                self._track_wagons[track_type] = []

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

    def _pickup_wagons_from_track(self, track_id: str) -> Generator[Any, Any]:
        """Process for picking up wagons from a specific collection track."""
        current_time = self.infra.engine.current_time()
        wagons_to_pickup = self._track_wagons.get(track_id, [])

        if not wagons_to_pickup:
            return

        # Clear wagons from track and update Railway Context
        self._track_wagons[track_id] = []
        occupancy_repo = self.railway_context.get_occupancy_repository()  # type: ignore[attr-defined]
        for wagon in wagons_to_pickup:
            track_occupancy = occupancy_repo.get(track_id)
            if track_occupancy:
                track_occupancy.remove_occupant(wagon.id, self.infra.engine.current_time())

        yield from self.infra.engine.delay(0.1)  # Small processing delay

        # Log pickup from collection track
        try:
            plog = get_process_logger()
            wagon_ids = ', '.join([w.id for w in wagons_to_pickup])
            plog.log(f'PICKUP: {len(wagons_to_pickup)} wagons from {track_id} [{wagon_ids}]', sim_time=current_time)

        except RuntimeError:
            pass

        # Use domain service to create pickup plan.
        # TODO: Fix is needed. It is using the workshop capacity but should use retrofit track

        # Utterly bullshit here!
        workshop_capacities = self._get_workshop_capacities()
        pickup_plan = self.wagon_pickup_service.create_pickup_plan(wagons_to_pickup, workshop_capacities)

        # Validate pickup feasibility
        available_locomotives = self._get_available_locomotive_count()
        is_feasible, _issues = self.wagon_pickup_service.validate_pickup_feasibility(pickup_plan, available_locomotives)

        if not is_feasible:
            return

        pickup_plan.wagons = wagons_to_pickup  # type: ignore[attr-defined]

        # Execute pickup plan using application service
        yield from self._execute_pickup_plan(pickup_plan, track_id)

        # Log capacity status after pickup
        if self.railway_capacity_service:
            self.railway_capacity_service.get_capacity_info(track_id)

        # Log remaining wagons on this collection track
        remaining_count = len(self._track_wagons.get(track_id, []))
        if remaining_count > 0:
            try:
                plog = get_process_logger()
                current_time = self.infra.engine.current_time()
                plog.log(f'WAITING: {remaining_count} wagons still on {track_id}', sim_time=current_time)
            except RuntimeError:
                pass

    def _group_wagons_by_retrofit_track(self, wagons: list[Any]) -> dict[str, list[Any]]:
        """Group wagons by their assigned retrofit track."""
        # Simple grouping - all wagons go to first retrofit track
        if not wagons:
            return {}
        return {'retrofit_track_1': wagons}

    def _distribute_wagons_to_workshops(self, wagons: list[Any]) -> Generator[Any, Any]:
        """Distribute wagons to workshops based on available capacity."""
        workshop_ids = getattr(self.infra, 'workshop_ids', ['workshop_1'])

        # Simple distribution - alternate between workshops
        for i, wagon in enumerate(wagons):
            workshop_id = workshop_ids[i % len(workshop_ids)]
            wagon.status = 'READY_FOR_RETROFIT'

            # Signal workshop via event bus
            event = WagonReadyForRetrofitEvent(wagon=wagon, workshop_id=workshop_id)
            self.infra.event_bus.publish(event)

            yield from self.infra.engine.delay(0.1)  # Small delay between distributions

    def _handle_train_arrived(self, event: TrainArrivedEvent) -> None:
        """Handle train arrived event - start classification process."""
        self.infra.engine.current_time()

        # Store wagons for access
        self.all_wagons.extend(event.wagons)

        # Set expected wagon count for this train
        self._expected_wagon_count = len(event.wagons)

        # Schedule classification process
        self.infra.engine.schedule_process(
            self._classify_train_wagons(
                event.wagons,
                event.train_id,
            )
        )  # type: ignore[func-returns-value]

    def _classify_train_wagons(self, wagons: list[Wagon], train_id: str) -> Generator:  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Classify train wagons through hump yard with timing using domain service."""
        # Calculate processing schedule using domain service
        process_times = self.scenario.process_times  # type: ignore[attr-defined, union-attr]
        schedule = self.hump_yard_service.calculate_processing_schedule(  # type: ignore[attr-defined, union-attr]
            len(wagons),
            process_times,
        )

        # 1. Delay from train arrival to hump yard
        if schedule.train_to_hump_delay > 0:
            yield from self.infra.engine.delay(schedule.train_to_hump_delay)

        # 2. Select collection track using strategy and classify wagons
        selected_track = self._select_track_by_type('collection')
        collection_track_id = selected_track.id if selected_track else 'collection'

        classification_result = self.hump_yard_service.classify_wagons(  # type: ignore[attr-defined, union-attr]
            wagons,
            self.yard_config,
            collection_track_id,
        )
        # 3. Process each wagon with timing intervals
        for i, wagon in enumerate(classification_result.accepted_wagons):
            self.wagons.append(wagon)

            # Apply timing interval for this wagon
            if i < len(schedule.wagon_intervals) and schedule.wagon_intervals[i] > 0:
                yield from self.infra.engine.delay(schedule.wagon_intervals[i])

        # 4. Add all train wagons to the selected collection track via Railway Context
        if classification_result.accepted_wagons:
            occupancy_repo = self.railway_context.get_occupancy_repository()  # type: ignore[attr-defined]
            for wagon in classification_result.accepted_wagons:
                # Add to track wagon list
                if collection_track_id not in self._track_wagons:
                    self._track_wagons[collection_track_id] = []
                self._track_wagons[collection_track_id].append(wagon)

                # Update Railway Context occupancy using proper aggregate pattern
                wagon_length = getattr(wagon, 'length', 15.0)
                track = self.railway_context.get_track(collection_track_id)  # type: ignore[attr-defined]
                if track:
                    track_occupancy = occupancy_repo.get_or_create(track)

                    # Check if track can accommodate the wagon
                    optimal_position = track_occupancy.find_optimal_position(wagon_length)
                    if optimal_position is None:
                        # Track is full - reject this wagon with specific track name
                        wagon.status = 'REJECTED'
                        wagon.rejection_reason = f'{collection_track_id}_FULL'
                        wagon.detailed_rejection_reason = (
                            f'Collection track {collection_track_id} has no space for wagon {wagon.id}'
                        )
                        classification_result.rejected_wagons.append(wagon)
                        classification_result.accepted_wagons.remove(wagon)
                        continue

                    occupant = TrackOccupant(
                        id=wagon.id,
                        type=OccupantType.WAGON,
                        length=wagon_length,
                        position_start=optimal_position,
                    )
                    track_occupancy.add_occupant(occupant, self.infra.engine.current_time())

            # Publish event to trigger pickup process
            pickup_event = WagonsReadyForPickupEvent(
                track_id=collection_track_id,
                wagon_count=len(classification_result.accepted_wagons),
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

                    reason = getattr(wagon, 'rejection_reason', 'UNKNOWN')
                    detailed_reason = getattr(wagon, 'detailed_rejection_reason', '')

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
            self.railway_capacity_service.get_capacity_info('collection')
        else:
            pass

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
        """Handle wagon retrofit completed event - batch wagons completing at same time."""
        # Find the wagon
        wagon = None
        for w in self.wagons:
            if getattr(w, 'id', None) == event.wagon_id:
                wagon = w
                break

        if not wagon:
            return

        # Add to batch for this workshop
        if event.workshop_id not in self._retrofitted_batches:
            self._retrofitted_batches[event.workshop_id] = []

        self._retrofitted_batches[event.workshop_id].append(wagon)

        # Schedule deferred check only once per workshop per time step
        if not self._pending_transport_checks.get(event.workshop_id, False):
            self._pending_transport_checks[event.workshop_id] = True
            self.infra.engine.schedule_process(self._check_and_transport_batch(event.workshop_id))

    def _get_workshop_capacity_for_batching(self, workshop_id: str) -> int:
        """Get workshop capacity for determining batch size."""
        for workshop in self.scenario.workshops:  # type: ignore[attr-defined, union-attr]
            if workshop.id == workshop_id:
                return workshop.retrofit_stations  # type: ignore[no-any-return]
        return 0

    def _check_and_transport_batch(self, workshop_id: str) -> Generator[Any, Any]:
        """Check if batch should be transported after allowing same-time completions to accumulate."""
        # Yield to allow all wagons completing at same time to be added to batch
        yield from self.infra.engine.delay(0)

        # Clear pending flag
        self._pending_transport_checks[workshop_id] = False

        if workshop_id not in self._retrofitted_batches or not self._retrofitted_batches[workshop_id]:
            return

        # Transport all wagons that completed together as one batch
        wagons_to_transport = self._retrofitted_batches[workshop_id][:]
        self._retrofitted_batches[workshop_id] = []

        if wagons_to_transport:
            self._form_and_transport_retrofitted_rake(wagons_to_transport, workshop_id)

            # Check if there are wagons waiting on collection tracks
            for track_id, wagons in self._track_wagons.items():
                if 'collection' in track_id and wagons:
                    pickup_event = WagonsReadyForPickupEvent(
                        track_id=track_id,
                        wagon_count=len(wagons),
                        event_timestamp=self.infra.engine.current_time(),
                    )
                    self.infra.event_bus.publish(pickup_event)
                    break  # Only trigger one pickup at a time

    def _form_and_transport_retrofitted_rake(self, wagons: list[Any], workshop_id: str) -> None:
        """Form rake from retrofitted wagons and request transport."""
        # Form rake
        rake = self._rake_formation_service.form_retrofitted_rake(wagons, workshop_id)
        self.rake_registry.register_rake(rake)

        # Publish rake formed event
        rake_event = RakeFormedEvent(rake=rake)
        self.infra.event_bus.publish(rake_event)

        # Request transport: workshop -> retrofitted -> parking
        transport_event = RakeTransportRequestedEvent(
            rake_id=rake.rake_id,
            from_track=workshop_id,
            to_track='retrofitted',
            rake_type=rake.rake_type,
        )
        self.infra.event_bus.publish(transport_event)

        # Remove from tracking
        for w in wagons:
            if w in self._retrofitted_batches[workshop_id]:
                self._retrofitted_batches[workshop_id].remove(w)

    def _bring_next_batch_from_retrofit(self, wagons: list[Any], workshop_id: str) -> Generator[Any, Any]:
        """Bring next batch of wagons from retrofit track to workshop."""
        if not wagons:
            return
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if not shunting_context:
            return

        yield from self._transport_wagon_batch_to_workshop(wagons, workshop_id, shunting_context)

    def _pickup_retrofitted_batch(self, wagons: list[Any]) -> Any:
        """Pickup retrofitted batch and move to parking."""
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if not shunting_context:
            return

        # Allocate locomotive for pickup
        loco = yield from shunting_context.allocate_locomotive(self)

        try:
            # Move to first workshop (WS1) to collect wagons
            yield from shunting_context.move_locomotive(self, loco, loco.current_track, 'WS1')

            # Couple wagons
            yield from shunting_context.couple_wagons(self, len(wagons), 'DAC')

            # Select retrofitted track and move to retrofitted area
            selected_retrofitted = self._select_track_by_type('retrofitted')
            retrofitted_track_id = selected_retrofitted.id if selected_retrofitted else 'retrofitted'

            yield from shunting_context.move_locomotive(self, loco, 'WS1', retrofitted_track_id)

            # Decouple wagons
            yield from shunting_context.decouple_wagons(self, len(wagons), 'DAC')

            # Move to parking
            yield from shunting_context.move_locomotive(self, loco, retrofitted_track_id, loco.home_track)

            # Select parking track and update wagon status
            selected_parking = self._select_track_by_type('parking')
            parking_track_id = selected_parking.id if selected_parking else 'parking'

            for wagon in wagons:
                wagon.status = 'PARKED'
                wagon.track = parking_track_id

        finally:
            # Release locomotive
            yield from shunting_context.release_locomotive(self, loco)

    def _pickup_individual_wagon(self, wagons: list[Any], workshop_id: str) -> Any:
        """Pickup individual wagon for MVP timeline compatibility."""
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if not shunting_context:
            return

        # Allocate locomotive for individual pickup
        loco = yield from shunting_context.allocate_locomotive(self)

        try:
            # Move to workshop to collect wagon
            yield from shunting_context.move_locomotive(self, loco, loco.current_track, workshop_id)

            # Couple wagon
            yield from shunting_context.couple_wagons(self, len(wagons), 'DAC')

            # Select retrofitted track and move to retrofitted area
            selected_retrofitted = self._select_track_by_type('retrofitted')
            retrofitted_track_id = selected_retrofitted.id if selected_retrofitted else 'retrofitted'

            yield from shunting_context.move_locomotive(self, loco, workshop_id, retrofitted_track_id)

            # Update wagon status and release workshop resources
            for wagon in wagons:
                wagon.status = 'RETROFITTED'
                wagon.track = retrofitted_track_id

                # Release workshop resource after pickup
                # TODO: This is currently a hack and needs to be improved
                if hasattr(wagon, '_workshop_resource') and hasattr(wagon, '_workshop_request'):  # pylint: disable=protected-access
                    wagon._workshop_resource.release(wagon._workshop_request)  # pylint: disable=protected-access
                    delattr(wagon, '_workshop_resource')
                    delattr(wagon, '_workshop_request')

            # Return to parking
            yield from shunting_context.move_locomotive(self, loco, retrofitted_track_id, loco.home_track)

        finally:
            # Release locomotive
            yield from shunting_context.release_locomotive(self, loco)

    def _process_individual_wagons(self, wagons: list[Any]) -> Any:
        """Process wagons individually, respecting workshop bay capacity."""
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if not shunting_context:
            return

        for wagon in wagons:
            # Wait for workshop bay to be available (listen for bay free event)
            # For now, process immediately for first wagon, then wait for completion events
            if wagon == wagons[0]:
                # First wagon can start immediately
                yield from self._move_wagon_to_workshop(wagon, 'WS1')
            else:
                # Subsequent wagons wait for previous wagon to complete and be picked up
                # This will be triggered by individual wagon retrofitted events
                pass

    def _move_wagon_to_workshop(self, wagon: Any, workshop_id: str) -> Any:
        """Move individual wagon from retrofit track to workshop bay."""
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if not shunting_context:
            return

        # Allocate locomotive
        loco = yield from shunting_context.allocate_locomotive(self)

        try:
            # Select retrofit track and move to retrofit track to get wagon
            selected_retrofit = self._select_track_by_type('retrofit')
            retrofit_track_id = selected_retrofit.id if selected_retrofit else 'retrofit'

            yield from shunting_context.move_locomotive(self, loco, loco.current_track, retrofit_track_id)

            # Couple wagon
            yield from shunting_context.couple_wagons(self, 1, 'SCREW')

            # Move to workshop
            yield from shunting_context.move_locomotive(self, loco, retrofit_track_id, workshop_id)

            # Decouple wagon at workshop
            yield from shunting_context.decouple_wagons(self, 1, 'SCREW')

            # Return to parking
            yield from shunting_context.move_locomotive(self, loco, workshop_id, loco.home_track)

            # Now wagon is at workshop and can start retrofitting
            wagon.track = workshop_id
            event = WagonReadyForRetrofitEvent(wagon=wagon, workshop_id=workshop_id)
            self.infra.event_bus.publish(event)

        finally:
            # Release locomotive
            yield from shunting_context.release_locomotive(self, loco)

    def _move_next_batch_to_workshop(self, wagons: list[Any], workshop_id: str) -> Any:
        """Move next batch of wagons from retrofit track to workshop."""
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if not shunting_context:
            return

        # Allocate locomotive
        loco = yield from shunting_context.allocate_locomotive(self)

        try:
            # Select retrofit track and move to retrofit track
            selected_retrofit = self._select_track_by_type('retrofit')
            retrofit_track_id = selected_retrofit.id if selected_retrofit else 'retrofit'

            yield from shunting_context.move_locomotive(self, loco, loco.current_track, retrofit_track_id)

            # Couple wagons
            yield from shunting_context.couple_wagons(self, len(wagons), 'SCREW')

            # Move to workshop
            yield from shunting_context.move_locomotive(self, loco, retrofit_track_id, workshop_id)

            # Decouple wagons at workshop
            yield from shunting_context.decouple_wagons(self, len(wagons), 'SCREW')

            # Return to parking
            yield from shunting_context.move_locomotive(self, loco, workshop_id, loco.home_track)

            # Now wagons are at workshop and can start retrofitting
            batch_id = f'batch_{self.infra.engine.current_time():.1f}'
            for wagon in wagons:
                wagon.track = workshop_id
                wagon.batch_id = batch_id
                event = WagonReadyForRetrofitEvent(wagon=wagon, workshop_id=workshop_id)
                self.infra.event_bus.publish(event)

        finally:
            # Release locomotive
            yield from shunting_context.release_locomotive(self, loco)

    def _pickup_and_process_next_batch(self, completed_wagons: list[Any], workshop_id: str) -> Any:  # pylint: disable=too-many-locals
        """Combine pickup of completed wagons and processing of next batch to eliminate timing gaps."""
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if not shunting_context:
            return

        # Allocate locomotive for pickup
        loco = yield from shunting_context.allocate_locomotive(self)

        try:
            # Pickup completed wagons
            yield from shunting_context.move_locomotive(self, loco, loco.current_track, workshop_id)

            yield from shunting_context.couple_wagons(self, len(completed_wagons), 'DAC')

            yield from shunting_context.move_locomotive(self, loco, workshop_id, 'retrofitted')

            yield from shunting_context.decouple_wagons(self, len(completed_wagons), 'DAC')

            # Select retrofitted track and update completed wagon status
            selected_retrofitted = self._select_track_by_type('retrofitted')
            retrofitted_track_id = selected_retrofitted.id if selected_retrofitted else 'retrofitted'

            for wagon in completed_wagons:
                wagon.status = 'PARKED'
                wagon.track = retrofitted_track_id

            # Return to parking first (MVP expects this)

            yield from shunting_context.move_locomotive(self, loco, retrofitted_track_id, loco.home_track)

            # Check if there are waiting wagons for this specific workshop
            if hasattr(self, '_waiting_wagons') and self._waiting_wagons:  # pylint: disable=no-member
                # Filter wagons assigned to this workshop (for multi-workshop) or all wagons (for single workshop)
                if len(self.scenario.workshops) > 1:  # type: ignore[attr-defined, union-attr]
                    workshop_wagons = [w for w in self._waiting_wagons if w.workshop_id == workshop_id]  # pylint: disable=no-member
                else:
                    workshop_wagons = self._waiting_wagons[:]  # pylint: disable=no-member

                if workshop_wagons:
                    workshop_capacity = len(completed_wagons)  # Same capacity as completed batch
                    next_batch_size = min(len(workshop_wagons), workshop_capacity)
                    next_batch = workshop_wagons[:next_batch_size]

                    # Remove processed wagons from waiting list
                    for wagon in next_batch:
                        if wagon in self._waiting_wagons:  # pylint: disable=no-member
                            self._waiting_wagons.remove(wagon)  # pylint: disable=no-member

                    # Select retrofit track and move from parking to retrofit track to get next batch (MVP flow)
                    selected_retrofit = self._select_track_by_type('retrofit')
                    retrofit_track_id = selected_retrofit.id if selected_retrofit else 'retrofit'

                    yield from shunting_context.move_locomotive(self, loco, loco.home_track, retrofit_track_id)

                    yield from shunting_context.couple_wagons(self, len(next_batch), 'SCREW')

                    yield from shunting_context.move_locomotive(self, loco, retrofit_track_id, workshop_id)

                    yield from shunting_context.decouple_wagons(self, len(next_batch), 'SCREW')

                    # Trigger retrofit for next batch
                    batch_id = f'batch_{self.infra.engine.current_time():.1f}'
                    for wagon in next_batch:
                        wagon.track = workshop_id
                        wagon.batch_id = batch_id
                        event = WagonReadyForRetrofitEvent(wagon=wagon, workshop_id=workshop_id)
                        self.infra.event_bus.publish(event)

                    # Return to parking from workshop
                    yield from shunting_context.move_locomotive(self, loco, workshop_id, loco.home_track)
                else:
                    # No more wagons for this workshop - add final movement for MVP compatibility
                    selected_retrofitted = self._select_track_by_type('retrofitted')
                    retrofitted_track_id = selected_retrofitted.id if selected_retrofitted else 'retrofitted'

                    yield from shunting_context.move_locomotive(self, loco, loco.home_track, retrofitted_track_id)

                    yield from shunting_context.move_locomotive(self, loco, retrofitted_track_id, loco.home_track)
            else:
                # No waiting wagons at all - add final movement for MVP compatibility
                selected_retrofitted = self._select_track_by_type('retrofitted')
                retrofitted_track_id = selected_retrofitted.id if selected_retrofitted else 'retrofitted'

                yield from shunting_context.move_locomotive(self, loco, loco.home_track, retrofitted_track_id)

                yield from shunting_context.move_locomotive(self, loco, retrofitted_track_id, loco.home_track)

        finally:
            # Release locomotive
            yield from shunting_context.release_locomotive(self, loco)

    def _transport_retrofitted_rake(self, rake: Any) -> Generator[Any, Any]:  # pylint: disable=too-many-locals, too-many-statements
        """Transport retrofitted rake: workshop -> retrofitted -> parking."""
        try:
            shunting_context = getattr(self.infra, 'shunting_context', None)
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

                # Update wagon locations, release workshop resources, and publish distributed events
                current_time = self.infra.engine.current_time()
                for wagon in rake.wagons:
                    wagon.track = retrofitted_track_id

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
            # Raising immediately is currently intended to avoid issues in premature shutdown of simulation
            except GeneratorExit:  # pylint: disable=try-except-raise
                raise

            self._retrofitted_accumulator.extend(rake.wagons)

            # Check if there are more wagons waiting to be retrofitted
            workshop_id = rake.formation_track
            has_more_wagons = workshop_id in self._waiting_at_retrofit and self._waiting_at_retrofit[workshop_id]

            # Calculate retrofitted track utilization
            retrofitted_capacity = self._get_retrofitted_track_capacity()
            total_length = sum(getattr(w, 'length', 20.0) for w in self._retrofitted_accumulator)
            utilization = total_length / retrofitted_capacity if retrofitted_capacity > 0 else 0

            # Move to parking if: (1) no more wagons waiting, OR (2) retrofitted track >= 80% full
            should_move_to_parking = not has_more_wagons or utilization >= 0.8

            if should_move_to_parking:
                wagons_to_park = self._retrofitted_accumulator[:]
                self._retrofitted_accumulator = []

                # Calculate total length BEFORE selecting track
                total_length = sum(getattr(wagon, 'length', 15.0) for wagon in wagons_to_park)

                # Check if parking capacity is available for these wagons
                selected_parking = self._select_track_by_type('parking')
                if not selected_parking:
                    raise RuntimeError(
                        f'CAPACITY EXCEEDED: No parking tracks available. '
                        f'Yard layout cannot handle the wagon volume. '
                        f'{len(wagons_to_park)} wagons ({total_length:.0f}m) cannot be parked.'
                    )

                parking_track_id = selected_parking.id

                loco2 = yield from shunting_context.allocate_locomotive(self)
                try:
                    selected_retrofitted = self._select_track_by_type('retrofitted')
                    retrofitted_track_id = selected_retrofitted.id if selected_retrofitted else 'retrofitted'

                    yield from shunting_context.move_locomotive(self, loco2, loco2.current_track, retrofitted_track_id)
                    yield from shunting_context.couple_wagons(self, len(wagons_to_park), 'DAC')
                    yield from shunting_context.move_locomotive(self, loco2, retrofitted_track_id, parking_track_id)
                    yield from shunting_context.decouple_wagons(self, len(wagons_to_park), 'DAC')

                    current_time = self.infra.engine.current_time()
                    for wagon in wagons_to_park:
                        wagon.status = WagonStatus.PARKING
                        wagon.track = parking_track_id
                        parked_event = WagonParkedEvent(wagon_id=wagon.id, parking_area_id=parking_track_id)
                        parked_event.event_timestamp = current_time
                        self.infra.event_bus.publish(parked_event)

                    # Update track occupancy
                    self._track_occupancy_m[parking_track_id] = (
                        self._track_occupancy_m.get(parking_track_id, 0.0) + total_length
                    )

                    yield from shunting_context.move_locomotive(self, loco2, parking_track_id, loco2.home_track)
                    yield from shunting_context.release_locomotive(self, loco2)
                except GeneratorExit:  # pylint: disable=try-except-raise
                    raise

            # After transporting retrofitted wagons, check if there are wagons waiting at retrofit track
            # Extract workshop_id from rake (it's the formation_track for retrofitted rakes)
            workshop_id = rake.formation_track
            if self._waiting_at_retrofit.get(workshop_id):
                # Bring next batch from retrofit to workshop
                workshop_capacity = self._get_workshop_capacity_for_batching(workshop_id)
                waiting_count = len(self._waiting_at_retrofit[workshop_id])
                next_batch_size = min(workshop_capacity, waiting_count)
                next_batch = self._waiting_at_retrofit[workshop_id][:next_batch_size]
                self._waiting_at_retrofit[workshop_id] = self._waiting_at_retrofit[workshop_id][next_batch_size:]

                # Schedule transport of next batch
                yield from self._bring_next_batch_from_retrofit(next_batch, workshop_id)
        except GeneratorExit:  # pylint: disable=try-except-raise
            return

    def get_metrics(self) -> dict[str, Any]:
        """Get yard operations metrics."""
        track_util = self._calculate_track_utilization()

        # Count wagons by status
        wagons_on_retrofitted = sum(1 for w in self.wagons if getattr(w, 'status', '') == 'RETROFITTED')
        wagons_on_retrofit = sum(1 for w in self.wagons if getattr(w, 'status', '') == 'READY_FOR_RETROFIT')
        wagons_on_collection = sum(1 for w in self.wagons if getattr(w, 'status', '') == 'COLLECTION')
        wagons_parked = sum(1 for w in self.wagons if getattr(w, 'status', '') == 'PARKED')

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
        for track_id in self._track_wagons:
            if 'collection' in track_id:
                available_capacity = self.railway_context.get_available_capacity(track_id)  # type: ignore[attr-defined]
                total_capacity = self.railway_context.get_total_capacity(track_id)  # type: ignore[attr-defined]
                if total_capacity > 0:
                    utilization = ((total_capacity - available_capacity) / total_capacity) * 100.0
                    track_util[track_id] = utilization

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
            for track in self._tracks_by_type.get('retrofitted', []):
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
        """Transport rake following professional process: collection → retrofit → workshop."""
        try:
            shunting_context = getattr(self.infra, 'shunting_context', None)
            if not shunting_context:
                yield from self._direct_rake_to_workshop(rake)
                return

            # Step 1: Move ALL wagons from collection to retrofit staging track
            loco = yield from shunting_context.allocate_locomotive(self)
            try:
                yield from shunting_context.move_locomotive(self, loco, loco.current_track, rake.formation_track)
                yield from shunting_context.couple_wagons(self, rake.wagon_count, 'SCREW', [])
                yield from shunting_context.move_locomotive(self, loco, rake.formation_track, rake.target_track)
                yield from shunting_context.decouple_wagons(self, rake.wagon_count, 'SCREW')
                yield from shunting_context.move_locomotive(self, loco, rake.target_track, loco.home_track)
            finally:
                yield from shunting_context.release_locomotive(self, loco)

            # Step 2: Transport FIRST batch only from retrofit to workshops in SEQUENCE order
            # Remaining wagons stay on retrofit track and are picked up when workshop capacity frees
            workshop_ids = (
                [w.id for w in self.scenario.workshops]
                if self.scenario and hasattr(self.scenario, 'workshops')
                else ['WS1']
            )

            # Get workshop capacities
            workshop_capacities = {ws_id: self._get_workshop_capacity_for_batching(ws_id) for ws_id in workshop_ids}

            # Distribute wagons using workshop-specific strategy
            strategy = getattr(self.scenario, 'workshop_selection_strategy', 'round_robin')
            if hasattr(strategy, 'value'):
                strategy = strategy.value

            self._workshop_round_robin_index = 0
            self._workshop_wagon_counts = dict.fromkeys(workshop_ids, 0)

            # Assign workshops to wagons using strategy
            for wagon in rake.wagons:
                if strategy == 'round_robin':
                    workshop_id = workshop_ids[self._workshop_round_robin_index % len(workshop_ids)]
                    self._workshop_round_robin_index += 1
                else:  # least_occupied
                    workshop_id = min(
                        self._workshop_wagon_counts.keys(), key=lambda ws: self._workshop_wagon_counts[ws]
                    )

                wagon.workshop_id = workshop_id
                self._workshop_wagon_counts[workshop_id] += 1

            # Group wagons by assigned workshop
            workshop_batches: dict[str, list[Wagon]] = {ws_id: [] for ws_id in workshop_ids}
            for wagon in rake.wagons:
                workshop_batches[wagon.workshop_id].append(wagon)

            # Transport first batch to each workshop, store rest as waiting
            for workshop_id in workshop_ids:
                batch_wagons = workshop_batches[workshop_id]
                if not batch_wagons:
                    continue

                batch_size = workshop_capacities[workshop_id]
                first_batch = batch_wagons[:batch_size]
                remaining = batch_wagons[batch_size:]

                # Transport first batch
                yield from self._transport_wagon_batch_to_workshop(first_batch, workshop_id, shunting_context)

                # Store remaining wagons for this workshop
                if remaining:
                    if workshop_id not in self._waiting_at_retrofit:
                        self._waiting_at_retrofit[workshop_id] = []
                    self._waiting_at_retrofit[workshop_id].extend(remaining)
        except GeneratorExit:
            return

    def _direct_rake_to_workshop(self, rake: Any) -> Generator[Any, Any]:
        """Direct rake assignment to workshop without shunting."""
        # Find wagons in the rake and update their status
        for wagon in self.wagons:
            if hasattr(wagon, 'rake_id') and wagon.rake_id == rake.rake_id:
                wagon.status = 'READY_FOR_RETROFIT'
                wagon.track = rake.target_track
                wagon.workshop_id = rake.target_track

                event = WagonReadyForRetrofitEvent(wagon=wagon, workshop_id=rake.target_track)
                self.infra.event_bus.publish(event)

        yield from self.infra.engine.delay(1.0)  # Small delay for processing

    def _transport_wagon_batch_to_workshop(
        self, wagons: list[Any], workshop_id: str, shunting_context: Any
    ) -> Generator[Any, Any]:
        """Transport a batch of wagons from retrofit to workshop."""
        loco = yield from shunting_context.allocate_locomotive(self)
        try:
            # Select retrofit track
            selected_retrofit = self._select_track_by_type('retrofit')
            retrofit_track_id = selected_retrofit.id if selected_retrofit else 'retrofit'

            yield from shunting_context.move_locomotive(self, loco, loco.current_track, retrofit_track_id)
            wagon_ids = [w.id for w in wagons]
            yield from shunting_context.couple_wagons(self, len(wagons), 'SCREW', wagon_ids)
            yield from shunting_context.move_locomotive(self, loco, retrofit_track_id, workshop_id, wagon_ids)
            yield from shunting_context.decouple_wagons(self, len(wagons), 'SCREW', wagon_ids)

            # Update wagon status and publish ready events
            for wagon in wagons:
                wagon.status = 'READY_FOR_RETROFIT'
                wagon.track = workshop_id
                wagon.workshop_id = workshop_id
                event = WagonReadyForRetrofitEvent(wagon=wagon, workshop_id=workshop_id)
                self.infra.event_bus.publish(event)

            yield from shunting_context.move_locomotive(self, loco, workshop_id, loco.home_track)
        finally:
            yield from shunting_context.release_locomotive(self, loco)

    def _get_workshop_capacities(self) -> dict[str, int]:
        """Get workshop capacities from scenario configuration."""
        workshop_capacities: dict[str, int] = {}
        if self.scenario and hasattr(self.scenario, 'workshops'):
            for workshop in self.scenario.workshops:
                workshop_capacities[workshop.id] = getattr(workshop, 'retrofit_stations', 1)

        if not workshop_capacities:
            workshop_capacities = {'WS1': 1}

        return workshop_capacities

    def _get_retrofit_track_capacities(self) -> dict[str, float]:
        """Get available capacities for retrofit tracks from railway infrastructure."""
        # Todo: Get track capacities from railway infrastructure context
        retrofit_tracks: dict[str, float] = {}

        if self.railway_capacity_service:
            # Get retrofit tracks from scenario or use defaults
            track_names = ['retrofit_1', 'retrofit_2', 'retrofit_3']
            if self.scenario and hasattr(self.scenario, 'tracks'):
                track_names = [t.id for t in self.scenario.tracks if 'retrofit' in t.id.lower()]

            for track_id in track_names:
                capacity_info = self.railway_capacity_service.get_capacity_info(track_id)
                if capacity_info and capacity_info.available_capacity > 0:
                    retrofit_tracks[track_id] = capacity_info.available_capacity

        # Fallback to default if no tracks found
        if not retrofit_tracks:
            retrofit_tracks = {'retrofit': 150.0}  # Default 150m capacity

        return retrofit_tracks

    def _get_available_locomotive_count(self) -> int:
        """Get number of available locomotives for pickup operations."""
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if shunting_context and hasattr(shunting_context, 'locomotive_pool'):
            return len(shunting_context.locomotive_pool.available_locomotives)
        return 2  # Default assumption

    def _select_track_by_type(self, track_type: str, strategy: str | None = None) -> Any | None:  # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches
        """Select track by type using configured strategy."""
        tracks = self._tracks_by_type.get(track_type, [])
        if not tracks:
            return None

        # Use scenario strategy if not specified
        if strategy is None:
            if track_type == 'parking':
                strategy = getattr(self.scenario, 'parking_selection_strategy', 'least_occupied')
            else:
                strategy = getattr(self.scenario, 'track_selection_strategy', 'least_occupied')
            if hasattr(strategy, 'value'):
                strategy = strategy.value

        if strategy == 'round_robin':
            idx = self._round_robin_index[track_type] % len(tracks)
            self._round_robin_index[track_type] += 1
            return tracks[idx]

        if strategy == 'least_occupied':
            # For parking tracks, always use length-based occupancy tracking
            if track_type == 'parking':
                # Get fill factor from scenario (default 0.75)
                fill_factor = 0.75
                if self.scenario and hasattr(self.scenario, 'fill_factor'):
                    fill_factor = self.scenario.fill_factor

                # Get track lengths from scenario
                track_lengths: dict[str, float] = {}
                if self.scenario and hasattr(self.scenario, 'tracks'):
                    for t in self.scenario.tracks:
                        track_lengths[t.id] = getattr(t, 'length', 200.0)

                # Calculate available capacity for each track (respecting fill factor)
                track_info = []
                for track in tracks:
                    track_length = track_lengths.get(track.id, 200.0)
                    max_usable = track_length * fill_factor  # Apply fill factor
                    occupied = self._track_occupancy_m.get(track.id, 0.0)
                    available_usable = max_usable - occupied  # Available within fill factor
                    available_absolute = track_length - occupied  # Available absolute capacity
                    track_info.append((track, available_usable, available_absolute, occupied, track_length))

                # First try: Select track with most available capacity within fill factor
                available_tracks = [
                    (t, avail_usable) for t, avail_usable, avail_abs, occ, tlen in track_info if avail_usable > 0
                ]
                if available_tracks:
                    return max(available_tracks, key=lambda x: x[1])[0]

                # Second try: All tracks at/over fill factor - check if ANY absolute capacity remains
                tracks_with_absolute_capacity = [
                    (t, avail_abs) for t, avail_usable, avail_abs, occ, tlen in track_info if avail_abs > 0
                ]
                if tracks_with_absolute_capacity:
                    # Use track with most absolute capacity remaining
                    return max(tracks_with_absolute_capacity, key=lambda x: x[1])[0]

                # No capacity available - return None to signal capacity exceeded
                return None
            if self.railway_context:
                # For non-parking tracks, use railway context capacity
                available = [(t, self.railway_context.get_available_capacity(t.id)) for t in tracks]
                return max(available, key=lambda x: x[1])[0] if available else tracks[0]
            # Fallback to first track
            return tracks[0]

        return tracks[0]

    def _execute_pickup_plan(self, pickup_plan: Any, from_track_id: str) -> Generator[Any, Any]:  # pylint: disable=too-many-locals
        """Execute pickup plan - form rakes limited by retrofit track capacity."""
        if not pickup_plan.rakes_to_pickup:
            return

        # Collect all wagons in sequence (physical order on collection track)
        # Todo: Check the allocation here. It looks like it is just workkshop
        all_wagons = []
        workshop_allocations: dict[str, list[Wagon]] = {}
        for rake in pickup_plan.rakes_to_pickup:
            all_wagons.extend(rake.wagons)
            for wagon in rake.wagons:
                workshop_id = getattr(wagon, 'workshop_id', 'WS1')
                if workshop_id not in workshop_allocations:
                    workshop_allocations[workshop_id] = []
                workshop_allocations[workshop_id].append(wagon)
        # Get retrofit track capacity
        retrofit_capacity = self._get_retrofit_track_capacity()

        # Split wagons by retrofit track capacity - MUST take wagons in sequence
        remaining_wagons = all_wagons
        batch_num = 1

        while remaining_wagons:
            # Take wagons sequentially from front until capacity is reached
            rake_wagons = []
            total_length = 0.0
            for wagon in remaining_wagons:
                wagon_length = getattr(wagon, 'length', 15.0)
                if total_length + wagon_length <= retrofit_capacity:
                    rake_wagons.append(wagon)
                    total_length += wagon_length
                else:
                    break

            if not rake_wagons:
                # If no wagons fit, take at least one to avoid infinite loop
                if remaining_wagons:
                    rake_wagons = [remaining_wagons[0]]
                else:
                    break

            batch_num += 1

            remaining_wagons = remaining_wagons[len(rake_wagons) :]

            # Form rake from specific collection track
            rake = self.wagon_pickup_service.create_single_retrofit_rake(
                rake_wagons,
                {
                    ws: [wagon for wagon in rake_wagons if getattr(wagon, 'workshop_id', None) == ws]
                    for ws in workshop_allocations
                },
            )
            rake.formation_track = from_track_id
            self.rake_registry.register_rake(rake)

            rake_event = RakeFormedEvent(rake=rake)
            self.infra.event_bus.publish(rake_event)

            transport_event = RakeTransportRequestedEvent(
                rake_id=rake.rake_id,
                from_track=rake.formation_track,
                to_track=rake.target_track,
                rake_type=rake.rake_type,
            )
            self.infra.event_bus.publish(transport_event)

            # Wait for transport to complete before forming next batch (only if more batches remain)
            if remaining_wagons:
                yield from self.infra.engine.delay(3.0)

    def _get_retrofit_track_capacity(self) -> float:
        """Get retrofit track full capacity in meters (no fill_factor for retrofit staging)."""
        # TODO: We should use the trackcapacity management of the railway infrastructure context (currently broke!)
        retrofit_tracks = self._tracks_by_type.get('retrofit', [])

        if not retrofit_tracks:
            raise RuntimeError(
                f'CONFIGURATION ERROR: No retrofit tracks found in scenario. '
                f'Available track types: {list(self._tracks_by_type.keys())}'
            )
        if not self.railway_context:
            raise RuntimeError('CONFIGURATION ERROR: Railway context not initialized.')
        track_capacity = self.railway_context.get_total_capacity(retrofit_tracks[0].id)
        if track_capacity <= 0:
            raise RuntimeError(
                f"CONFIGURATION ERROR: Retrofit track '{retrofit_tracks[0].id}' has no capacity. "
                f'Check topology.json for track length definition.'
            )
        return track_capacity

    def _get_retrofitted_track_capacity(self) -> float:
        """Get retrofitted track capacity in meters."""
        # TODO: We should use the trackcapacity management of the railway infrastructure context (currently broke!)
        retrofitted_tracks = self._tracks_by_type.get('retrofitted', [])
        if not retrofitted_tracks:
            raise RuntimeError(
                f'CONFIGURATION ERROR: No retrofitted tracks found in scenario. '
                f'Available track types: {list(self._tracks_by_type.keys())}'
            )
        if not self.railway_context:
            raise RuntimeError('CONFIGURATION ERROR: Railway context not initialized.')
        track_capacity = self.railway_context.get_track_capacity(retrofitted_tracks[0].id)
        if track_capacity <= 0:
            raise RuntimeError(
                f"CONFIGURATION ERROR: Retrofitted track '{retrofitted_tracks[0].id}' has no capacity. "
                f'Check topology.json for track length definition.'
            )
        return track_capacity

    def _execute_direct_rake_assignment(self, rakes: list[Any]) -> Generator[Any, Any]:
        """Fallback: direct rake assignment without shunting operations."""
        for rake in rakes:
            yield from self._direct_rake_to_workshop(rake)

    def _execute_retrofit_track_transport(self, wagons: list[Any]) -> Generator[Any, Any]:
        """Execute transport to retrofit tracks using new strategy."""
        retrofit_tracks = self._get_retrofit_track_capacities()

        # Use convenience method for retrofit track rake formation
        retrofit_rakes = self._rake_formation_service.form_retrofit_track_rakes(wagons, retrofit_tracks, 'collection')

        # Execute transport for each rake
        for rake in retrofit_rakes:
            self.rake_registry.register_rake(rake)

            transport_event = RakeTransportRequestedEvent(
                rake_id=rake.rake_id,
                from_track=rake.formation_track,
                to_track=rake.target_track,
                rake_type=rake.rake_type,
            )
            self.infra.event_bus.publish(transport_event)

            yield from self.infra.engine.delay(0.1)

    def _form_workshop_rakes(self, wagons: list[Any]) -> None:
        """Legacy method - now uses retrofit track transport."""
        # Use new retrofit track transport instead of workshop-based approach
        self.infra.engine.schedule_process(self._execute_retrofit_track_transport(wagons))

    def _trigger_initial_movement(self) -> Any:
        """Trigger initial locomotive movement for test compatibility."""
        yield from self.infra.engine.delay(0)

    def get_status(self) -> dict[str, Any]:
        """Get status."""
        return {'status': 'ready'}

    def _flush_retrofitted_to_parking(self) -> Generator[Any, Any]:
        """Flush remaining wagons from retrofitted accumulator to parking."""
        shunting_context = getattr(self.infra, 'shunting_context', None)
        if not shunting_context or not self._retrofitted_accumulator:
            return

        wagons_to_park = self._retrofitted_accumulator[:]
        self._retrofitted_accumulator = []

        loco = yield from shunting_context.allocate_locomotive(self)
        try:
            selected_retrofitted = self._select_track_by_type('retrofitted')
            retrofitted_track_id = selected_retrofitted.id if selected_retrofitted else 'retrofitted'

            selected_parking = self._select_track_by_type('parking')
            parking_track_id = selected_parking.id if selected_parking else 'parking'

            yield from shunting_context.move_locomotive(self, loco, loco.current_track, retrofitted_track_id)
            yield from shunting_context.couple_wagons(self, len(wagons_to_park), 'DAC')
            yield from shunting_context.move_locomotive(self, loco, retrofitted_track_id, parking_track_id)
            yield from shunting_context.decouple_wagons(self, len(wagons_to_park), 'DAC')

            current_time = self.infra.engine.current_time()
            for wagon in wagons_to_park:
                wagon.status = WagonStatus.PARKING
                wagon.track = parking_track_id
                parked_event = WagonParkedEvent(wagon_id=wagon.id, parking_area_id=parking_track_id)
                parked_event.event_timestamp = current_time
                self.infra.event_bus.publish(parked_event)

            yield from shunting_context.move_locomotive(self, loco, parking_track_id, loco.home_track)
        finally:
            yield from shunting_context.release_locomotive(self, loco)

    def cleanup(self) -> None:
        """Cleanup."""

    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed."""
