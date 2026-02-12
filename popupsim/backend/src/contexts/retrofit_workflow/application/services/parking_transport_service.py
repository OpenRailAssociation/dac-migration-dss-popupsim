"""Parking transport service for orchestrating wagon transport to parking areas."""

from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class ParkingTransportService:
    """Application service for parking transport orchestration."""

    def __init__(self, config: Any):
        """Initialize transport service with configuration."""
        self.config = config

    def transport_batch_to_parking(self, batch_aggregate: Any, parking_track_id: str) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area with full orchestration.

        Args:
            batch_aggregate: Batch aggregate to transport
            parking_track_id: Target parking track ID

        Yields
        ------
            SimPy process events
        """
        batch_id = batch_aggregate.id
        wagons = batch_aggregate.wagons

        # Publish batch formation events
        self._publish_batch_events(batch_aggregate, parking_track_id)

        # Allocate locomotive
        loco = yield from self.config.locomotive_manager.allocate(purpose='batch_transport')
        EventPublisherHelper.publish_loco_allocated(self.config.loco_event_publisher, self.config.env.now, loco.id)

        try:
            # Execute transport workflow
            yield from self._execute_transport_workflow(loco, batch_aggregate, batch_id, parking_track_id)
            yield from self._park_wagons(wagons, parking_track_id)
            yield from self._return_locomotive(loco, parking_track_id)
        finally:
            # Always release locomotive
            yield from self.config.locomotive_manager.release(loco)

    def transport_batch_old_method(
        self, wagons: list[Wagon], batch_id: str, parking_track_id: str
    ) -> Generator[Any, Any]:
        """Transport batch using old method (fallback).

        Args:
            wagons: List of wagons to transport
            batch_id: Batch identifier
            parking_track_id: Target parking track ID

        Yields
        ------
            SimPy process events
        """
        loco = yield from self.config.locomotive_manager.allocate(purpose='batch_transport')
        EventPublisherHelper.publish_loco_allocated(self.config.loco_event_publisher, self.config.env.now, loco.id)

        try:
            yield from self._transport_to_parking_simple(loco, wagons, batch_id, parking_track_id)
            yield from self._park_wagons(wagons, parking_track_id)
            yield from self._return_locomotive(loco, parking_track_id)
        finally:
            yield from self.config.locomotive_manager.release(loco)

    def _publish_batch_events(self, batch_aggregate: Any, parking_track_id: str) -> None:
        """Publish batch formation events."""
        EventPublisherHelper.publish_batch_events_for_aggregate(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_aggregate,
            parking_track_id,
        )

    def _execute_transport_workflow(
        self, loco: Any, batch_aggregate: Any, batch_id: str, parking_track_id: str
    ) -> Generator[Any, Any]:
        """Execute complete transport workflow with train formation."""
        wagons = batch_aggregate.wagons

        # Publish transport start
        EventPublisherHelper.publish_batch_transport_started(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            loco.id,
            parking_track_id,
            len(wagons),
        )

        # Form train and prepare
        route_type = self.config.route_service.get_route_type('retrofitted', parking_track_id)
        train = self.config.train_service.form_train(loco, batch_aggregate, 'retrofitted', parking_track_id, route_type)
        process_times = self.config.scenario.process_times
        prep_time = self.config.train_service.prepare_train(train, process_times, self.config.env.now)
        yield self.config.env.timeout(prep_time)

        # Execute transport
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'retrofitted', parking_track_id
        )

        base_transport_time = self.config.route_service.get_duration('retrofitted', parking_track_id)
        yield self.config.env.timeout(base_transport_time)

        # Dissolve train
        loco_decouple_time = self.config.train_service.dissolve_train(train)
        yield self.config.env.timeout(loco_decouple_time)

        rake_decouple_time = self.config.train_service.coupling_service.get_rake_decoupling_time(wagons)
        yield self.config.env.timeout(rake_decouple_time)

        # Publish arrival
        EventPublisherHelper.publish_batch_arrived(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            parking_track_id,
            len(wagons),
        )

    def _transport_to_parking_simple(
        self, loco: Any, wagons: list[Wagon], batch_id: str, parking_track_id: str
    ) -> Generator[Any, Any]:
        """Perform transport without train formation (fallback)"""
        EventPublisherHelper.publish_batch_transport_started(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            loco.id,
            parking_track_id,
            len(wagons),
        )

        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'retrofitted', parking_track_id
        )

        transport_time = self.config.route_service.get_duration('retrofitted', parking_track_id)
        yield self.config.env.timeout(transport_time)

        EventPublisherHelper.publish_batch_arrived(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            parking_track_id,
            len(wagons),
        )

    def _park_wagons(self, wagons: list[Wagon], parking_track_id: str) -> Generator[Any, Any]:
        """Park wagons in parking area."""
        for wagon in wagons:
            wagon.park(parking_track_id)
            EventPublisherHelper.publish_wagon_event(
                self.config.wagon_event_publisher, self.config.env.now, wagon.id, 'PARKED', parking_track_id, 'PARKED'
            )
        yield self.config.env.timeout(0)

    def _return_locomotive(self, loco: Any, parking_track_id: str) -> Generator[Any, Any]:
        """Return locomotive to home track."""
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, parking_track_id, loco.home_track
        )

        return_time = self.config.route_service.get_duration(parking_track_id, 'loco_parking')
        yield self.config.env.timeout(return_time)
