"""Process tracking mixin for simulation components."""

from collections.abc import Generator
from typing import Any

from infrastructure.tracking.process_tracker import get_process_tracker
from infrastructure.tracking.state_tracker import LocomotiveState
from infrastructure.tracking.state_tracker import WagonState
from infrastructure.tracking.state_tracker import get_state_tracker
from shared.domain.events.process_tracking_events import ProcessType
from shared.domain.events.process_tracking_events import ResourceType


class ProcessTrackingMixin:
    """Mixin for tracking process operations and state changes."""

    def __init__(self) -> None:
        self.process_tracker = get_process_tracker()
        self.state_tracker = get_state_tracker()

    def track_wagon_coupling(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, env: Any, wagon_ids: list[str], location: str, duration: float, batch_id: str | None = None
    ) -> Generator[Any]:
        """Track wagon coupling process."""
        start_time = env.now

        # Track process duration
        for wagon_id in wagon_ids:
            self.process_tracker.start_process(
                resource_id=wagon_id,
                resource_type=ResourceType.WAGON,
                process_type=ProcessType.COUPLING,
                location=location,
                start_time=start_time,
                estimated_duration=duration,
                batch_id=batch_id,
                wagon_count=len(wagon_ids),
            )

        yield env.timeout(duration)

        # Complete process and record state if needed
        end_time = env.now
        for wagon_id in wagon_ids:
            self.process_tracker.complete_process(wagon_id, end_time)

    def track_wagon_retrofitting(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, env: Any, wagon_ids: list[str], workshop_id: str, duration: float, batch_id: str | None = None
    ) -> Generator[Any]:
        """Track wagon retrofitting process with state changes."""
        start_time = env.now

        # Record state: entering workshop
        for wagon_id in wagon_ids:
            self.state_tracker.record_wagon_state(
                timestamp=start_time,
                wagon_id=wagon_id,
                state=WagonState.IN_WORKSHOP,
                location=workshop_id,
                batch_id=batch_id,
            )

        # Track process duration
        for wagon_id in wagon_ids:
            self.process_tracker.start_process(
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

        yield env.timeout(duration)

        # Complete process and record state: retrofitted
        end_time = env.now
        for wagon_id in wagon_ids:
            self.process_tracker.complete_process(wagon_id, end_time)
            self.state_tracker.record_wagon_state(
                timestamp=end_time,
                wagon_id=wagon_id,
                state=WagonState.RETROFITTED,
                location=workshop_id,
                batch_id=batch_id,
            )

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

        # Track locomotive state if provided
        if locomotive_id:
            self.state_tracker.record_locomotive_state(
                timestamp=start_time, locomotive_id=locomotive_id, state=LocomotiveState.MOVING, location=from_location
            )

        # Track process duration for wagons
        for wagon_id in wagon_ids:
            self.process_tracker.start_process(
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

        # Track locomotive process if provided
        if locomotive_id:
            self.process_tracker.start_process(
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

        yield env.timeout(duration)

        # Complete processes and update locomotive state
        end_time = env.now
        for wagon_id in wagon_ids:
            self.process_tracker.complete_process(wagon_id, end_time)

        if locomotive_id:
            self.process_tracker.complete_process(locomotive_id, end_time)
            self.state_tracker.record_locomotive_state(
                timestamp=end_time, locomotive_id=locomotive_id, state=LocomotiveState.IDLE, location=to_location
            )

    def record_wagon_arrival(self, timestamp: float, wagon_id: str, location: str, train_id: str) -> None:
        """Record wagon arrival state."""
        self.state_tracker.record_wagon_state(
            timestamp=timestamp, wagon_id=wagon_id, state=WagonState.ARRIVED, location=location, train_id=train_id
        )

    def record_wagon_queued(self, timestamp: float, wagon_id: str, location: str) -> None:
        """Record wagon queued state."""
        self.state_tracker.record_wagon_state(
            timestamp=timestamp, wagon_id=wagon_id, state=WagonState.QUEUED, location=location
        )

    def record_wagon_parked(self, timestamp: float, wagon_id: str, location: str) -> None:
        """Record wagon parked state."""
        self.state_tracker.record_wagon_state(
            timestamp=timestamp, wagon_id=wagon_id, state=WagonState.PARKED, location=location
        )
