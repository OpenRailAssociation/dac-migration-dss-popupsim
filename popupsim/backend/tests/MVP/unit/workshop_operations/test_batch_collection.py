"""Unit tests for batch collection behavior (Issue #7)."""

from collections.abc import Generator
from typing import Any

import pytest
import simpy


class MockWagon:
    """Mock wagon for testing."""

    def __init__(self, wagon_id: str, length: float = 15.0) -> None:
        self.id = wagon_id
        self.length = length
        self.coupler_type = "DAC"


def test_batch_collection_full_batch_available() -> None:
    """Test batch collection when all wagons are immediately available (burst pattern)."""
    env = simpy.Environment()
    store = simpy.Store(env)
    batch_size = 5

    # Pre-populate store with wagons (burst pattern)
    for i in range(10):
        store.put(MockWagon(f"wagon_{i}"))

    collected_batches: list[list[MockWagon]] = []

    def collector() -> Generator[Any, Any]:
        """Collect batches."""
        for _ in range(2):  # Collect 2 batches
            batch: list[MockWagon] = []
            wagon: MockWagon = yield store.get()
            batch.append(wagon)

            for _ in range(batch_size - 1):
                if len(store.items) > 0:
                    additional_wagon: MockWagon = yield store.get()
                    batch.append(additional_wagon)
                else:
                    break

            collected_batches.append(batch)

    env.process(collector())
    env.run()

    assert len(collected_batches) == 2
    assert len(collected_batches[0]) == 5  # Full batch
    assert len(collected_batches[1]) == 5  # Full batch


def test_batch_collection_partial_batch() -> None:
    """Test batch collection when fewer wagons than batch size available."""
    env = simpy.Environment()
    store = simpy.Store(env)
    batch_size = 5

    # Only 3 wagons available
    for i in range(3):
        store.put(MockWagon(f"wagon_{i}"))

    collected_batch: list[MockWagon] = []

    def collector() -> Generator[Any, Any]:
        """Collect batch."""
        wagon: MockWagon = yield store.get()
        collected_batch.append(wagon)

        for _ in range(batch_size - 1):
            if len(store.items) > 0:
                additional_wagon: MockWagon = yield store.get()
                collected_batch.append(additional_wagon)
            else:
                break

    env.process(collector())
    env.run()

    assert len(collected_batch) == 3  # Partial batch
    assert len(store.items) == 0  # All wagons collected


def test_batch_collection_single_wagon() -> None:
    """Test batch collection when only one wagon available."""
    env = simpy.Environment()
    store = simpy.Store(env)
    batch_size = 5

    # Only 1 wagon available
    store.put(MockWagon("wagon_0"))

    collected_batch: list[MockWagon] = []

    def collector() -> Generator[Any, Any]:
        """Collect batch."""
        wagon: MockWagon = yield store.get()
        collected_batch.append(wagon)

        for _ in range(batch_size - 1):
            if len(store.items) > 0:
                additional_wagon: MockWagon = yield store.get()
                collected_batch.append(additional_wagon)
            else:
                break

    env.process(collector())
    env.run()

    assert len(collected_batch) == 1  # Single wagon batch
    assert len(store.items) == 0


def test_batch_collection_immediate_break_no_timeout() -> None:
    """Test that batch collection breaks immediately without waiting when queue empty."""
    env = simpy.Environment()
    store = simpy.Store(env)
    batch_size = 5

    # Only 2 wagons available
    store.put(MockWagon("wagon_0"))
    store.put(MockWagon("wagon_1"))

    collected_batch: list[MockWagon] = []
    collection_time: float = 0.0

    def collector() -> Generator[Any, Any]:
        """Collect batch."""
        nonlocal collection_time
        start_time = env.now

        wagon: MockWagon = yield store.get()
        collected_batch.append(wagon)

        for _ in range(batch_size - 1):
            if len(store.items) > 0:
                additional_wagon: MockWagon = yield store.get()
                collected_batch.append(additional_wagon)
            else:
                break  # Immediate break - no timeout

        collection_time = env.now - start_time

    env.process(collector())
    env.run()

    assert len(collected_batch) == 2
    assert collection_time == 0.0  # No waiting time


def test_batch_collection_multiple_batches_mixed_sizes() -> None:
    """Test collecting multiple batches with varying availability."""
    env = simpy.Environment()
    store = simpy.Store(env)
    batch_size = 5

    # First batch: 5 wagons (full)
    # Second batch: 2 wagons (partial)
    for i in range(7):
        store.put(MockWagon(f"wagon_{i}"))

    collected_batches: list[list[MockWagon]] = []

    def collector() -> Generator[Any, Any]:
        """Collect batches."""
        for _ in range(2):
            batch: list[MockWagon] = []
            wagon: MockWagon = yield store.get()
            batch.append(wagon)

            for _ in range(batch_size - 1):
                if len(store.items) > 0:
                    additional_wagon: MockWagon = yield store.get()
                    batch.append(additional_wagon)
                else:
                    break

            collected_batches.append(batch)

    env.process(collector())
    env.run()

    assert len(collected_batches) == 2
    assert len(collected_batches[0]) == 5  # Full batch
    assert len(collected_batches[1]) == 2  # Partial batch
    assert len(store.items) == 0  # All wagons collected


def test_batch_collection_respects_batch_size() -> None:
    """Test that batch collection never exceeds batch_size."""
    env = simpy.Environment()
    store = simpy.Store(env)
    batch_size = 3

    # More wagons than batch size
    for i in range(10):
        store.put(MockWagon(f"wagon_{i}"))

    collected_batch: list[MockWagon] = []

    def collector() -> Generator[Any, Any]:
        """Collect batch."""
        wagon: MockWagon = yield store.get()
        collected_batch.append(wagon)

        for _ in range(batch_size - 1):
            if len(store.items) > 0:
                additional_wagon: MockWagon = yield store.get()
                collected_batch.append(additional_wagon)
            else:
                break

    env.process(collector())
    env.run()

    assert len(collected_batch) == batch_size  # Exactly batch_size
    assert len(store.items) == 7  # Remaining wagons


def test_batch_collection_concurrent_arrival() -> None:
    """Test batch collection with wagons arriving during collection."""
    env = simpy.Environment()
    store = simpy.Store(env)
    batch_size = 5

    # Start with 2 wagons
    store.put(MockWagon("wagon_0"))
    store.put(MockWagon("wagon_1"))

    collected_batch: list[MockWagon] = []

    def wagon_producer() -> Generator[Any, Any]:
        """Produce wagons with delay."""
        yield env.timeout(0.5)
        store.put(MockWagon("wagon_2"))
        yield env.timeout(0.5)
        store.put(MockWagon("wagon_3"))

    def collector() -> Generator[Any, Any]:
        """Collect batch."""
        wagon: MockWagon = yield store.get()
        collected_batch.append(wagon)

        for _ in range(batch_size - 1):
            if len(store.items) > 0:
                additional_wagon: MockWagon = yield store.get()
                collected_batch.append(additional_wagon)
            else:
                break

    env.process(wagon_producer())
    env.process(collector())
    env.run()

    # Should collect only immediately available wagons (2)
    # Does not wait for wagons arriving later
    assert len(collected_batch) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
