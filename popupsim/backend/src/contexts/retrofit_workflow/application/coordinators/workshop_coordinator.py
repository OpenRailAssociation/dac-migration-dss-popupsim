"""Workshop Coordinator - orchestrates workshop retrofit operations."""

from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.services.train_formation_service import TrainFormationService
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks


class WorkshopCoordinator:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Coordinates workshop retrofit operations.

    Flow:
    1. Wait for workshop to become free
    2. Form batch from retrofit track (size = available bays)
    3. Transport batch to workshop
    4. Process all wagons simultaneously
    5. Transport batch to retrofitted track
    """

    def __init__(
        self,
        env: Any,
        workshops: dict[str, Any],
        retrofit_queue: Any,
        retrofitted_queue: Any,
        locomotive_manager: Any,
        route_service: Any,
        batch_service: Any,
        train_service: TrainFormationService,
        scenario: Any,
        wagon_event_publisher: Any = None,
        loco_event_publisher: Any = None,
        event_publisher: Any = None,
    ):
        self.env = env
        self.workshops = workshops
        self.retrofit_queue = retrofit_queue
        self.retrofitted_queue = retrofitted_queue
        self.locomotive_manager = locomotive_manager
        self.route_service = route_service
        self.batch_service = batch_service
        self.train_service = train_service
        self.scenario = scenario
        self.wagon_event_publisher = wagon_event_publisher or event_publisher
        self.loco_event_publisher = loco_event_publisher
        self.event_publisher = event_publisher
        self.workshop_busy = dict.fromkeys(self.workshops.keys(), False)
        self.track_manager = None
        self._waiting_processes: list[Any] = []
        self.track_selector: Any = None  # Will be set by context

    def _get_tracks_by_type(self, track_type: str) -> list[Any]:
        """Get tracks by type using track_selector if available, otherwise empty list."""
        if self.track_selector:
            return self.track_selector.get_tracks_of_type(track_type)
        return []

    def start(self) -> None:
        """Start coordinator processes."""
        self.env.process(self._assignment_process())

    def _assignment_process(self) -> Generator[Any, Any]:
        """Single process that assigns wagons from retrofit queue to workshops."""
        while True:
            print(f'[t={self.env.now}] WS: Waiting for wagon...')
            wagon = yield self.retrofit_queue.get()
            print(f'[t={self.env.now}] WS: Got {wagon.id}')

            available_workshop = self._find_available_workshop()
            if not available_workshop:
                print(f'[t={self.env.now}] WS: No workshop available, creating wait event')
                wait_event = self.env.event()
                self._waiting_processes.append(wait_event)
                yield wait_event
                print(f'[t={self.env.now}] WS: Workshop became available')
                available_workshop = self._find_available_workshop()
                if not available_workshop:
                    raise RuntimeError(f'Workshop should be available after event at t={self.env.now}')

            print(f'[t={self.env.now}] WS: Using {available_workshop}')
            self.workshop_busy[available_workshop] = True

            workshop = self.workshops[available_workshop]
            available_bays = workshop.available_capacity
            wagons = [wagon]

            for _ in range(available_bays - 1):
                if len(self.retrofit_queue.items) > 0:
                    additional_wagon = yield self.retrofit_queue.get()
                    wagons.append(additional_wagon)
                    print(f'[t={self.env.now}] WS: Added {additional_wagon.id}')
                else:
                    break

            batch_wagons = self.batch_service.form_batch_for_workshop(wagons, workshop)
            print(f'[t={self.env.now}] WS: Batch {len(batch_wagons)} wagons for {available_workshop}')

            # Remove wagons from retrofit track to free capacity
            if not self.track_manager:
                raise RuntimeError('track_manager not initialized - cannot manage retrofit track capacity')
            # Get retrofit tracks by type (same pattern as collection_coordinator)
            retrofit_tracks = self._get_tracks_by_type('retrofit')
            if not retrofit_tracks:
                raise RuntimeError('No retrofit tracks found in track_manager')
            retrofit_track = retrofit_tracks[0]  # Use first retrofit track

            try:
                yield from retrofit_track.remove_wagons(batch_wagons)
            except Exception as e:
                print(f'[t={self.env.now}] WS: ERROR removing wagons from retrofit track: {e}')
                print(f'[t={self.env.now}] WS: Wagons to remove: {[w.id for w in batch_wagons]}')
                print(
                    f'[t={self.env.now}] WS: Track capacity: {retrofit_track.get_occupied_capacity():.1f}m / {retrofit_track.capacity_meters:.1f}m'
                )
                print(f'[t={self.env.now}] WS: Wagons on track: {[w.id for w in retrofit_track.wagons]}')
                raise

            self.env.process(self._process_and_release(available_workshop, batch_wagons))

    def _find_available_workshop(self) -> str | None:
        """Find first available workshop (not busy)."""
        for workshop_id in sorted(self.workshops.keys()):
            if not self.workshop_busy[workshop_id]:
                return workshop_id  # type: ignore[no-any-return]
        return None

    def _process_and_release(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Process batch and release workshop."""
        try:
            yield from self._process_workshop_batch(workshop_id, wagons)
            # Release workshop BEFORE pickup transport
            print(
                f'[t={self.env.now}] WS: Releasing {workshop_id}, notifying {len(self._waiting_processes)} waiting processes'
            )
            self.workshop_busy[workshop_id] = False
            # Trigger ALL waiting processes
            for event in self._waiting_processes:
                if not event.triggered:
                    event.succeed()
            self._waiting_processes.clear()
            # Now do pickup transport (workshop is free for next batch)
            yield from self._pickup_and_transport_to_retrofitted(workshop_id, wagons)
        except Exception as e:
            print(f'[t={self.env.now}] WS: ERROR in process_and_release: {e}')
            self.workshop_busy[workshop_id] = False
            for event in self._waiting_processes:
                if not event.triggered:
                    event.succeed()
            self._waiting_processes.clear()
            raise

    def _process_workshop_batch(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Process a batch of wagons in workshop."""
        # MVP: Couple wagons on retrofit track for workshop batch
        # (Assumes wagons are decoupled - simplification until full rake management)
        coupling_time = self._get_coupling_time(wagons)
        yield self.env.timeout(coupling_time)

        # Create inbound batch aggregate (SCREW couplers) for rake validation
        try:
            _ = self.batch_service.create_batch_aggregate(wagons, workshop_id)
            # Batch aggregate created successfully - rake is valid
            loco = yield from self.locomotive_manager.allocate(purpose='batch_transport')
            yield from self._transport_to_workshop(loco, workshop_id)
        except Exception:  # pylint: disable=broad-exception-caught
            # Fallback to old method
            loco = yield from self.locomotive_manager.allocate(purpose='batch_transport')
            yield from self._transport_to_workshop(loco, workshop_id)

        # Decouple rake at workshop arrival (wagons go to bays)
        decoupling_time = self._get_decoupling_time(wagons)
        yield self.env.timeout(decoupling_time)

        retrofit_start_time = self.env.now
        yield from self._start_retrofit(workshop_id, wagons)
        yield from self._return_locomotive(loco, workshop_id)

        elapsed_time = self.env.now - retrofit_start_time
        retrofit_time_ticks = timedelta_to_sim_ticks(self.scenario.process_times.wagon_retrofit_time)
        remaining_time = max(0, retrofit_time_ticks - elapsed_time)

        if remaining_time > 0:
            yield self.env.timeout(remaining_time)

        # Complete retrofit and publish events
        yield from self._complete_retrofit_events(workshop_id, wagons)

    def _transport_to_workshop(self, loco: Any, workshop_id: str) -> Generator[Any, Any]:
        """Transport locomotive to workshop with train formation."""
        # Transport: loco_parking -> retrofit (no prep, loco is already there)
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'loco_parking', 'retrofit'
        )

        transport_time = self.route_service.get_duration('loco_parking', 'retrofit')
        yield self.env.timeout(transport_time)

        # Prepare train at retrofit (loco coupling + prep time)
        # Note: Loco coupling time is now dynamic based on wagon coupler types
        # For workshop transport, wagons have SCREW couplers (before retrofit)
        loco_coupling_time = timedelta_to_sim_ticks(self.scenario.process_times.screw_coupling_time)
        prep_time_ticks = loco_coupling_time + timedelta_to_sim_ticks(
            self.scenario.process_times.shunting_preparation_time
        )
        yield self.env.timeout(prep_time_ticks)

        # Transport: retrofit -> workshop
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'retrofit', workshop_id
        )

        transport_time = self.route_service.get_duration('retrofit', workshop_id)
        yield self.env.timeout(transport_time)

    def _start_retrofit(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Start retrofit process for wagons."""
        workshop = self.workshops[workshop_id]
        busy_before = len(workshop.busy_bays)

        for wagon in wagons:
            workshop.assign_to_bay(wagon.id, self.env.now)
            wagon.start_retrofit(workshop_id, self.env.now)
            print(f'[t={self.env.now}] WS: wagon[{wagon.id}] RETROFIT_STARTED {workshop_id}')

            EventPublisherHelper.publish_wagon_event(
                self.wagon_event_publisher,
                self.env.now,
                wagon.id,
                'RETROFIT_STARTED',
                workshop_id,
                'PROCESSING',
            )

        # Publish workshop resource event
        busy_after = len(workshop.busy_bays)
        if self.event_publisher:
            event = ResourceStateChangeEvent(
                timestamp=self.env.now,
                resource_type='workshop',
                resource_id=workshop_id,
                change_type='bay_occupied',
                total_bays=workshop.capacity,
                busy_bays_before=busy_before,
                busy_bays_after=busy_after,
            )
            self.event_publisher(event)

        yield self.env.timeout(0)

    def _return_locomotive(self, loco: Any, workshop_id: str) -> Generator[Any, Any]:
        """Return locomotive to parking."""
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, workshop_id, 'loco_parking'
        )

        return_time = self.route_service.get_duration(workshop_id, 'loco_parking')
        yield self.env.timeout(return_time)
        yield from self.locomotive_manager.release(loco)

    def _transport_from_workshop(self, loco: Any, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Transport wagons from workshop to retrofitted track with train formation."""
        # Move locomotive from loco_parking to workshop
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'loco_parking', workshop_id
        )

        transport_time = self.route_service.get_duration('loco_parking', workshop_id)
        yield self.env.timeout(transport_time)

        # Get route type
        route_type = self.route_service.get_route_type(workshop_id, 'retrofitted')

        # Create batch for train formation
        batch = self.batch_service.create_batch_aggregate(wagons, 'retrofitted')

        # Form train at workshop
        train = self.train_service.form_train(
            locomotive=loco, batch=batch, origin=workshop_id, destination='retrofitted', route_type=route_type
        )

        # Prepare train (adds loco coupling + prep time)
        prep_time = self.train_service.prepare_train(train, self.scenario.process_times, self.env.now)
        yield self.env.timeout(prep_time)

        # Depart from workshop
        train.depart(self.env.now)
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, workshop_id, 'retrofitted'
        )

        # Transport to retrofitted
        transport_time = self.route_service.get_duration(workshop_id, 'retrofitted')
        yield self.env.timeout(transport_time)
        train.arrive(self.env.now)

        # Put wagons on retrofitted queue
        print(f'[t={self.env.now}] WS: Putting {len(wagons)} wagons in retrofitted_queue')
        # Get retrofitted tracks by type (same pattern as collection_coordinator)
        retrofitted_tracks = self._get_tracks_by_type('retrofitted')
        if retrofitted_tracks:
            retrofitted_track = retrofitted_tracks[0]
            yield from retrofitted_track.add_wagons(wagons)
        for wagon in wagons:
            wagon.move_to('retrofitted')
            self.retrofitted_queue.put(wagon)
            print(f'[t={self.env.now}] WS: Put {wagon.id} in retrofitted_queue')

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'retrofitted', 'loco_parking'
        )

        # Return locomotive
        return_time = self.route_service.get_duration('retrofitted', 'loco_parking')
        yield self.env.timeout(return_time)

        train.dissolve()

    def _get_decoupling_time(self, wagons: list[Wagon]) -> float:
        """Calculate decoupling time: (n-1) couplings x time_per_coupling."""
        if len(wagons) <= 1:
            return 0.0

        # Use first wagon's coupler type
        coupler_type = wagons[0].coupler_a.type.value if hasattr(wagons[0], 'coupler_a') else 'SCREW'

        if coupler_type == 'SCREW':
            time_per_coupling = timedelta_to_sim_ticks(self.scenario.process_times.screw_decoupling_time)
        else:  # DAC
            time_per_coupling = timedelta_to_sim_ticks(self.scenario.process_times.dac_decoupling_time)

        return (len(wagons) - 1) * time_per_coupling

    def _get_coupling_time(self, wagons: list[Wagon]) -> float:
        """Calculate coupling time: (n-1) couplings x time_per_coupling."""
        if len(wagons) <= 1:
            return 0.0

        coupler_type = wagons[0].coupler_a.type.value if hasattr(wagons[0], 'coupler_a') else 'SCREW'

        if coupler_type == 'SCREW':
            time_per_coupling = timedelta_to_sim_ticks(self.scenario.process_times.screw_coupling_time)
        else:  # DAC
            time_per_coupling = timedelta_to_sim_ticks(self.scenario.process_times.dac_coupling_time)

        return (len(wagons) - 1) * time_per_coupling

    def _complete_retrofit_events(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Complete retrofit and publish events only."""
        workshop = self.workshops[workshop_id]
        busy_before = len(workshop.busy_bays)

        for wagon in wagons:
            bay = workshop.get_wagon_bay(wagon.id)
            if bay:
                workshop.complete_retrofit(bay.id)

            wagon.complete_retrofit(self.env.now)

            EventPublisherHelper.publish_wagon_event(
                self.wagon_event_publisher,
                self.env.now,
                wagon.id,
                'RETROFIT_COMPLETED',
                workshop_id,
                'COMPLETED',
            )

        # Publish workshop resource event
        busy_after = len(workshop.busy_bays)
        if self.event_publisher:
            event = ResourceStateChangeEvent(
                timestamp=self.env.now,
                resource_type='workshop',
                resource_id=workshop_id,
                change_type='bay_freed',
                total_bays=workshop.capacity,
                busy_bays_before=busy_before,
                busy_bays_after=busy_after,
            )
            self.event_publisher(event)

        yield self.env.timeout(0)

    def _pickup_and_transport_to_retrofitted(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Pickup and transport wagons to retrofitted track (after workshop released)."""
        # Couple rake
        coupling_time = self._get_coupling_time(wagons)
        yield self.env.timeout(coupling_time)

        # Allocate locomotive
        print(f'[t={self.env.now}] WS: Allocating locomotive for pickup from {workshop_id}')
        pickup_loco = yield from self.locomotive_manager.allocate(purpose='batch_transport')
        print(f'[t={self.env.now}] WS: Got locomotive {pickup_loco.id} for pickup')

        try:
            _ = self.batch_service.create_batch_aggregate(wagons, 'retrofitted')
            yield from self._transport_from_workshop(pickup_loco, workshop_id, wagons)
        except Exception:  # pylint: disable=broad-exception-caught
            yield from self._transport_from_workshop(pickup_loco, workshop_id, wagons)
        finally:
            yield from self.locomotive_manager.release(pickup_loco)
