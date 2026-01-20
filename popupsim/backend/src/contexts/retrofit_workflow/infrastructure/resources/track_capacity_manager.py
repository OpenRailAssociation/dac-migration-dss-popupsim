"""Track Capacity Manager - wraps SimPy Container for meter-based capacity."""

from collections.abc import Callable
from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.ports.resource_port import ResourcePort
import simpy


class TrackCapacityManager(ResourcePort):
    """Manages track capacity using SimPy Container (supports floats!).

    Track capacity is measured in METERS (float), not wagon count.
    SimPy Container handles float values perfectly and provides:
    - Automatic blocking when track full
    - Automatic queuing of waiting wagons
    - Built-in level tracking

    Example:
        track = TrackCapacityManager(env, 'collection', 500.5)  # 500.5 meters
        yield from track.add_wagons([wagon1, wagon2])  # Blocks if not enough space
        yield from track.remove_wagons([wagon1])  # Frees space
    """

    def __init__(
        self,
        env: simpy.Environment,
        track_id: str,
        capacity_meters: float,
        event_publisher: Callable[[ResourceStateChangeEvent], None] | None = None,
    ):
        """Initialize track capacity manager.

        Args:
            env: SimPy environment
            track_id: Track identifier
            capacity_meters: Total track capacity in METERS (float)
            event_publisher: Optional callback to publish events
        """
        self.env = env
        self.track_id = track_id
        self.capacity_meters = capacity_meters
        self.event_publisher = event_publisher

        # Level represents occupied meters
        self.container: simpy.Container = simpy.Container(
            env,
            capacity=capacity_meters,
            init=0.0,
        )

        # Track wagons on this track (for domain logic)
        self.wagons: list[Wagon] = []

    def get_available_capacity(self) -> float:
        """Get available capacity in meters.

        Returns
        -------
            Available space in meters (float)
        """
        return self.capacity_meters - self.container.level

    def get_occupied_capacity(self) -> float:
        """Get occupied capacity in meters.

        Returns
        -------
            Occupied space in meters (float)
        """
        return self.container.level

    def get_utilization(self) -> float:
        """Get track utilization percentage.

        Returns
        -------
            Utilization as percentage (0-100)
        """
        if self.capacity_meters == 0:
            return 0.0

        return (self.container.level / self.capacity_meters) * 100.0

    def can_fit_wagons(self, wagons: list[Wagon]) -> bool:
        """Check if wagons can fit on track (non-blocking check).

        Args:
            wagons: Wagons to check

        Returns
        -------
            True if wagons fit in available capacity
        """
        total_length = sum(w.length for w in wagons)
        return total_length <= self.get_available_capacity()  # type: ignore[no-any-return]

    def add_wagons(self, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Add wagons to track (blocks if not enough capacity).

        This is the CORE operation - SimPy handles all the complexity:
        - Calculates total length needed
        - Blocks if not enough space
        - Automatically queues if track full
        - Updates capacity when space available

        Args:
            wagons: Wagons to add to track

        Yields
        ------
            SimPy event (blocks until space available)
        """
        # Calculate total length needed (float!)
        total_length = sum(w.length for w in wagons)
        print(
            f't={self.env.now}: TrackCapacityManager.add_wagons: '
            f'adding {total_length}m, current level={self.container.level}'
        )

        # Capture state before
        used_before = self.container.level

        # Request space - BLOCKS if not enough capacity!
        # SimPy automatically queues and waits for space
        yield self.container.put(total_length)

        print(
            f't={self.env.now}: TrackCapacityManager.add_wagons: '
            f'added {total_length}m, new level={self.container.level}'
        )

        # Capture state after
        used_after = self.container.level

        # Publish event
        if self.event_publisher:
            self.event_publisher(
                ResourceStateChangeEvent(
                    timestamp=self.env.now,
                    resource_type='track',
                    resource_id=self.track_id,
                    change_type='capacity_reserved',
                    capacity=self.capacity_meters,
                    used_before=used_before,
                    used_after=used_after,
                    change_amount=total_length,
                    triggered_by=f'batch_{len(wagons)}_wagons',
                )
            )

        # Space acquired - add wagons
        self.wagons.extend(wagons)
        for wagon in wagons:
            wagon.move_to(self.track_id)

    def remove_wagons(self, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Remove wagons from track (frees capacity).

        Args:
            wagons: Wagons to remove from track

        Yields
        ------
            SimPy event
        """
        # Calculate total length to free (float!)
        total_length = sum(w.length for w in wagons)
        print(
            f't={self.env.now}: TrackCapacityManager.remove_wagons: '
            f'removing {total_length}m, current level={self.container.level}'
        )

        # Capture state before
        used_before = self.container.level

        # Free space - automatically unblocks waiting processes!
        yield self.container.get(total_length)

        print(
            f't={self.env.now}: TrackCapacityManager.remove_wagons: '
            f'removed {total_length}m, new level={self.container.level}'
        )

        # Capture state after
        used_after = self.container.level

        # Publish event
        if self.event_publisher:
            self.event_publisher(
                ResourceStateChangeEvent(
                    timestamp=self.env.now,
                    resource_type='track',
                    resource_id=self.track_id,
                    change_type='capacity_released',
                    capacity=self.capacity_meters,
                    used_before=used_before,
                    used_after=used_after,
                    change_amount=-total_length,
                    triggered_by=f'batch_{len(wagons)}_wagons',
                )
            )

        # Remove wagons
        for wagon in wagons:
            if wagon in self.wagons:
                self.wagons.remove(wagon)

    def get_queue_length(self) -> int:
        """Get queue length (number of wagons on track).

        Returns
        -------
            Number of wagons on track
        """
        return len(self.wagons)

    def get_wagon_count(self) -> int:
        """Get number of wagons on track.

        Returns
        -------
            Number of wagons
        """
        return len(self.wagons)

    def get_metrics(self) -> dict[str, Any]:
        """Get track capacity metrics.

        Returns
        -------
            Dict with capacity metrics
        """
        return {
            'track_id': self.track_id,
            'capacity_meters': self.capacity_meters,
            'occupied_meters': self.get_occupied_capacity(),
            'available_meters': self.get_available_capacity(),
            'utilization_percent': self.get_utilization(),
            'wagon_count': self.get_wagon_count(),
        }


class TrackResourceManager:
    """Manages multiple tracks with float-based capacity.

    This replaces the scattered track capacity logic in railway_context.py
    with a clean, centralized manager.

    Example:
        manager = TrackResourceManager(env, {
            'collection': 500.0,
            'retrofit': 300.5,
            'parking': 1000.75,
        })

        collection = manager.get_track('collection')
        yield from collection.add_wagons([wagon1, wagon2])
    """

    def __init__(
        self,
        env: simpy.Environment,
        tracks: dict[str, float],
        event_publisher: Callable[[ResourceStateChangeEvent], None] | None = None,
    ):
        """Initialize track resource manager.

        Args:
            env: SimPy environment
            tracks: Dict mapping track_id -> capacity_meters (float)
            event_publisher: Optional callback to publish events
        """
        self.env = env
        self.tracks = {
            track_id: TrackCapacityManager(env, track_id, capacity, event_publisher)
            for track_id, capacity in tracks.items()
        }

    def get_track(self, track_id: str) -> TrackCapacityManager | None:
        """Get track manager by ID.

        Args:
            track_id: Track identifier

        Returns
        -------
            Track manager or None if not found
        """
        return self.tracks.get(track_id)

    def get_available_capacity(self, track_id: str) -> float:
        """Get available capacity for track.

        Args:
            track_id: Track identifier

        Returns
        -------
            Available capacity in meters (float)
        """
        track = self.tracks.get(track_id)
        return track.get_available_capacity() if track else 0.0

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get capacity metrics for all tracks.

        Returns
        -------
            Dict mapping track_id -> metrics
        """
        return {track_id: track.get_metrics() for track_id, track in self.tracks.items()}
