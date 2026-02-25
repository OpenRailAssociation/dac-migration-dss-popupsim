"""Comprehensive integration mixin for process tracking and state management."""

from collections.abc import Generator
from typing import Any

from infrastructure.event_bus.event_bus import EventBus
from infrastructure.tracking.unified_resource_tracker import get_unified_tracker
from shared.domain.events.journey_timeline_events import LocomotiveLocationChangedEvent
from shared.domain.events.journey_timeline_events import LocomotiveState
from shared.domain.events.journey_timeline_events import LocomotiveStateChangedEvent
from shared.domain.events.journey_timeline_events import WagonLocationChangedEvent
from shared.domain.events.journey_timeline_events import WagonState
from shared.domain.events.journey_timeline_events import WagonStateChangedEvent
from shared.domain.events.unified_process_events import ProcessType
from shared.domain.events.unified_process_events import ResourceType


class UnifiedTrackingMixin:
    """Comprehensive mixin for process tracking and state management."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.unified_tracker = get_unified_tracker()
        self.event_bus = event_bus

        # State tracking
        self._wagon_states: dict[str, WagonState] = {}
        self._locomotive_states: dict[str, LocomotiveState] = {}
        self._wagon_locations: dict[str, str] = {}
        self._locomotive_locations: dict[str, str] = {}

    # === WAGON PROCESS TRACKING ===

    def track_wagon_coupling(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # noqa: PLR0913
        self,
        env: Any,
        wagon_ids: list[str],
        location: str,
        duration: float,
        rake_id: str | None = None,
        locomotive_id: str | None = None,
    ) -> Generator[Any]:
        """Track wagon coupling process."""
        start_time = env.now

        # Start process tracking for all wagons
        for wagon_id in wagon_ids:
            self.unified_tracker.start_process(
                resource_id=wagon_id,
                resource_type=ResourceType.WAGON,
                process_type=ProcessType.COUPLING,
                location=location,
                start_time=start_time,
                estimated_duration=duration,
                rake_id=rake_id,
                locomotive_id=locomotive_id,
                wagon_count=len(wagon_ids),
            )

        # Track locomotive process if provided
        if locomotive_id:
            self.unified_tracker.start_process(
                resource_id=locomotive_id,
                resource_type=ResourceType.LOCOMOTIVE,
                process_type=ProcessType.COUPLING,
                location=location,
                start_time=start_time,
                estimated_duration=duration,
                rake_id=rake_id,
                wagon_count=len(wagon_ids),
            )

        # Simulate the process
        yield env.timeout(duration)

        # Complete process tracking
        end_time = env.now
        for wagon_id in wagon_ids:
            self.unified_tracker.complete_process(wagon_id, end_time)

        if locomotive_id:
            self.unified_tracker.complete_process(locomotive_id, end_time)

    def track_wagon_retrofitting(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, env: Any, wagon_ids: list[str], workshop_id: str, duration: float, batch_id: str | None = None
    ) -> Generator[Any]:
        """Track wagon retrofitting process."""
        start_time = env.now

        # Update wagon states to in_workshop
        for wagon_id in wagon_ids:
            self._update_wagon_state(wagon_id, WagonState.IN_WORKSHOP, workshop_id, start_time)

        # Start process tracking
        for wagon_id in wagon_ids:
            self.unified_tracker.start_process(
                resource_id=wagon_id,
                resource_type=ResourceType.WAGON,
                process_type=ProcessType.RETROFITTING,
                location=workshop_id,
                start_time=start_time,
                estimated_duration=duration,
                batch_id=batch_id,
                workshop_id=workshop_id,
                batch_size=len(wagon_ids),
            )

        # Simulate the process
        yield env.timeout(duration)

        # Complete process tracking
        end_time = env.now
        for wagon_id in wagon_ids:
            self.unified_tracker.complete_process(wagon_id, end_time)
            # Update state to retrofitted
            self._update_wagon_state(wagon_id, WagonState.RETROFITTED, workshop_id, end_time)

    def track_wagon_moving(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # noqa: PLR0913
        self,
        env: Any,
        wagon_ids: list[str],
        from_location: str,
        to_location: str,
        duration: float,
        locomotive_id: str | None = None,
    ) -> Generator[Any]:
        """Track wagon moving process."""
        start_time = env.now

        # Start process tracking for wagons
        for wagon_id in wagon_ids:
            self.unified_tracker.start_process(
                resource_id=wagon_id,
                resource_type=ResourceType.WAGON,
                process_type=ProcessType.MOVING,
                location=f'{from_location}->{to_location}',
                start_time=start_time,
                estimated_duration=duration,
                locomotive_id=locomotive_id,
                from_location=from_location,
                to_location=to_location,
                wagon_count=len(wagon_ids),
            )

        # Track locomotive process
        if locomotive_id:
            self._update_locomotive_state(locomotive_id, LocomotiveState.MOVING, from_location, start_time)
            self.unified_tracker.start_process(
                resource_id=locomotive_id,
                resource_type=ResourceType.LOCOMOTIVE,
                process_type=ProcessType.MOVING,
                location=f'{from_location}->{to_location}',
                start_time=start_time,
                estimated_duration=duration,
                from_location=from_location,
                to_location=to_location,
                wagon_count=len(wagon_ids),
            )

        # Simulate the process
        yield env.timeout(duration)

        # Complete process tracking and update locations
        end_time = env.now
        for wagon_id in wagon_ids:
            self.unified_tracker.complete_process(wagon_id, end_time)
            self._update_wagon_location(wagon_id, to_location, end_time)

        if locomotive_id:
            self.unified_tracker.complete_process(locomotive_id, end_time)
            self._update_locomotive_location(locomotive_id, to_location, end_time)
            self._update_locomotive_state(locomotive_id, LocomotiveState.IDLE, to_location, end_time)

    def track_wagon_waiting(self, env: Any, wagon_id: str, location: str, waiting_reason: str = 'queue') -> None:
        """Start tracking wagon waiting process."""
        self._update_wagon_state(wagon_id, WagonState.QUEUED, location, env.now)
        self.unified_tracker.start_process(
            resource_id=wagon_id,
            resource_type=ResourceType.WAGON,
            process_type=ProcessType.WAITING,
            location=location,
            start_time=env.now,
            waiting_reason=waiting_reason,
        )

    def complete_wagon_waiting(self, env: Any, wagon_id: str) -> None:
        """Complete wagon waiting process."""
        self.unified_tracker.complete_process(wagon_id, env.now)

    # === LOCOMOTIVE PROCESS TRACKING ===

    def track_locomotive_maintenance(
        self, env: Any, locomotive_id: str, location: str, duration: float
    ) -> Generator[Any]:
        """Track locomotive maintenance process."""
        start_time = env.now

        self._update_locomotive_state(locomotive_id, LocomotiveState.MAINTENANCE, location, start_time)
        self.unified_tracker.start_process(
            resource_id=locomotive_id,
            resource_type=ResourceType.LOCOMOTIVE,
            process_type=ProcessType.MAINTENANCE,
            location=location,
            start_time=start_time,
            estimated_duration=duration,
        )

        yield env.timeout(duration)

        end_time = env.now
        self.unified_tracker.complete_process(locomotive_id, end_time)
        self._update_locomotive_state(locomotive_id, LocomotiveState.IDLE, location, end_time)

    # === STATE MANAGEMENT ===

    def _update_wagon_state(self, wagon_id: str, new_state: WagonState, location: str, timestamp: float) -> None:
        """Update wagon state and publish event."""
        previous_state = self._wagon_states.get(wagon_id)
        self._wagon_states[wagon_id] = new_state

        if self.event_bus:
            event = WagonStateChangedEvent(
                wagon_id=wagon_id,
                previous_state=previous_state,
                new_state=new_state,
                location=location,
                timestamp=timestamp,
            )
            self.event_bus.publish(event)

    def _update_locomotive_state(
        self, locomotive_id: str, new_state: LocomotiveState, location: str, timestamp: float
    ) -> None:
        """Update locomotive state and publish event."""
        previous_state = self._locomotive_states.get(locomotive_id)
        self._locomotive_states[locomotive_id] = new_state

        if self.event_bus:
            event = LocomotiveStateChangedEvent(
                locomotive_id=locomotive_id,
                previous_state=previous_state,
                new_state=new_state,
                location=location,
                timestamp=timestamp,
            )
            self.event_bus.publish(event)

    def _update_wagon_location(self, wagon_id: str, new_location: str, timestamp: float) -> None:
        """Update wagon location and publish event."""
        previous_location = self._wagon_locations.get(wagon_id)
        self._wagon_locations[wagon_id] = new_location

        if self.event_bus:
            event = WagonLocationChangedEvent(
                wagon_id=wagon_id, previous_location=previous_location, new_location=new_location, timestamp=timestamp
            )
            self.event_bus.publish(event)

    def _update_locomotive_location(self, locomotive_id: str, new_location: str, timestamp: float) -> None:
        """Update locomotive location and publish event."""
        previous_location = self._locomotive_locations.get(locomotive_id)
        self._locomotive_locations[locomotive_id] = new_location

        if self.event_bus:
            event = LocomotiveLocationChangedEvent(
                locomotive_id=locomotive_id,
                previous_location=previous_location,
                new_location=new_location,
                timestamp=timestamp,
            )
            self.event_bus.publish(event)

    # === QUERY METHODS ===

    def get_wagon_state(self, wagon_id: str) -> WagonState | None:
        """Get current wagon state."""
        return self._wagon_states.get(wagon_id)

    def get_locomotive_state(self, locomotive_id: str) -> LocomotiveState | None:
        """Get current locomotive state."""
        return self._locomotive_states.get(locomotive_id)

    def get_wagon_location(self, wagon_id: str) -> str | None:
        """Get current wagon location."""
        return self._wagon_locations.get(wagon_id)

    def get_locomotive_location(self, locomotive_id: str) -> str | None:
        """Get current locomotive location."""
        return self._locomotive_locations.get(locomotive_id)

    def get_active_wagon_process(self, wagon_id: str) -> Any | None:
        """Get active process for wagon."""
        return self.unified_tracker.get_active_process(wagon_id)

    def get_active_locomotive_process(self, locomotive_id: str) -> Any | None:
        """Get active process for locomotive."""
        return self.unified_tracker.get_active_process(locomotive_id)
