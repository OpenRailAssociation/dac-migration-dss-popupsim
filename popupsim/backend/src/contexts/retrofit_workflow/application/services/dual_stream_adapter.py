"""Adapter to add dual-stream recording to existing event system."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent

if TYPE_CHECKING:
    from contexts.retrofit_workflow.application.event_collector import EventCollector


def create_dual_stream_wagon_publisher(
    original_publisher: Callable[[WagonJourneyEvent], None] | None, event_collector: 'EventCollector'
) -> Callable[[WagonJourneyEvent], None]:
    """Wrap wagon event publisher to also record dual-stream events."""

    def publisher(event: WagonJourneyEvent) -> None:
        # Call original publisher
        if original_publisher:
            original_publisher(event)

        # Map to dual-stream events
        _record_wagon_dual_stream(event, event_collector)

    return publisher


def create_dual_stream_loco_publisher(
    original_publisher: Callable[[LocomotiveMovementEvent], None] | None, event_collector: 'EventCollector'
) -> Callable[[LocomotiveMovementEvent], None]:
    """Wrap locomotive event publisher to also record dual-stream events."""

    def publisher(event: LocomotiveMovementEvent) -> None:
        # Call original publisher
        if original_publisher:
            original_publisher(event)

        # Map to dual-stream events
        _record_loco_dual_stream(event, event_collector)

    return publisher


def _record_wagon_dual_stream(event: WagonJourneyEvent, collector: 'EventCollector') -> None:
    """Record wagon event in dual-stream system."""
    # State changes - map event types to states
    state_map = {
        'ARRIVED': 'arrived',
        'REJECTED': 'rejected',
        'WAITING_FOR_COUPLING': 'waiting',
        'ON_RETROFIT_TRACK': 'queued',
        'AT_WORKSHOP': 'in_workshop',
        'RETROFIT_STARTED': 'in_workshop',
        'RETROFIT_COMPLETED': 'retrofitted',
        'PARKED': 'parked',
        'MOVING': 'moving',
    }

    if event.event_type in state_map:
        collector.record_state_change(
            timestamp=event.timestamp,
            resource_id=event.wagon_id,
            resource_type='wagon',
            state=state_map[event.event_type],
            train_id=event.train_id,
            rejection_reason=event.rejection_reason,
        )

    # Process events for coupling/decoupling (NO location change)
    process_map = {
        'RAKE_COUPLING_STARTED': 'rake_coupling_started',
        'RAKE_COUPLING_COMPLETED': 'rake_coupling_completed',
        'RAKE_DECOUPLING_STARTED': 'rake_decoupling_started',
        'RAKE_DECOUPLING_COMPLETED': 'rake_decoupling_completed',
    }

    if event.event_type in process_map:
        # Extract coupler type from event metadata if available
        coupler_type = getattr(event, 'coupler_type', None)

        collector.record_process_event(
            timestamp=event.timestamp,
            resource_id=event.wagon_id,
            resource_type='wagon',
            process_state=process_map[event.event_type],
            location=event.location,
            coupler_type=coupler_type,
        )
        # Do NOT record location change for coupling/decoupling
        return

    # Location changes ONLY for actual location transitions (NOT for MOVING)
    # MOVING state doesn't change location - wagons are in transit
    location_change_events = {
        'ARRIVED',
        'WAITING_FOR_COUPLING',
        'ON_RETROFIT_TRACK',
        'AT_WORKSHOP',
        'RETROFIT_STARTED',
        'ON_RETROFITTED_TRACK',
        'PARKED',
    }

    if event.event_type in location_change_events and event.location and event.location != 'REJECTED':
        collector.record_location_change(
            timestamp=event.timestamp, resource_id=event.wagon_id, resource_type='wagon', location=event.location
        )

    # For MOVING events, record route_path without changing location
    if event.event_type == 'MOVING':
        route_path = getattr(event, 'route_path', None)
        if route_path and event.location:
            # Record location with route_path for visualization
            collector.record_location_change(
                timestamp=event.timestamp,
                resource_id=event.wagon_id,
                resource_type='wagon',
                location=event.location,
                route_path=route_path,
            )


def _record_loco_dual_stream(event: LocomotiveMovementEvent, collector: 'EventCollector') -> None:
    """Record locomotive event in dual-stream system."""
    # State changes
    state_map = {'ALLOCATED': 'assigned', 'MOVING': 'moving', 'ARRIVED': 'idle', 'RELEASED': 'idle'}

    if event.event_type in state_map:
        collector.record_state_change(
            timestamp=event.timestamp,
            resource_id=event.locomotive_id,
            resource_type='locomotive',
            state=state_map[event.event_type],
        )

    # Location changes
    if event.to_location:
        collector.record_location_change(
            timestamp=event.timestamp,
            resource_id=event.locomotive_id,
            resource_type='locomotive',
            location=event.to_location,
            previous_location=event.from_location,
        )
