"""Performance benchmark for batch collection with timeouts (Issue #7)."""

from collections.abc import Generator
from typing import Any

import pytest
import simpy


class MockWagon:
    """Mock wagon for testing."""

    def __init__(self, wagon_id: str, length: float = 15.0) -> None:
        self.id = wagon_id
        self.length = length
        self.coupler_type = 'DAC'


def create_test_scenario(
    env: simpy.Environment, batch_size: int, wagon_arrival_pattern: str, num_wagons: int
) -> tuple[simpy.Store, list[float]]:
    """Create test scenario with wagons arriving at different rates."""
    completed_store = simpy.Store(env)
    arrival_times: list[float] = []

    def wagon_producer() -> Generator[Any, Any]:
        """Produce wagons according to pattern."""
        if wagon_arrival_pattern == 'burst':
            # All wagons arrive at once
            for i in range(num_wagons):
                wagon = MockWagon(f'wagon_{i}')
                yield completed_store.put(wagon)
                arrival_times.append(env.now)

        elif wagon_arrival_pattern == 'steady':
            # Wagons arrive every 2 time units
            for i in range(num_wagons):
                wagon = MockWagon(f'wagon_{i}')
                yield completed_store.put(wagon)
                arrival_times.append(env.now)
                yield env.timeout(2.0)

        elif wagon_arrival_pattern == 'slow':
            # Wagons arrive every 10 time units (slower than timeout)
            for i in range(num_wagons):
                wagon = MockWagon(f'wagon_{i}')
                yield completed_store.put(wagon)
                arrival_times.append(env.now)
                yield env.timeout(10.0)

        elif wagon_arrival_pattern == 'mixed':
            # First batch arrives quickly, then slow
            for i in range(min(batch_size, num_wagons)):
                wagon = MockWagon(f'wagon_{i}')
                yield completed_store.put(wagon)
                arrival_times.append(env.now)
                yield env.timeout(0.5)
            for i in range(batch_size, num_wagons):
                wagon = MockWagon(f'wagon_{i}')
                yield completed_store.put(wagon)
                arrival_times.append(env.now)
                yield env.timeout(8.0)

    env.process(wagon_producer())
    return completed_store, arrival_times


# CURRENT IMPLEMENTATION (with 5s timeout)
def batch_collector_current(
    env: simpy.Environment, completed_store: simpy.Store, batch_size: int
) -> Generator[Any, Any, list[MockWagon]]:
    """CURRENT: Batch collection with 5s timeout per additional wagon."""
    batch: list[MockWagon] = []

    wagon: MockWagon = yield completed_store.get()
    batch.append(wagon)

    for _ in range(batch_size - 1):
        if len(completed_store.items) > 0:
            additional_wagon: MockWagon = yield completed_store.get()
            batch.append(additional_wagon)
        else:
            try:
                timeout_event = env.timeout(5.0)
                get_event = completed_store.get()
                result = yield timeout_event | get_event
                if get_event in result:
                    batch.append(result[get_event])
                else:
                    break
            except (RuntimeError, KeyError, StopIteration):
                break

    return batch


# OPTION 1: Immediate break
def batch_collector_option1(
    env: simpy.Environment, completed_store: simpy.Store, batch_size: int
) -> Generator[Any, Any, list[MockWagon]]:
    """OPTION 1: Immediate break when queue empty."""
    batch: list[MockWagon] = []

    wagon: MockWagon = yield completed_store.get()
    batch.append(wagon)

    for _ in range(batch_size - 1):
        if len(completed_store.items) > 0:
            additional_wagon: MockWagon = yield completed_store.get()
            batch.append(additional_wagon)
        else:
            break

    return batch


# OPTION 2: Single configurable timeout
def batch_collector_option2(
    env: simpy.Environment, completed_store: simpy.Store, batch_size: int, timeout: float = 5.0
) -> Generator[Any, Any, list[MockWagon]]:
    """OPTION 2: Single timeout for entire batch collection."""
    batch: list[MockWagon] = []

    wagon: MockWagon = yield completed_store.get()
    batch.append(wagon)

    timeout_event = env.timeout(timeout)
    for _ in range(batch_size - 1):
        if len(completed_store.items) > 0:
            additional_wagon: MockWagon = yield completed_store.get()
            batch.append(additional_wagon)
        else:
            get_event = completed_store.get()
            result = yield timeout_event | get_event
            if get_event in result:
                batch.append(result[get_event])
            else:
                break

    return batch


# OPTION 3: Hybrid with short wait
def batch_collector_option3(
    env: simpy.Environment, completed_store: simpy.Store, batch_size: int
) -> Generator[Any, Any, list[MockWagon]]:
    """OPTION 3: Immediate check first, then short wait if needed."""
    batch: list[MockWagon] = []
    max_immediate_checks = 3
    short_wait = 0.5

    wagon: MockWagon = yield completed_store.get()
    batch.append(wagon)

    for i in range(batch_size - 1):
        if len(completed_store.items) > 0:
            additional_wagon: MockWagon = yield completed_store.get()
            batch.append(additional_wagon)
        elif i < max_immediate_checks:
            break
        else:
            try:
                timeout_event = env.timeout(short_wait)
                get_event = completed_store.get()
                result = yield timeout_event | get_event
                if get_event in result:
                    batch.append(result[get_event])
                else:
                    break
            except (RuntimeError, KeyError, StopIteration):
                break

    return batch


