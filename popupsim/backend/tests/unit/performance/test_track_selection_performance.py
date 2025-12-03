"""Benchmark for track selection optimization."""

import pytest
from workshop_operations.domain.entities.track import Track
from workshop_operations.domain.entities.track import TrackType

from configuration.domain.models.topology import Topology


class TrackCapacityManagerBaseline:
    """Baseline implementation with repeated dict lookups."""

    def __init__(self, tracks: list[Track], topology: Topology) -> None:
        self.track_capacities: dict[str, float] = {}
        self.current_occupancy: dict[str, float] = {}
        self.collection_tracks: list[str] = []

        for track in tracks:
            if track.type == TrackType.COLLECTION:
                total_length = sum(topology.get_edge_length(edge_id) for edge_id in track.edges)
                self.track_capacities[track.id] = total_length * 0.75
                self.current_occupancy[track.id] = 0.0
                self.collection_tracks.append(track.id)

    def can_add_wagon(self, track_id: str, wagon_length: float) -> bool:
        return self.current_occupancy[track_id] + wagon_length <= self.track_capacities[track_id]

    def select_track_baseline(self, wagon_length: float) -> str | None:
        available_tracks = [t for t in self.collection_tracks if self.can_add_wagon(t, wagon_length)]
        if not available_tracks:
            return None
        return min(available_tracks, key=lambda t: self.current_occupancy[t] / self.track_capacities[t])


class TrackCapacityManagerOptimized:
    """Optimized implementation with cached ratios."""

    def __init__(self, tracks: list[Track], topology: Topology) -> None:
        self.track_capacities: dict[str, float] = {}
        self.current_occupancy: dict[str, float] = {}
        self.collection_tracks: list[str] = []

        for track in tracks:
            if track.type == TrackType.COLLECTION:
                total_length = sum(topology.get_edge_length(edge_id) for edge_id in track.edges)
                self.track_capacities[track.id] = total_length * 0.75
                self.current_occupancy[track.id] = 0.0
                self.collection_tracks.append(track.id)

    def can_add_wagon(self, track_id: str, wagon_length: float) -> bool:
        return self.current_occupancy[track_id] + wagon_length <= self.track_capacities[track_id]

    def select_track_optimized(self, wagon_length: float) -> str | None:
        available_with_ratio = [
            (t, self.current_occupancy[t] / self.track_capacities[t])
            for t in self.collection_tracks
            if self.can_add_wagon(t, wagon_length)
        ]
        if not available_with_ratio:
            return None
        return min(available_with_ratio, key=lambda x: x[1])[0]


def create_test_tracks(num_tracks: int) -> tuple[list[Track], Topology]:
    """Create test tracks and topology."""
    tracks = []
    topology = Topology()

    for i in range(num_tracks):
        track_id = f'track_{i}'
        edge_id = f'edge_{i}'
        tracks.append(Track(id=track_id, type=TrackType.COLLECTION, edges=[edge_id]))
        topology.edge_lengths[edge_id] = 100.0

    return tracks, topology


@pytest.mark.benchmark(group='track-selection')
def test_baseline_small(benchmark: pytest.fixture) -> None:
    """Benchmark baseline with 5 tracks, 100 selections."""
    tracks, topology = create_test_tracks(5)
    manager = TrackCapacityManagerBaseline(tracks, topology)

    def run() -> None:
        for _ in range(100):
            manager.select_track_baseline(10.0)

    benchmark(run)


@pytest.mark.benchmark(group='track-selection')
def test_optimized_small(benchmark: pytest.fixture) -> None:
    """Benchmark optimized with 5 tracks, 100 selections."""
    tracks, topology = create_test_tracks(5)
    manager = TrackCapacityManagerOptimized(tracks, topology)

    def run() -> None:
        for _ in range(100):
            manager.select_track_optimized(10.0)

    benchmark(run)


@pytest.mark.benchmark(group='track-selection')
def test_baseline_medium(benchmark: pytest.fixture) -> None:
    """Benchmark baseline with 10 tracks, 1000 selections."""
    tracks, topology = create_test_tracks(10)
    manager = TrackCapacityManagerBaseline(tracks, topology)

    def run() -> None:
        for _ in range(1000):
            manager.select_track_baseline(10.0)

    benchmark(run)


@pytest.mark.benchmark(group='track-selection')
def test_optimized_medium(benchmark: pytest.fixture) -> None:
    """Benchmark optimized with 10 tracks, 1000 selections."""
    tracks, topology = create_test_tracks(10)
    manager = TrackCapacityManagerOptimized(tracks, topology)

    def run() -> None:
        for _ in range(1000):
            manager.select_track_optimized(10.0)

    benchmark(run)


@pytest.mark.benchmark(group='track-selection')
def test_baseline_large(benchmark: pytest.fixture) -> None:
    """Benchmark baseline with 20 tracks, 5000 selections."""
    tracks, topology = create_test_tracks(20)
    manager = TrackCapacityManagerBaseline(tracks, topology)

    def run() -> None:
        for _ in range(5000):
            manager.select_track_baseline(10.0)

    benchmark(run)


@pytest.mark.benchmark(group='track-selection')
def test_optimized_large(benchmark: pytest.fixture) -> None:
    """Benchmark optimized with 20 tracks, 5000 selections."""
    tracks, topology = create_test_tracks(20)
    manager = TrackCapacityManagerOptimized(tracks, topology)

    def run() -> None:
        for _ in range(5000):
            manager.select_track_optimized(10.0)

    benchmark(run)
