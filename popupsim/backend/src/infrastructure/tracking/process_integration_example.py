"""Example integration of process tracking in simulation workflows."""

from collections.abc import Generator
from typing import Any

from infrastructure.tracking.wagon_process_tracker import get_process_tracker


class ProcessTrackingMixin:
    """Mixin to add process tracking capabilities to simulation components."""

    def __init__(self) -> None:
        self.process_tracker = get_process_tracker()

    def track_coupling_process(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, env: Any, wagon_ids: list[str], location: str, duration: float, rake_id: str = ''
    ) -> Generator[Any]:
        """Track coupling process for multiple wagons."""
        start_time = env.now

        # Start tracking for all wagons
        for wagon_id in wagon_ids:
            self.process_tracker.start_process(
                wagon_id=wagon_id,
                process_type='coupling',
                location=location,
                start_time=start_time,
                rake_id=rake_id,
                wagon_count=len(wagon_ids),
            )

        # Simulate the coupling process
        yield env.timeout(duration)

        # Complete tracking for all wagons
        end_time = env.now
        for wagon_id in wagon_ids:
            self.process_tracker.complete_process(wagon_id, end_time)

    def track_decoupling_process(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, env: Any, wagon_ids: list[str], location: str, duration: float, rake_id: str = ''
    ) -> Generator[Any]:
        """Track decoupling process for multiple wagons."""
        start_time = env.now

        # Start tracking for all wagons
        for wagon_id in wagon_ids:
            self.process_tracker.start_process(
                wagon_id=wagon_id,
                process_type='decoupling',
                location=location,
                start_time=start_time,
                rake_id=rake_id,
                wagon_count=len(wagon_ids),
            )

        # Simulate the decoupling process
        yield env.timeout(duration)

        # Complete tracking for all wagons
        end_time = env.now
        for wagon_id in wagon_ids:
            self.process_tracker.complete_process(wagon_id, end_time)

    def track_retrofitting_process(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, env: Any, wagon_ids: list[str], workshop_id: str, duration: float, batch_id: str | None = None
    ) -> Generator[Any]:
        """Track retrofitting process for wagons."""
        start_time = env.now

        # Start tracking for all wagons
        for wagon_id in wagon_ids:
            self.process_tracker.start_process(
                wagon_id=wagon_id,
                process_type='retrofitting',
                location=workshop_id,
                start_time=start_time,
                batch_id=batch_id,
                batch_size=len(wagon_ids),
            )

        # Simulate the retrofitting process
        yield env.timeout(duration)

        # Complete tracking for all wagons
        end_time = env.now
        for wagon_id in wagon_ids:
            self.process_tracker.complete_process(wagon_id, end_time)

    def track_moving_process(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # noqa: PLR0913
        self,
        env: Any,
        wagon_ids: list[str],
        from_location: str,
        to_location: str,
        duration: float,
        locomotive_id: str = '',
    ) -> Generator[Any]:
        """Track moving process for wagons."""
        start_time = env.now

        # Start tracking for all wagons
        for wagon_id in wagon_ids:
            self.process_tracker.start_process(
                wagon_id=wagon_id,
                process_type='moving',
                location=f'{from_location}->{to_location}',
                start_time=start_time,
                from_location=from_location,
                to_location=to_location,
                locomotive_id=locomotive_id,
                wagon_count=len(wagon_ids),
            )

        # Simulate the moving process
        yield env.timeout(duration)

        # Complete tracking for all wagons
        end_time = env.now
        for wagon_id in wagon_ids:
            self.process_tracker.complete_process(wagon_id, end_time)

    def track_parking_process(
        self, env: Any, wagon_ids: list[str], parking_track: str, duration: float
    ) -> Generator[Any]:
        """Track parking process for wagons."""
        start_time = env.now

        # Start tracking for all wagons
        for wagon_id in wagon_ids:
            self.process_tracker.start_process(
                wagon_id=wagon_id, process_type='parking', location=parking_track, start_time=start_time
            )

        # Simulate the parking process
        yield env.timeout(duration)

        # Complete tracking for all wagons
        end_time = env.now
        for wagon_id in wagon_ids:
            self.process_tracker.complete_process(wagon_id, end_time)

    def track_waiting_process(self, env: Any, wagon_id: str, location: str, waiting_reason: str = 'queue') -> None:
        """Start tracking waiting process for a wagon."""
        self.process_tracker.start_process(
            wagon_id=wagon_id,
            process_type='waiting',
            location=location,
            start_time=env.now,
            waiting_reason=waiting_reason,
        )

    def complete_waiting_process(self, env: Any, wagon_id: str) -> None:
        """Complete waiting process for a wagon."""
        self.process_tracker.complete_process(wagon_id, env.now)


# Example usage in a workshop simulation component
class ExampleWorkshopWithProcessTracking(ProcessTrackingMixin):
    """Example workshop component with integrated process tracking."""

    def __init__(self, workshop_id: str) -> None:
        super().__init__()
        self.workshop_id = workshop_id

    def process_wagon_batch(self, env: Any, wagon_ids: list[str], batch_id: str) -> Generator[Any]:
        """Process a batch of wagons with detailed tracking."""
        # 1. Track waiting for workshop availability
        for wagon_id in wagon_ids:
            self.track_waiting_process(env, wagon_id, self.workshop_id, 'workshop_queue')

        # Simulate waiting for workshop availability
        yield env.timeout(5.0)  # 5 minutes wait

        # Complete waiting
        for wagon_id in wagon_ids:
            self.complete_waiting_process(env, wagon_id)

        # 2. Track moving wagons into workshop
        yield from self.track_moving_process(
            env, wagon_ids, 'retrofit_track', self.workshop_id, duration=3.0, locomotive_id='LOCO_01'
        )

        # 3. Track coupling wagons in workshop
        yield from self.track_coupling_process(env, wagon_ids, self.workshop_id, duration=2.0, rake_id=batch_id)

        # 4. Track actual retrofitting
        yield from self.track_retrofitting_process(env, wagon_ids, self.workshop_id, duration=45.0, batch_id=batch_id)

        # 5. Track decoupling after retrofit
        yield from self.track_decoupling_process(env, wagon_ids, self.workshop_id, duration=2.0, rake_id=batch_id)

        # 6. Track moving to parking
        yield from self.track_moving_process(
            env, wagon_ids, self.workshop_id, 'parking_track', duration=4.0, locomotive_id='LOCO_01'
        )

        # 7. Track final parking
        yield from self.track_parking_process(env, wagon_ids, 'parking_track', duration=1.0)
