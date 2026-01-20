"""Tests for ArrivalCoordinator application component."""

from contexts.retrofit_workflow.application.config.coordinator_config import ArrivalCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.arrival_coordinator import ArrivalCoordinator
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
import pytest
import simpy


class TestArrivalCoordinator:
    """Test ArrivalCoordinator application component."""

    @pytest.fixture
    def env(self) -> simpy.Environment:
        """Create SimPy environment."""
        return simpy.Environment()

    @pytest.fixture
    def collection_queue(self, env: simpy.Environment) -> simpy.FilterStore:
        """Create collection queue."""
        return simpy.FilterStore(env)

    @pytest.fixture
    def events(self) -> list[WagonJourneyEvent]:
        """Event collector for testing."""
        return []

    @pytest.fixture
    def coordinator(
        self, env: simpy.Environment, collection_queue: simpy.FilterStore, events: list[WagonJourneyEvent]
    ) -> ArrivalCoordinator:
        """Create arrival coordinator."""
        config = ArrivalCoordinatorConfig(env=env, collection_queue=collection_queue, event_publisher=events.append)
        return ArrivalCoordinator(config)

    def test_initialization(self, coordinator: ArrivalCoordinator) -> None:
        """Test coordinator initialization."""
        assert len(coordinator.trains) == 0

    def test_schedule_train_immediate_arrival(
        self,
        env: simpy.Environment,
        coordinator: ArrivalCoordinator,
        collection_queue: simpy.FilterStore,
        events: list[WagonJourneyEvent],
    ) -> None:
        """Test scheduling train with immediate arrival."""
        wagon_configs = [{'id': 'wagon_1', 'length': 15.0}, {'id': 'wagon_2', 'length': 20.0}]

        coordinator.schedule_train(train_id='train_1', arrival_time=0.0, wagon_configs=wagon_configs)

        # Run simulation
        env.run(until=1.0)

        # Check train created
        assert len(coordinator.trains) == 1
        train = coordinator.trains[0]
        assert train.id == 'train_1'
        assert len(train.wagons) == 2

        # Check wagons in collection queue
        assert len(collection_queue.items) == 2

        # Check events published
        assert len(events) == 2
        for event in events:
            assert event.event_type == 'ARRIVED'
            assert event.location == 'collection'
            assert event.train_id == 'train_1'

    def test_schedule_train_delayed_arrival(
        self, env: simpy.Environment, coordinator: ArrivalCoordinator, collection_queue: simpy.FilterStore
    ) -> None:
        """Test scheduling train with delayed arrival."""
        wagon_configs = [{'id': 'wagon_1', 'length': 15.0}]

        coordinator.schedule_train(train_id='train_1', arrival_time=10.0, wagon_configs=wagon_configs)

        # Run until before arrival
        env.run(until=5.0)
        assert len(collection_queue.items) == 0

        # Run until after arrival
        env.run(until=15.0)
        assert len(collection_queue.items) == 1

    def test_schedule_multiple_trains(
        self,
        env: simpy.Environment,
        coordinator: ArrivalCoordinator,
        collection_queue: simpy.FilterStore,
        events: list[WagonJourneyEvent],
    ) -> None:
        """Test scheduling multiple trains."""
        # Schedule first train
        coordinator.schedule_train(
            train_id='train_1', arrival_time=0.0, wagon_configs=[{'id': 'wagon_1', 'length': 15.0}]
        )

        # Schedule second train
        coordinator.schedule_train(
            train_id='train_2',
            arrival_time=5.0,
            wagon_configs=[{'id': 'wagon_2', 'length': 20.0}, {'id': 'wagon_3', 'length': 18.0}],
        )

        env.run(until=10.0)

        # Check both trains created
        assert len(coordinator.trains) == 2

        # Check all wagons in collection queue
        assert len(collection_queue.items) == 3

        # Check events for both trains
        train_1_events = [e for e in events if e.train_id == 'train_1']
        train_2_events = [e for e in events if e.train_id == 'train_2']
        assert len(train_1_events) == 1
        assert len(train_2_events) == 2

    def test_wagon_creation_with_default_values(
        self, env: simpy.Environment, coordinator: ArrivalCoordinator, collection_queue: simpy.FilterStore
    ) -> None:
        """Test wagon creation uses default values when not specified."""
        wagon_configs = [
            {'id': 'wagon_1'},  # No length specified
            {'id': 'wagon_2', 'length': 25.0},
        ]

        coordinator.schedule_train(train_id='train_1', arrival_time=0.0, wagon_configs=wagon_configs)

        env.run(until=1.0)

        # Get wagons from queue
        wagons = []
        while collection_queue.items:
            wagon = collection_queue.items.pop(0)
            wagons.append(wagon)

        # Check default length applied
        wagon_1 = next(w for w in wagons if w.id == 'wagon_1')
        wagon_2 = next(w for w in wagons if w.id == 'wagon_2')

        assert wagon_1.length == 15.0  # Default
        assert wagon_2.length == 25.0  # Specified

    def test_no_event_publisher(self, env: simpy.Environment, collection_queue: simpy.FilterStore) -> None:
        """Test coordinator works without event publisher."""
        config = ArrivalCoordinatorConfig(env=env, collection_queue=collection_queue, event_publisher=None)
        coordinator = ArrivalCoordinator(config)

        coordinator.schedule_train(
            train_id='train_1', arrival_time=0.0, wagon_configs=[{'id': 'wagon_1', 'length': 15.0}]
        )

        # Should not raise exception
        env.run(until=1.0)

        # Wagon should still be in queue
        assert len(collection_queue.items) == 1

    def test_empty_wagon_configs(
        self, env: simpy.Environment, coordinator: ArrivalCoordinator, collection_queue: simpy.FilterStore
    ) -> None:
        """Test train with no wagons raises error."""
        with pytest.raises(ValueError, match='Train train_1 must have at least one wagon'):
            coordinator.schedule_train(train_id='train_1', arrival_time=0.0, wagon_configs=[])
            env.run(until=1.0)
