"""Performance benchmark for ResourcePool utilization calculation."""

from typing import Any

import pytest


class MockSim:
    """Mock simulation for testing."""

    def __init__(self) -> None:
        self._time = 0.0

    def current_time(self) -> float:
        """Get current simulation time."""
        return self._time

    def set_time(self, time: float) -> None:
        """Set simulation time."""
        self._time = time

    def create_store(self, capacity: int | None = None) -> Any:
        """Create mock store."""
        return MockStore()


class MockStore:
    """Mock store for testing."""

    def __init__(self) -> None:
        self.items: list[Any] = []

    def put(self, item: Any) -> None:
        """Put item in store."""
        self.items.append(item)


class MockResource:
    """Mock resource for testing."""

    def __init__(self, resource_id: str) -> None:
        self.id = resource_id
        self.status = 'available'
        self.track: str | None = None


def create_old_resource_pool(sim: MockSim, resources: list[MockResource]) -> Any:
    """Create resource pool with OLD implementation (O(n*m))."""

    class OldResourcePool:
        """Old implementation with quadratic complexity."""

        def __init__(self, sim: MockSim, resources: list[MockResource]) -> None:
            self.sim = sim
            self.all_resources = {r.id: r for r in resources}
            self.allocated: dict[str, float] = {}
            self.allocation_history: list[tuple[float, str, str, str | None]] = []

        def track_allocation(self, resource_id: str) -> None:
            """Track allocation."""
            self.allocated[resource_id] = self.sim.current_time()
            self.allocation_history.append((self.sim.current_time(), resource_id, 'allocated', None))

        def track_release(self, resource_id: str) -> None:
            """Track release."""
            if resource_id in self.allocated:
                del self.allocated[resource_id]
                self.allocation_history.append((self.sim.current_time(), resource_id, 'released', None))

        def get_utilization(self, total_time: float) -> dict[str, float]:
            """OLD: O(n*m) implementation."""
            utilization = {}
            for resource_id in self.all_resources:
                allocated_time = 0.0
                last_alloc = None

                for time, rid, action, _ in self.allocation_history:  # O(m) scan
                    if rid == resource_id:
                        if action == 'allocated':
                            last_alloc = time
                        elif action == 'released' and last_alloc is not None:
                            allocated_time += time - last_alloc
                            last_alloc = None

                if resource_id in self.allocated:
                    allocated_time += total_time - self.allocated[resource_id]

                utilization[resource_id] = (allocated_time / total_time * 100) if total_time > 0 else 0.0

            return utilization

    return OldResourcePool(sim, resources)


def create_new_resource_pool(sim: MockSim, resources: list[MockResource]) -> Any:
    """Create resource pool with NEW implementation (O(n))."""

    class NewResourcePool:
        """New implementation with linear complexity."""

        def __init__(self, sim: MockSim, resources: list[MockResource]) -> None:
            self.sim = sim
            self.all_resources = {r.id: r for r in resources}
            self.allocated: dict[str, float] = {}
            self.total_allocated_time: dict[str, float] = {r.id: 0.0 for r in resources}

        def track_allocation(self, resource_id: str) -> None:
            """Track allocation."""
            self.allocated[resource_id] = self.sim.current_time()

        def track_release(self, resource_id: str) -> None:
            """Track release."""
            if resource_id in self.allocated:
                allocation_duration = self.sim.current_time() - self.allocated[resource_id]
                self.total_allocated_time[resource_id] += allocation_duration
                del self.allocated[resource_id]

        def get_utilization(self, total_time: float) -> dict[str, float]:
            """NEW: O(n) implementation."""
            utilization = {}
            for resource_id in self.all_resources:
                allocated_time = self.total_allocated_time[resource_id]
                if resource_id in self.allocated:
                    allocated_time += self.sim.current_time() - self.allocated[resource_id]
                utilization[resource_id] = (allocated_time / total_time * 100) if total_time > 0 else 0.0
            return utilization

    return NewResourcePool(sim, resources)


def setup_pools(num_resources: int, num_events: int) -> tuple[Any, Any, float]:
    """Setup pools with simulated allocation/release cycles."""
    sim = MockSim()
    resources = [MockResource(f'resource_{i}') for i in range(num_resources)]
    old_pool = create_old_resource_pool(sim, resources)
    new_pool = create_new_resource_pool(sim, resources)

    for i in range(num_events):
        resource_id = f'resource_{i % num_resources}'
        sim.set_time(float(i * 2))
        old_pool.track_allocation(resource_id)
        new_pool.track_allocation(resource_id)
        sim.set_time(float(i * 2 + 1))
        old_pool.track_release(resource_id)
        new_pool.track_release(resource_id)

    return old_pool, new_pool, float(num_events * 2)


@pytest.mark.benchmark(group='old-implementation')
@pytest.mark.parametrize('num_resources,num_events', [(5, 100), (10, 1000), (20, 10000)])
def test_old_implementation(benchmark: Any, num_resources: int, num_events: int) -> None:
    """Benchmark OLD O(n*m) implementation."""
    old_pool, _, total_time = setup_pools(num_resources, num_events)
    result = benchmark(old_pool.get_utilization, total_time)
    assert len(result) == num_resources


@pytest.mark.benchmark(group='new-implementation')
@pytest.mark.parametrize('num_resources,num_events', [(5, 100), (10, 1000), (20, 10000)])
def test_new_implementation(benchmark: Any, num_resources: int, num_events: int) -> None:
    """Benchmark NEW O(n) implementation."""
    _, new_pool, total_time = setup_pools(num_resources, num_events)
    result = benchmark(new_pool.get_utilization, total_time)
    assert len(result) == num_resources


@pytest.mark.skip(reason='Correctness test, not a benchmark')
def test_resource_pool_correctness() -> None:
    """Verify new implementation produces correct results."""
    sim = MockSim()
    resources = [MockResource(f'loco_{i}') for i in range(3)]
    pool = create_new_resource_pool(sim, resources)

    sim.set_time(0.0)
    pool.track_allocation('loco_0')
    sim.set_time(10.0)
    pool.track_release('loco_0')
    sim.set_time(20.0)
    pool.track_allocation('loco_0')
    sim.set_time(30.0)
    pool.track_release('loco_0')

    sim.set_time(5.0)
    pool.track_allocation('loco_1')
    sim.set_time(15.0)
    pool.track_release('loco_1')

    utilization = pool.get_utilization(30.0)

    assert abs(utilization['loco_0'] - 66.67) < 0.1
    assert abs(utilization['loco_1'] - 33.33) < 0.1
    assert abs(utilization['loco_2'] - 0.0) < 0.1


@pytest.mark.skip(reason='Correctness test, not a benchmark')
def test_resource_pool_still_allocated() -> None:
    """Test utilization calculation with resources still allocated."""
    sim = MockSim()
    resources = [MockResource('loco_0')]
    pool = create_new_resource_pool(sim, resources)

    sim.set_time(0.0)
    pool.track_allocation('loco_0')
    sim.set_time(100.0)

    utilization = pool.get_utilization(100.0)
    assert abs(utilization['loco_0'] - 100.0) < 0.1


def test_correctness_comparison() -> None:
    """Verify OLD and NEW produce identical results."""
    old_pool, new_pool, total_time = setup_pools(10, 100)
    old_result = old_pool.get_utilization(total_time)
    new_result = new_pool.get_utilization(total_time)

    assert len(old_result) == len(new_result)
    for resource_id in old_result:
        assert abs(old_result[resource_id] - new_result[resource_id]) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--benchmark-only', '--benchmark-compare'])
