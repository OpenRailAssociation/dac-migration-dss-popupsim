"""Workshop Coordinator - orchestrates workshop retrofit operations."""

from collections.abc import Generator
from dataclasses import dataclass
import logging
from typing import Any

from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.events import CouplingEvent
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.services.train_formation_service import TrainFormationService
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks

logger = logging.getLogger(__name__)


@dataclass
class WorkshopCoordinatorConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for workshop coordinator.

    Note: Multiple attributes needed for coordinator configuration.
    """

    env: Any
    workshops: dict[str, Any]
    retrofit_queue: Any
    retrofitted_queue: Any
    locomotive_manager: Any
    route_service: Any
    batch_service: Any
    train_service: TrainFormationService
    scenario: Any
    wagon_event_publisher: Any = None
    loco_event_publisher: Any = None
    event_publisher: Any = None
    coupling_event_publisher: Any = None


class WorkshopCoordinator:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Coordinates workshop retrofit operations.

    Flow:
    1. Wait for workshop to become free
    2. Form batch from retrofit track (size = available bays)
    3. Transport batch to workshop
    4. Process all wagons simultaneously
    5. Transport batch to retrofitted track

    Note: Multiple instance attributes needed for coordination responsibilities.
    """

    def __init__(self, config: WorkshopCoordinatorConfig) -> None:
        self.env = config.env
        self.workshops = config.workshops
        self.retrofit_queue = config.retrofit_queue
        self.retrofitted_queue = config.retrofitted_queue
        self.locomotive_manager = config.locomotive_manager
        self.route_service = config.route_service
        self.batch_service = config.batch_service
        self.train_service = config.train_service
        self.scenario = config.scenario
        self.wagon_event_publisher = config.wagon_event_publisher or config.event_publisher
        self.loco_event_publisher = config.loco_event_publisher
        self.event_publisher = config.event_publisher
        self.coupling_event_publisher = config.coupling_event_publisher
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
        # Start one assignment process per retrofit track to monitor all queues
        retrofit_tracks = self._get_tracks_by_type('retrofit')
        if not retrofit_tracks:
            logger.error('No retrofit tracks configured')
            return

        for retrofit_track in retrofit_tracks:
            self.env.process(self._assignment_process(retrofit_track))
            logger.info('Started workshop assignment process for %s', retrofit_track.track_id)

    def _assignment_process(self, retrofit_track: Any) -> Generator[Any, Any]:
        """Single process that assigns wagons from a specific retrofit track queue to workshops.

        Args:
            retrofit_track: The retrofit track to monitor
        """
        retrofit_queue = retrofit_track.queue
        retrofit_track_id = retrofit_track.track_id

        while True:
            wagon = yield retrofit_queue.get()
            logger.info('t=%.1f: WAGON[%s] → Retrieved from %s queue', self.env.now, wagon.id, retrofit_track_id)

            available_workshop = self._find_available_workshop()
            if not available_workshop:
                logger.info('t=%.1f: WORKSHOP → No workshop available, waiting...', self.env.now)
                wait_event = self.env.event()
                self._waiting_processes.append(wait_event)
                yield wait_event
                logger.info('t=%.1f: WORKSHOP → Workshop became available', self.env.now)
                available_workshop = self._find_available_workshop()
                if not available_workshop:
                    raise RuntimeError(f'Workshop should be available after event at t={self.env.now}')

            logger.info('t=%.1f: WORKSHOP[%s] → Selected for batch', self.env.now, available_workshop)

            # Mark workshop as busy IMMEDIATELY to prevent race condition
            self.workshop_busy[available_workshop] = True

            workshop = self.workshops[available_workshop]
            available_bays = workshop.available_capacity
            wagons = [wagon]

            for _ in range(available_bays - 1):
                if len(retrofit_queue.items) > 0:
                    additional_wagon = yield retrofit_queue.get()
                    wagons.append(additional_wagon)
                    logger.info('t=%.1f: WAGON[%s] → Added to batch', self.env.now, additional_wagon.id)
                else:
                    break

            batch_wagons = self.batch_service.form_batch_for_workshop(wagons, workshop)
            wagon_ids = ','.join(w.id for w in batch_wagons)
            logger.info(
                't=%.1f: BATCH[%s] → Formed %d wagons for %s',
                self.env.now,
                wagon_ids,
                len(batch_wagons),
                available_workshop,
            )

            # Remove wagons from THIS retrofit track to free capacity
            if not self.track_manager:
                raise RuntimeError('track_manager not initialized - cannot manage retrofit track capacity')

            try:
                yield from retrofit_track.remove_wagons(batch_wagons)
                logger.info(
                    't=%.1f: TRACK[%s] → Removed %d wagons (%.1fm freed)',
                    self.env.now,
                    retrofit_track_id,
                    len(batch_wagons),
                    sum(w.length for w in batch_wagons),
                )
            except Exception as e:
                print(f'[t={self.env.now}] WS: ERROR removing wagons from {retrofit_track_id}: {e}')
                print(f'[t={self.env.now}] WS: Wagons to remove: {[w.id for w in batch_wagons]}')
                print(
                    f'[t={self.env.now}] WS: Track capacity: '
                    f'{retrofit_track.get_occupied_capacity():.1f}m / {retrofit_track.capacity_meters:.1f}m'
                )
                print(f'[t={self.env.now}] WS: Wagons on track: {[w.id for w in retrofit_track.wagons]}')
                raise

            # Allocate locomotive (workshop already marked as busy above)
            loco = yield from self.locomotive_manager.allocate(purpose='batch_transport')

            # Start workshop process
            self.env.process(self._process_and_release(available_workshop, batch_wagons, loco, retrofit_track.track_id))

    def _find_available_workshop(self) -> str | None:
        """Find first available workshop (not busy)."""
        for workshop_id in sorted(self.workshops.keys()):
            if not self.workshop_busy[workshop_id]:
                return workshop_id  # type: ignore[no-any-return]
        return None

    def _process_and_release(  # noqa: C901
        self, workshop_id: str, wagons: list[Wagon], loco: Any, retrofit_track_id: str
    ) -> Generator[Any, Any]:
        """Process batch and release workshop.

        Args:
            workshop_id: Workshop ID
            wagons: List of wagons to process
            loco: Locomotive
            retrofit_track_id: ID of the retrofit track where wagons came from
        """
        try:
            yield from self._process_workshop_batch(workshop_id, wagons, loco, retrofit_track_id)

            # Allocate pickup locomotive and transport wagons away
            coupling_time = self._get_coupling_time(wagons)
            wagon_ids = ','.join(w.id for w in wagons)
            logger.info(
                't=%.1f: RAKE[%s] → COUPLING at %s (%d couplings, %.1f min)',
                self.env.now,
                wagon_ids,
                workshop_id,
                len(wagons) - 1,
                coupling_time,
            )
            yield self.env.timeout(coupling_time)

            logger.info('t=%.1f: LOCO → Allocating for pickup from %s', self.env.now, workshop_id)
            pickup_loco = yield from self.locomotive_manager.allocate(purpose='batch_transport')
            logger.info('t=%.1f: LOCO[%s] → Allocated for pickup', self.env.now, pickup_loco.id)

            # Transport wagons away from workshop
            try:
                retrofitted_tracks = self._get_tracks_by_type('retrofitted')
                if not retrofitted_tracks:
                    raise RuntimeError('No retrofitted tracks configured')
                # Select retrofitted track with most available capacity (load balancing)
                retrofitted_track = max(retrofitted_tracks, key=lambda t: t.get_available_capacity())
                retrofitted_track_id = retrofitted_track.track_id
                _ = self.batch_service.create_batch_aggregate(wagons, retrofitted_track_id)
                yield from self._transport_from_workshop(pickup_loco, workshop_id, wagons)
            except GeneratorExit:
                pass
            except Exception:  # pylint: disable=broad-exception-caught
                yield from self._transport_from_workshop(pickup_loco, workshop_id, wagons)
            finally:
                yield from self.locomotive_manager.release(pickup_loco)

            # NOW release workshop (wagons are gone)
            logger.info(
                't=%.1f: WORKSHOP[%s] → Released, notifying %d waiting processes',
                self.env.now,
                workshop_id,
                len(self._waiting_processes),
            )
            self.workshop_busy[workshop_id] = False
            # Only trigger ONE waiting process to prevent race condition
            if self._waiting_processes:
                event = self._waiting_processes.pop(0)
                if not event.triggered:
                    event.succeed()
        except GeneratorExit:
            # Simulation ended - clean up and re-raise
            self.workshop_busy[workshop_id] = False
            if self._waiting_processes:
                event = self._waiting_processes.pop(0)
                if not event.triggered:
                    event.succeed()
            raise
        except Exception as e:
            print(f'[t={self.env.now}] WS: ERROR in process_and_release: {e}')
            self.workshop_busy[workshop_id] = False
            # Only trigger ONE waiting process to prevent race condition
            if self._waiting_processes:
                event = self._waiting_processes.pop(0)
                if not event.triggered:
                    event.succeed()
            raise

    def _process_workshop_batch(  # pylint: disable=too-many-locals
        self, workshop_id: str, wagons: list[Wagon], loco: Any, retrofit_track_id: str
    ) -> Generator[Any, Any]:
        """Process a batch of wagons in workshop.

        Args:
            workshop_id: Workshop ID
            wagons: List of wagons to process
            loco: Locomotive
            retrofit_track_id: ID of the retrofit track where wagons came from
        """
        # MVP: Couple wagons on retrofit track for workshop batch
        coupling_time = self._get_coupling_time(wagons)
        wagon_ids = ','.join(w.id for w in wagons)
        logger.info(
            't=%.1f: RAKE[%s] → COUPLING at retrofit (%d couplings, %.1f min)',
            self.env.now,
            wagon_ids,
            len(wagons) - 1,
            coupling_time,
        )
        yield self.env.timeout(coupling_time)

        # Create inbound batch aggregate (SCREW couplers) for rake validation
        try:
            _ = self.batch_service.create_batch_aggregate(wagons, workshop_id)
            # Batch aggregate created successfully - rake is valid
            yield from self._transport_to_workshop(loco, workshop_id, wagons, retrofit_track_id)
        except GeneratorExit:
            pass
        except Exception:  # pylint: disable=broad-exception-caught
            # Fallback to old method
            yield from self._transport_to_workshop(loco, workshop_id, wagons, retrofit_track_id)

        # Decouple rake at workshop arrival (wagons go to bays)
        decoupling_time = self._get_decoupling_time(wagons)
        wagon_ids = ','.join(w.id for w in wagons)
        logger.info(
            't=%.1f: RAKE[%s] → DECOUPLING at %s (%d couplings, %.1f min)',
            self.env.now,
            wagon_ids,
            workshop_id,
            len(wagons) - 1,
            decoupling_time,
        )
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

    def _transport_to_workshop(
        self, loco: Any, workshop_id: str, wagons: list[Wagon], retrofit_track_id: str
    ) -> Generator[Any, Any]:
        """Transport locomotive to workshop with train formation.

        Args:
            loco: Locomotive
            workshop_id: Target workshop ID
            wagons: List of wagons to transport
            retrofit_track_id: ID of the retrofit track where wagons are located
        """
        # Transport: loco home track -> retrofit (no prep, loco is already there)
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, loco.home_track, retrofit_track_id
        )

        transport_time = self.route_service.get_duration(loco.home_track, retrofit_track_id)
        yield self.env.timeout(transport_time)

        # Prepare train at retrofit (loco coupling + prep time)
        # Note: Loco coupling time is now dynamic based on wagon coupler types
        # For workshop transport, wagons have SCREW couplers (before retrofit)
        loco_coupling_time = timedelta_to_sim_ticks(self.scenario.process_times.screw_coupling_time)
        prep_time_ticks = timedelta_to_sim_ticks(self.scenario.process_times.shunting_preparation_time)

        logger.info(
            't=%.1f: LOCO[%s] → COUPLING at %s (%.1f min)', self.env.now, loco.id, retrofit_track_id, loco_coupling_time
        )
        if self.coupling_event_publisher:
            self.coupling_event_publisher(
                CouplingEvent(
                    timestamp=self.env.now,
                    locomotive_id=loco.id,
                    event_type='COUPLING_STARTED',
                    location=retrofit_track_id,
                    coupler_type='SCREW',
                    wagon_count=0,
                    duration=loco_coupling_time,
                )
            )
        yield self.env.timeout(loco_coupling_time)
        if self.coupling_event_publisher:
            self.coupling_event_publisher(
                CouplingEvent(
                    timestamp=self.env.now,
                    locomotive_id=loco.id,
                    event_type='COUPLING_COMPLETED',
                    location=retrofit_track_id,
                    coupler_type='SCREW',
                    wagon_count=0,
                    duration=loco_coupling_time,
                )
            )

        if prep_time_ticks > 0:
            logger.info(
                't=%.1f: LOCO[%s] → SHUNTING_PREP at %s (%.1f min)',
                self.env.now,
                loco.id,
                retrofit_track_id,
                prep_time_ticks,
            )
            if self.coupling_event_publisher:
                self.coupling_event_publisher(
                    CouplingEvent(
                        timestamp=self.env.now,
                        locomotive_id=loco.id,
                        event_type='SHUNTING_PREPARATION',
                        location=retrofit_track_id,
                        coupler_type='',
                        wagon_count=0,
                        duration=prep_time_ticks,
                    )
                )
        yield self.env.timeout(prep_time_ticks)

        # Transport: retrofit -> workshop - NOW wagons start moving
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, retrofit_track_id, workshop_id
        )

        # Get route path for MOVING state visualization
        route_path = self.route_service.get_route_path(retrofit_track_id, workshop_id)

        # Publish MOVING state for all wagons
        for wagon in wagons:
            EventPublisherHelper.publish_wagon_event(
                self.wagon_event_publisher,
                self.env.now,
                wagon.id,
                'MOVING',
                retrofit_track_id,
                'MOVING',
                route_path=route_path,
            )

        transport_time = self.route_service.get_duration(retrofit_track_id, workshop_id)
        yield self.env.timeout(transport_time)

        # Wagons arrived at workshop - publish arrival state immediately (end of MOVING)
        for wagon in wagons:
            EventPublisherHelper.publish_wagon_event(
                self.wagon_event_publisher,
                self.env.now,
                wagon.id,
                'AT_WORKSHOP',
                workshop_id,
                'ARRIVED',
            )

        # Decouple locomotive from rake at workshop
        # Use loco_coupling_time from process_times (not rake coupling time)
        loco_decoupling_time = timedelta_to_sim_ticks(self.scenario.process_times.get_decoupling_time('SCREW'))

        logger.info(
            't=%.1f: LOCO[%s] → DECOUPLING at %s (%.1f min)', self.env.now, loco.id, workshop_id, loco_decoupling_time
        )
        if self.coupling_event_publisher:
            self.coupling_event_publisher(
                CouplingEvent(
                    timestamp=self.env.now,
                    locomotive_id=loco.id,
                    event_type='DECOUPLING_STARTED',
                    location=workshop_id,
                    coupler_type='SCREW',
                    wagon_count=0,
                    duration=loco_decoupling_time,
                )
            )
        yield self.env.timeout(loco_decoupling_time)
        if self.coupling_event_publisher:
            self.coupling_event_publisher(
                CouplingEvent(
                    timestamp=self.env.now,
                    locomotive_id=loco.id,
                    event_type='DECOUPLING_COMPLETED',
                    location=workshop_id,
                    coupler_type='SCREW',
                    wagon_count=0,
                    duration=loco_decoupling_time,
                )
            )

    def _start_retrofit(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Start retrofit process for wagons."""
        workshop = self.workshops[workshop_id]
        busy_before = len(workshop.busy_bays)

        for wagon in wagons:
            workshop.assign_to_bay(wagon.id, self.env.now)
            wagon.start_retrofit(workshop_id, self.env.now)
            logger.info('t=%.1f: WAGON[%s] → RETROFIT_STARTED at %s', self.env.now, wagon.id, workshop_id)

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
            self.loco_event_publisher, self.env.now, loco.id, workshop_id, loco.home_track
        )

        return_time = self.route_service.get_duration(workshop_id, loco.home_track)
        yield self.env.timeout(return_time)
        yield from self.locomotive_manager.release(loco)

    def _transport_from_workshop(  # pylint: disable=too-many-locals
        self, loco: Any, workshop_id: str, wagons: list[Wagon]
    ) -> Generator[Any, Any]:
        """Transport wagons from workshop to retrofitted track with train formation."""
        # Get retrofitted tracks and select one with most available capacity
        retrofitted_tracks = self._get_tracks_by_type('retrofitted')
        if not retrofitted_tracks:
            raise RuntimeError('No retrofitted tracks configured')
        retrofitted_track = max(retrofitted_tracks, key=lambda t: t.get_available_capacity())
        retrofitted_track_id = retrofitted_track.track_id

        # Move locomotive from home track to workshop
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, loco.home_track, workshop_id
        )

        transport_time = self.route_service.get_duration(loco.home_track, workshop_id)
        yield self.env.timeout(transport_time)

        # Get route type
        route_type = self.route_service.get_route_type(workshop_id, retrofitted_track_id)

        # Create batch for train formation
        batch = self.batch_service.create_batch_aggregate(wagons, retrofitted_track_id)

        # Form train at workshop
        train = self.train_service.form_train(
            locomotive=loco, batch=batch, origin=workshop_id, destination=retrofitted_track_id, route_type=route_type
        )

        # Prepare train (adds loco coupling + prep time) - wagons wait at workshop
        prep_start_time = self.env.now
        prep_operations = self.train_service.prepare_train(
            train,
            self.scenario.process_times,
            prep_start_time,
            coupling_event_publisher=self.coupling_event_publisher,
        )

        # Publish RAKE_COUPLING_STARTED for wagons if rake coupling happens
        if prep_operations['rake_coupling']:
            rake_op = prep_operations['rake_coupling']
            for wagon in wagons:
                EventPublisherHelper.publish_wagon_event(
                    self.wagon_event_publisher,
                    self.env.now,
                    wagon.id,
                    'RAKE_COUPLING_STARTED',
                    workshop_id,
                    'COUPLING',
                    coupler_type=rake_op['coupler_type'],
                )

        # Wait for ALL preparation
        yield self.env.timeout(prep_operations['total_time'])

        # Publish RAKE_COUPLING_COMPLETED for wagons if rake coupling happened
        if prep_operations['rake_coupling']:
            rake_op = prep_operations['rake_coupling']
            for wagon in wagons:
                EventPublisherHelper.publish_wagon_event(
                    self.wagon_event_publisher,
                    self.env.now,
                    wagon.id,
                    'RAKE_COUPLING_COMPLETED',
                    workshop_id,
                    'WAITING',
                    coupler_type=rake_op['coupler_type'],
                )

        logger.info(
            't=%.1f: LOCO[%s] → TRAIN_PREP completed at %s (%.1f min)',
            self.env.now,
            loco.id,
            workshop_id,
            prep_operations['total_time'],
        )

        # Depart from workshop - NOW after coupling is complete
        train.depart(self.env.now)
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, workshop_id, retrofitted_track_id
        )

        # Get route path for MOVING state visualization
        route_path = self.route_service.get_route_path(workshop_id, retrofitted_track_id)

        # Publish MOVING state for all wagons - location stays at origin during movement
        for wagon in wagons:
            EventPublisherHelper.publish_wagon_event(
                self.wagon_event_publisher,
                self.env.now,
                wagon.id,
                'MOVING',
                workshop_id,
                'MOVING',
                route_path=route_path,
            )

        # Transport to retrofitted (pure transport time)
        transport_time = self.route_service.get_duration(workshop_id, retrofitted_track_id)
        yield self.env.timeout(transport_time)
        train.arrive(self.env.now)

        # Wagons arrived at retrofitted track - add to queue immediately, capacity managed by track
        logger.info(
            't=%.1f: BATCH → Putting %d wagons on retrofitted track %s', self.env.now, len(wagons), retrofitted_track_id
        )

        # Add wagons to track capacity (may block if full)
        yield from retrofitted_track.add_wagons(wagons)

        # Update wagon locations and add to workflow queue
        for wagon in wagons:
            wagon.move_to(retrofitted_track.track_id)
            retrofitted_track.queue.put(wagon)  # Add to workflow queue
            # Publish arrival event on retrofitted track
            EventPublisherHelper.publish_wagon_event(
                self.wagon_event_publisher,
                self.env.now,
                wagon.id,
                'ON_RETROFITTED_TRACK',
                retrofitted_track.track_id,
                'WAITING',
            )
            logger.info(
                't=%.1f: WAGON[%s] → Added to retrofitted track %s',
                self.env.now,
                wagon.id,
                retrofitted_track.track_id,
            )

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, retrofitted_track_id, loco.home_track
        )

        # Return locomotive
        return_time = self.route_service.get_duration(retrofitted_track_id, loco.home_track)
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

        total_time = (len(wagons) - 1) * time_per_coupling
        return total_time

    def _get_coupling_time(self, wagons: list[Wagon]) -> float:
        """Calculate coupling time: (n-1) couplings x time_per_coupling."""
        if len(wagons) <= 1:
            return 0.0

        coupler_type = wagons[0].coupler_a.type.value if hasattr(wagons[0], 'coupler_a') else 'SCREW'

        if coupler_type == 'SCREW':
            time_per_coupling = timedelta_to_sim_ticks(self.scenario.process_times.screw_coupling_time)
        else:  # DAC
            time_per_coupling = timedelta_to_sim_ticks(self.scenario.process_times.dac_coupling_time)

        total_time = (len(wagons) - 1) * time_per_coupling
        return total_time

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
        except GeneratorExit:
            pass
        except Exception:  # pylint: disable=broad-exception-caught
            yield from self._transport_from_workshop(pickup_loco, workshop_id, wagons)
        finally:
            yield from self.locomotive_manager.release(pickup_loco)