def run_simulation(
    collector_func: Any, batch_size: int, wagon_arrival_pattern: str, num_wagons: int, timeout: float = 5.0
) -> dict[str, Any]:
    """Run simulation and collect metrics."""
    env = simpy.Environment()
    completed_store, arrival_times = create_test_scenario(env, batch_size, wagon_arrival_pattern, num_wagons)

    batches: list[list[MockWagon]] = []
    batch_times: list[float] = []

    def batch_processor() -> Generator[Any, Any]:
        """Process batches until all wagons collected."""
        wagons_collected = 0
        while wagons_collected < num_wagons:
            start_time = env.now
            if collector_func == batch_collector_option2:
                batch = yield env.process(collector_func(env, completed_store, batch_size, timeout))
            else:
                batch = yield env.process(collector_func(env, completed_store, batch_size))
            batch_times.append(env.now - start_time)
            batches.append(batch)
            wagons_collected += len(batch)

    env.process(batch_processor())
    env.run()

    return {
        'total_time': env.now,
        'num_batches': len(batches),
        'batch_sizes': [len(b) for b in batches],
        'avg_batch_size': sum(len(b) for b in batches) / len(batches) if batches else 0,
        'batch_times': batch_times,
        'avg_batch_time': sum(batch_times) / len(batch_times) if batch_times else 0,
    }


# Benchmark tests
@pytest.mark.benchmark(group='burst-arrivals')
@pytest.mark.parametrize(
    'collector_name,collector_func',
    [
        ('current', batch_collector_current),
        ('option1', batch_collector_option1),
        ('option2', batch_collector_option2),
        ('option3', batch_collector_option3),
    ],
)
def test_burst_arrivals(benchmark: Any, collector_name: str, collector_func: Any) -> None:
    """Benchmark with burst arrivals (all wagons available immediately)."""
    result = benchmark(run_simulation, collector_func, batch_size=5, wagon_arrival_pattern='burst', num_wagons=20)
    assert result['num_batches'] == 4
    assert sum(result['batch_sizes']) == 20


@pytest.mark.benchmark(group='steady-arrivals')
@pytest.mark.parametrize(
    'collector_name,collector_func',
    [
        ('current', batch_collector_current),
        ('option1', batch_collector_option1),
        ('option2', batch_collector_option2),
        ('option3', batch_collector_option3),
    ],
)
def test_steady_arrivals(benchmark: Any, collector_name: str, collector_func: Any) -> None:
    """Benchmark with steady arrivals (wagons arrive every 2 time units)."""
    result = benchmark(run_simulation, collector_func, batch_size=5, wagon_arrival_pattern='steady', num_wagons=20)
    assert sum(result['batch_sizes']) <= 20  # May timeout before all collected


@pytest.mark.benchmark(group='slow-arrivals')
@pytest.mark.parametrize(
    'collector_name,collector_func',
    [
        ('current', batch_collector_current),
        ('option1', batch_collector_option1),
        ('option2', batch_collector_option2),
        ('option3', batch_collector_option3),
    ],
)
def test_slow_arrivals(benchmark: Any, collector_name: str, collector_func: Any) -> None:
    """Benchmark with slow arrivals (wagons arrive every 10 time units)."""
    result = benchmark(run_simulation, collector_func, batch_size=5, wagon_arrival_pattern='slow', num_wagons=10)
    assert sum(result['batch_sizes']) <= 10  # May timeout before all collected


@pytest.mark.benchmark(group='mixed-arrivals')
@pytest.mark.parametrize(
    'collector_name,collector_func',
    [
        ('current', batch_collector_current),
        ('option1', batch_collector_option1),
        ('option2', batch_collector_option2),
        ('option3', batch_collector_option3),
    ],
)
def test_mixed_arrivals(benchmark: Any, collector_name: str, collector_func: Any) -> None:
    """Benchmark with mixed arrivals (burst then slow)."""
    result = benchmark(run_simulation, collector_func, batch_size=5, wagon_arrival_pattern='mixed', num_wagons=15)
    assert sum(result['batch_sizes']) <= 15  # May timeout before all collected


# Detailed analysis tests (not benchmarked)
@pytest.mark.parametrize(
    'collector_name,collector_func',
    [
        ('current', batch_collector_current),
        ('option1', batch_collector_option1),
        ('option2', batch_collector_option2),
        ('option3', batch_collector_option3),
    ],
)
def test_detailed_metrics(collector_name: str, collector_func: Any) -> None:
    """Detailed metrics for each option."""
    patterns = ['burst', 'steady', 'slow', 'mixed']

    print(f'\n\n=== {collector_name.upper()} ===')
    for pattern in patterns:
        result = run_simulation(collector_func, batch_size=5, wagon_arrival_pattern=pattern, num_wagons=20)
        print(f'\n{pattern.upper()} Pattern:')
        print(f'  Total time: {result["total_time"]:.2f}')
        print(f'  Num batches: {result["num_batches"]}')
        print(f'  Batch sizes: {result["batch_sizes"]}')
        print(f'  Avg batch size: {result["avg_batch_size"]:.2f}')
        print(f'  Avg batch time: {result["avg_batch_time"]:.2f}')


def test_option2_timeout_sensitivity() -> None:
    """Test Option 2 with different timeout values."""
    timeouts = [0.0, 1.0, 5.0, 10.0]

    print('\n\n=== OPTION 2 TIMEOUT SENSITIVITY ===')
    for timeout in timeouts:
        result = run_simulation(
            batch_collector_option2, batch_size=5, wagon_arrival_pattern='steady', num_wagons=20, timeout=timeout
        )
        print(f'\nTimeout={timeout}s:')
        print(f'  Total time: {result["total_time"]:.2f}')
        print(f'  Avg batch size: {result["avg_batch_size"]:.2f}')
        print(f'  Num batches: {result["num_batches"]}')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--benchmark-only'])
