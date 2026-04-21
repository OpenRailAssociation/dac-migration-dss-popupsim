"""Railway Operations Service - Universal application service for railway operations."""

from collections.abc import Callable
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.strategies.wagon_collection_strategies import WagonCollectionStrategy
from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.entities.wagon import Wagon


@dataclass
class RailwayServices:
    """Container for railway services and infrastructure needed by operations."""

    env: Any
    locomotive_manager: Any
    train_service: Any
    route_service: Any
    process_times: Any
    batch_event_publisher: Any = None
    loco_event_publisher: Any = None


class RailwayOperationsService:
    """Universal application service for railway operations with SimPy encapsulation."""

    def transport_rake_between_tracks(
        self, rake: BatchAggregate, origin: str, destination: str, services: RailwayServices
    ) -> Generator[Any, Any]:
        """Complete rake transport: allocate loco → form train → transport → dissolve → release loco.

        Args:
            rake: BatchAggregate (rake of coupled wagons) to transport
            origin: Starting track/location
            destination: Target track/location
            services: Railway services container (includes env)
        """
        batch_id = rake.id
        wagons = rake.wagons
        env = services.env

        # 1. Allocate locomotive
        loco = yield from services.locomotive_manager.allocate(purpose='batch_transport')

        if services.loco_event_publisher:
            EventPublisherHelper.publish_loco_allocated(
                services.loco_event_publisher, env.now, loco.id, 'batch_transport'
            )

        # Publish transport started event with correct locomotive ID
        if services.batch_event_publisher:
            EventPublisherHelper.publish_batch_transport_started(
                services.batch_event_publisher,
                env.now,
                batch_id,
                loco.id,
                destination,
                len(wagons),
            )

        try:
            # 2. Form train and prepare
            route_type = services.route_service.get_route_type(origin, destination)
            train = services.train_service.form_train(loco, rake, origin, destination, route_type)
            prep_time = services.train_service.prepare_train(train, services.process_times, env.now)
            yield env.timeout(prep_time)

            # 3. Transport
            if services.loco_event_publisher:
                EventPublisherHelper.publish_loco_moving(
                    services.loco_event_publisher, env.now, loco.id, origin, destination
                )

            transport_time = services.route_service.get_duration(origin, destination)
            yield env.timeout(transport_time)

            # 4. Dissolve train
            loco_decouple_time = services.train_service.dissolve_train(train)
            yield env.timeout(loco_decouple_time)

            rake_decouple_time = services.train_service.coupling_service.get_rake_decoupling_time(wagons)
            yield env.timeout(rake_decouple_time)

            # Publish arrival event
            if services.batch_event_publisher:
                EventPublisherHelper.publish_batch_arrived(
                    services.batch_event_publisher,
                    env.now,
                    batch_id,
                    destination,
                    len(wagons),
                )

        finally:
            # 5. Release locomotive
            yield from services.locomotive_manager.release(loco)

    def collect_wagons_by_strategy(
        self, first_wagon: Wagon, queue: Any, strategy: WagonCollectionStrategy
    ) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons using pluggable strategies.

        Args:
            first_wagon: First wagon already obtained
            queue: SimPy queue to collect from
            strategy: Collection strategy to use

        Returns
        -------
            List of collected wagons
        """
        wagons = [first_wagon]

        while len(queue.items) > 0:
            next_wagon = queue.items[0]

            if strategy.should_collect_wagon(wagons, next_wagon, None):
                wagon = yield queue.get()
                wagons.append(wagon)
            else:
                break

        return wagons

    def wait_for_resource_availability(
        self, env: Any, resource_checker: Callable[[], bool], timeout: float | None = None
    ) -> Generator[Any, Any]:
        """Wait for resource with timeout.

        Args:
            env: SimPy environment
            resource_checker: Function that returns True when resource is available
            timeout: Optional timeout in simulation ticks
        """
        start_time = env.now

        while not resource_checker():
            if timeout and (env.now - start_time) >= timeout:
                break
            yield env.event()
