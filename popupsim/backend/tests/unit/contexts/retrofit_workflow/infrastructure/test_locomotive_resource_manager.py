"""Tests for LocomotiveResourceManager infrastructure component."""

from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
from contexts.retrofit_workflow.infrastructure.resources.locomotive_resource_manager import LocomotiveResourceManager
import pytest
import simpy


class TestLocomotiveResourceManager:
    """Test LocomotiveResourceManager infrastructure component."""

    @pytest.fixture
    def env(self) -> simpy.Environment:
        """Create SimPy environment."""
        return simpy.Environment()

    @pytest.fixture
    def locomotives(self) -> list[Locomotive]:
        """Create test locomotives."""
        return [
            Locomotive(
                id='loco_1',
                home_track='locoparking',
                coupler_front=Coupler(CouplerType.HYBRID, 'FRONT'),
                coupler_back=Coupler(CouplerType.HYBRID, 'BACK'),
            ),
            Locomotive(
                id='loco_2',
                home_track='locoparking',
                coupler_front=Coupler(CouplerType.HYBRID, 'FRONT'),
                coupler_back=Coupler(CouplerType.HYBRID, 'BACK'),
            ),
        ]

    @pytest.fixture
    def events(self) -> list[ResourceStateChangeEvent]:
        """Event collector for testing."""
        events = []
        return events

    @pytest.fixture
    def manager(
        self, env: simpy.Environment, locomotives: list[Locomotive], events: list[ResourceStateChangeEvent]
    ) -> LocomotiveResourceManager:
        """Create locomotive resource manager."""
        return LocomotiveResourceManager(env=env, locomotives=locomotives, event_publisher=events.append)

    def test_initialization(self, manager: LocomotiveResourceManager, locomotives: list[Locomotive]) -> None:
        """Test manager initialization."""
        assert manager.get_total_count() == 2
        assert manager.get_available_count() == 2
        assert manager.get_allocated_count() == 0
        assert manager.get_utilization() == 0.0

    def test_allocate_single_locomotive(
        self, env: simpy.Environment, manager: LocomotiveResourceManager, events: list[ResourceStateChangeEvent]
    ) -> None:
        """Test allocating single locomotive."""

        def process() -> None:
            loco = yield from manager.allocate()
            assert loco.id in ['loco_1', 'loco_2']
            assert manager.get_allocated_count() == 1
            assert manager.get_available_count() == 1
            assert manager.get_utilization() == 50.0

        env.process(process())
        env.run()

        # Check event published
        assert len(events) == 1
        event = events[0]
        assert event.resource_type == 'locomotive'
        assert event.change_type == 'allocated'
        assert event.busy_count_before == 0
        assert event.busy_count_after == 1

    def test_allocate_all_locomotives(self, env: simpy.Environment, manager: LocomotiveResourceManager) -> None:
        """Test allocating all locomotives."""
        allocated_locos = []

        def process() -> None:
            loco1 = yield from manager.allocate()
            allocated_locos.append(loco1)
            loco2 = yield from manager.allocate()
            allocated_locos.append(loco2)

        env.process(process())
        env.run()

        assert len(allocated_locos) == 2
        assert manager.get_allocated_count() == 2
        assert manager.get_available_count() == 0
        assert manager.get_utilization() == 100.0

    def test_release_locomotive(
        self, env: simpy.Environment, manager: LocomotiveResourceManager, events: list[ResourceStateChangeEvent]
    ) -> None:
        """Test releasing locomotive."""

        def process() -> None:
            loco = yield from manager.allocate()
            yield from manager.release(loco)

            assert manager.get_allocated_count() == 0
            assert manager.get_available_count() == 2
            assert manager.get_utilization() == 0.0

        env.process(process())
        env.run()

        # Check events (allocate + release)
        assert len(events) == 2
        release_event = events[1]
        assert release_event.change_type == 'released'
        assert release_event.busy_count_before == 1
        assert release_event.busy_count_after == 0

    def test_blocking_when_all_allocated(self, env: simpy.Environment, manager: LocomotiveResourceManager) -> None:
        """Test that allocation blocks when all locomotives are allocated."""
        results = []

        def allocate_all() -> None:
            loco1 = yield from manager.allocate()
            loco2 = yield from manager.allocate()
            results.extend([loco1, loco2])

            # Hold for 10 time units
            yield env.timeout(10)

            # Release one
            yield from manager.release(loco1)

        def try_allocate_third() -> None:
            # This should block until a locomotive is released
            yield env.timeout(5)  # Start after others allocated
            loco3 = yield from manager.allocate()
            results.append(loco3)

        env.process(allocate_all())
        env.process(try_allocate_third())
        env.run()

        # Should have allocated 3 times (2 initial + 1 after release)
        assert len(results) == 3

    def test_batch_completion_priority_strategy(self, env: simpy.Environment, locomotives: list[Locomotive]) -> None:
        """Test that manager works without priority strategy (removed feature)."""
        manager = LocomotiveResourceManager(env=env, locomotives=locomotives)

        results = []

        def allocate_for_parking() -> None:
            loco = yield from manager.allocate(purpose='parking')
            results.append(('parking', loco))

        def allocate_for_workshop() -> None:
            yield env.timeout(1)
            loco = yield from manager.allocate(purpose='workshop_pickup')
            results.append(('workshop', loco))

        env.process(allocate_for_parking())
        env.process(allocate_for_workshop())
        env.run(until=10)

        # Both should allocate successfully (FIFO order)
        assert len(results) == 2
        assert results[0][0] == 'parking'
        assert results[1][0] == 'workshop'

    def test_get_metrics(self, manager: LocomotiveResourceManager) -> None:
        """Test metrics collection."""
        metrics = manager.get_metrics()

        expected_keys = {'total', 'available', 'allocated', 'utilization_percent'}
        assert set(metrics.keys()) == expected_keys
        assert metrics['total'] == 2
        assert metrics['available'] == 2
        assert metrics['allocated'] == 0
        assert metrics['utilization_percent'] == 0.0

    def test_empty_locomotive_pool(self, env: simpy.Environment) -> None:
        """Test manager with empty locomotive pool raises error."""
        with pytest.raises(ValueError, match='"capacity" must be > 0.'):
            LocomotiveResourceManager(env=env, locomotives=[])
