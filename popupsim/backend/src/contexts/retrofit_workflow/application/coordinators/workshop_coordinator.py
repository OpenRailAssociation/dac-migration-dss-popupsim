"""Workshop Coordinator - orchestrates workshop retrofit operations."""

from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import WorkshopCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.interfaces.coordination_interfaces import CoordinationService
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
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

    def __init__(self, config: WorkshopCoordinatorConfig, coordination: CoordinationService):
        self.env = config.env
        self.workshops = config.workshops
        self.retrofit_queue = config.retrofit_queue
        self.retrofitted_queue = config.retrofitted_queue
        self.locomotive_manager = config.locomotive_manager
        self.route_service = config.route_service
        self.batch_service = config.batch_service
        self.scenario = config.scenario
        self.wagon_event_publisher = config.wagon_event_publisher
        self.loco_event_publisher = config.loco_event_publisher
        self.coordination = coordination
        self.workshop_busy = dict.fromkeys(self.workshops.keys(), False)
        self.track_manager = None
        self._workshop_free_event: Any = None

    def start(self) -> None:
        """Start coordinator processes."""
        self.env.process(self._assignment_process())

    def _assignment_process(self) -> Generator[Any, Any]:
        """Single process that assigns wagons from retrofit queue to workshops."""
        while True:
            wagon = yield self.retrofit_queue.get()

            available_workshop = self._find_available_workshop()
            while not available_workshop:
                workshop_free_event = self.env.event()
                self._workshop_free_event = workshop_free_event
                yield workshop_free_event
                available_workshop = self._find_available_workshop()

            self.workshop_busy[available_workshop] = True

            workshop = self.workshops[available_workshop]
            available_bays = workshop.available_capacity
            wagons = [wagon]

            for _ in range(available_bays - 1):
                if len(self.retrofit_queue.items) > 0:
                    additional_wagon = yield self.retrofit_queue.get()
                    wagons.append(additional_wagon)
                else:
                    break

            # Form batch based on workshop capacity
            batch_wagons = self.batch_service.form_batch_for_workshop(wagons, workshop)

            # Use old batch processing temporarily
            # Free retrofit track capacity
            if self.track_manager:
                retrofit_track = self.track_manager.get_track('retrofit')
                if retrofit_track:
                    yield from retrofit_track.remove_wagons(batch_wagons)

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
        finally:
            self.workshop_busy[workshop_id] = False
            # Trigger waiting assignment process if it exists
            if self._workshop_free_event is not None and not self._workshop_free_event.triggered:
                self._workshop_free_event.succeed()

    def _process_workshop_batch(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Process a batch of wagons in workshop."""
        # MVP: Couple wagons on retrofit track for workshop batch
        # (Assumes wagons are decoupled - simplification until full rake management)
        coupling_time = self._get_coupling_time(wagons)
        yield self.env.timeout(coupling_time)

        # Create inbound batch aggregate (SCREW couplers)
        try:
            batch_aggregate_in = self.batch_service.create_batch_aggregate(wagons, workshop_id)
            loco = yield from self.locomotive_manager.allocate(purpose='batch_transport')
            yield from self._transport_to_workshop_with_batch(loco, workshop_id, batch_aggregate_in)
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

        yield from self._complete_retrofit_and_pickup(workshop_id, wagons)

    def _complete_retrofit_and_pickup(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Complete retrofit and handle pickup transport."""
        workshop = self.workshops[workshop_id]

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

        # Couple rake at workshop departure (bays → wagons)
        coupling_time = self._get_coupling_time(wagons)
        yield self.env.timeout(coupling_time)

        # Create outbound batch aggregate (DAC couplers after retrofit)
        pickup_loco = yield from self.locomotive_manager.allocate(purpose='batch_transport')
        try:
            batch_aggregate_out = self.batch_service.create_batch_aggregate(wagons, 'retrofitted')
            yield from self._transport_from_workshop_with_batch(pickup_loco, workshop_id, batch_aggregate_out)
        except Exception:  # pylint: disable=broad-exception-caught
            # Fallback to old method
            yield from self._transport_from_workshop(pickup_loco, workshop_id, wagons)
        finally:
            yield from self.locomotive_manager.release(pickup_loco)

    def _transport_to_workshop_with_batch(
        self,
        loco: Any,
        workshop_id: str,
        batch_aggregate: Any,  # noqa: ARG002
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to workshop (no coupling time - handled manually at workshop)."""
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'loco_parking', 'retrofit'
        )

        transport_time = self.route_service.get_duration('loco_parking', 'retrofit')
        yield self.env.timeout(transport_time)

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'retrofit', workshop_id
        )

        # Use base transport time only (coupling/decoupling handled manually at workshop)
        transport_time = self.route_service.get_duration('retrofit', workshop_id)
        yield self.env.timeout(transport_time)

    def _transport_from_workshop_with_batch(
        self, loco: Any, workshop_id: str, batch_aggregate: Any
    ) -> Generator[Any, Any]:
        """Transport batch from workshop to retrofitted track (no coupling - handled at workshop)."""
        wagons = batch_aggregate.wagons

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'loco_parking', workshop_id
        )

        # Move to workshop
        transport_time = self.route_service.get_duration('loco_parking', workshop_id)
        yield self.env.timeout(transport_time)

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, workshop_id, 'retrofitted'
        )

        # Use base transport time only (coupling/decoupling handled manually at workshop)
        transport_time = self.route_service.get_duration(workshop_id, 'retrofitted')
        yield self.env.timeout(transport_time)

        # Put wagons on retrofitted queue
        for wagon in wagons:
            wagon.move_to('retrofitted')
            self.retrofitted_queue.put(wagon)

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'retrofitted', 'loco_parking'
        )

        # Return locomotive
        return_time = self.route_service.get_duration('retrofitted', 'loco_parking')
        yield self.env.timeout(return_time)

    def _transport_to_workshop(self, loco: Any, workshop_id: str) -> Generator[Any, Any]:
        """Transport locomotive to workshop."""
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'loco_parking', 'retrofit'
        )

        transport_time = self.route_service.get_duration('loco_parking', 'retrofit')
        yield self.env.timeout(transport_time)

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'retrofit', workshop_id
        )

        transport_time = self.route_service.get_duration('retrofit', workshop_id)
        yield self.env.timeout(transport_time)

    def _start_retrofit(self, workshop_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Start retrofit process for wagons."""
        workshop = self.workshops[workshop_id]

        for wagon in wagons:
            workshop.assign_to_bay(wagon.id, self.env.now)
            wagon.start_retrofit(workshop_id, self.env.now)

            EventPublisherHelper.publish_wagon_event(
                self.wagon_event_publisher,
                self.env.now,
                wagon.id,
                'RETROFIT_STARTED',
                workshop_id,
                'PROCESSING',
            )

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
        """Transport wagons from workshop to retrofitted track."""
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'loco_parking', workshop_id
        )

        # Move to workshop
        transport_time = self.route_service.get_duration('loco_parking', workshop_id)
        yield self.env.timeout(transport_time)

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, workshop_id, 'retrofitted'
        )

        # Transport to retrofitted
        transport_time = self.route_service.get_duration(workshop_id, 'retrofitted')
        yield self.env.timeout(transport_time)

        # Put wagons on retrofitted queue
        for wagon in wagons:
            wagon.move_to('retrofitted')
            self.retrofitted_queue.put(wagon)

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'retrofitted', 'loco_parking'
        )

        # Return locomotive
        return_time = self.route_service.get_duration('retrofitted', 'loco_parking')
        yield self.env.timeout(return_time)

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
