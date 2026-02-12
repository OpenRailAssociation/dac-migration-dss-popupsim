"""Integration tests for RetrofitWorkshopContext."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
import pytest
import simpy


class MockScenario:
    """Mock scenario for testing."""

    def __init__(self) -> None:
        self.id = 'test_scenario'
        self.workshops = [
            Mock(id='ws_1', track='track_1', retrofit_stations=2),
            Mock(id='ws_2', track='track_2', retrofit_stations=3),
        ]

        self.locomotives = [Mock(id='loco_1', track='locoparking'), Mock(id='loco_2', track='locoparking')]

        self.tracks = [
            Mock(id='collection', type='collection', length=100.0, fillfactor=0.8),
            Mock(id='retrofit', type='retrofit', length=80.0, fillfactor=0.9),
            Mock(id='retrofitted', type='retrofitted', length=120.0, fillfactor=0.8),
            Mock(id='parking_1', type='parking', length=200.0, fillfactor=0.7),
            Mock(id='parking_2', type='parking', length=150.0, fillfactor=0.7),
        ]

        self.routes = [
            Mock(
                from_location='collection',
                to_location='retrofit',
                duration=timedelta(minutes=2),
                path=['collection', 'retrofit'],
            ),
            Mock(
                from_location='retrofit', to_location='ws_1', duration=timedelta(minutes=3), path=['retrofit', 'ws_1']
            ),
            Mock(
                from_location='ws_1',
                to_location='retrofitted',
                duration=timedelta(minutes=3),
                path=['ws_1', 'retrofitted'],
            ),
            Mock(
                from_location='retrofitted',
                to_location='parking_1',
                duration=timedelta(minutes=4),
                path=['retrofitted', 'parking_1'],
            ),
        ]

        self.trains = [
            Mock(train_id='train_1', wagons=[Mock(id='wagon_1', length=15.0), Mock(id='wagon_2', length=18.0)])
        ]

        self.process_times = Mock(wagon_retrofit_time=timedelta(minutes=10))
        self.loco_priority_strategy = Mock(value='workshop_priority')
        self.collection_track_strategy = Mock(value='round_robin')
        self.retrofit_selection_strategy = Mock(value='least_busy')
        self.parking_selection_strategy = Mock(value='least_busy')
        self.parking_strategy = Mock(value='batch_completion')
        self.parking_normal_threshold = 0.8
        self.parking_critical_threshold = 0.95
        self.parking_idle_check_interval = 5.0


class TestRetrofitWorkshopContext:
    """Test RetrofitWorkshopContext integration."""

    @pytest.fixture
    def env(self) -> simpy.Environment:
        """Create SimPy environment."""
        return simpy.Environment()

    @pytest.fixture
    def scenario(self) -> MockScenario:
        """Create mock scenario."""
        return MockScenario()

    @pytest.fixture
    def context(self, env: simpy.Environment, scenario: MockScenario) -> RetrofitWorkshopContext:
        """Create retrofit workflowcontext."""
        return RetrofitWorkshopContext(env, scenario)

    def test_initialization_creates_queues(self, context: RetrofitWorkshopContext) -> None:
        """Test context initialization creates SimPy queues."""
        assert context.collection_queue is not None
        assert context.retrofit_queue is not None
        assert context.retrofitted_queue is not None
        assert isinstance(context.collection_queue, simpy.FilterStore)

    def test_initialize_creates_workshops(self, context: RetrofitWorkshopContext, scenario: MockScenario) -> None:
        """Test initialization creates workshop entities."""
        context.initialize()

        assert len(context.workshops) == 2
        assert 'ws_1' in context.workshops
        assert 'ws_2' in context.workshops

        ws_1 = context.workshops['ws_1']
        assert ws_1.id == 'ws_1'
        assert ws_1.location == 'track_1'
        assert ws_1.capacity == 2

    def test_initialize_creates_locomotives(self, context: RetrofitWorkshopContext, scenario: MockScenario) -> None:
        """Test initialization creates locomotive entities."""
        context.initialize()

        assert len(context.locomotives) == 2
        loco_ids = [loco.id for loco in context.locomotives]
        assert 'loco_1' in loco_ids
        assert 'loco_2' in loco_ids

    def test_initialize_creates_resource_managers(self, context: RetrofitWorkshopContext) -> None:
        """Test initialization creates resource managers."""
        context.initialize()

        assert context.workshop_resources is not None
        assert context.locomotive_manager is not None
        assert context.track_manager is not None

    def test_initialize_creates_domain_services(self, context: RetrofitWorkshopContext) -> None:
        """Test initialization creates domain services."""
        context.initialize()

        assert context.route_service is not None
        assert context.coupling_validator is not None
        assert context.batch_formation_service is not None

    def test_initialize_creates_coordinators(self, context: RetrofitWorkshopContext) -> None:
        """Test initialization creates coordinators."""
        context.initialize()

        assert context.arrival_coordinator is not None
        # Note: Other coordinators may be None in current implementation

    def test_initialize_creates_event_collector(self, context: RetrofitWorkshopContext) -> None:
        """Test initialization creates event collector."""
        context.initialize()

        assert context.event_collector is not None

    def test_start_processes_without_error(self, context: RetrofitWorkshopContext) -> None:
        """Test starting processes doesn't raise errors."""
        context.initialize()

        # Should not raise exception
        context.start_processes()

    def test_get_metrics_returns_data(self, context: RetrofitWorkshopContext) -> None:
        """Test metrics collection returns data."""
        context.initialize()

        metrics = context.get_metrics()

        assert 'workshops' in metrics
        assert 'locomotives' in metrics
        assert 'tracks' in metrics

    def test_get_status_returns_info(self, context: RetrofitWorkshopContext) -> None:
        """Test status returns context information."""
        context.initialize()

        status = context.get_status()

        assert 'workshops' in status
        assert 'locomotives' in status
        assert 'status' in status
        assert status['workshops'] == 2
        assert status['locomotives'] == 2
        assert status['status'] == 'ready'

    def test_cleanup_without_error(self, context: RetrofitWorkshopContext) -> None:
        """Test cleanup doesn't raise errors."""
        context.initialize()

        # Should not raise exception
        context.cleanup()

    def test_export_events_without_error(self, context: RetrofitWorkshopContext, tmp_path) -> None:
        """Test event export doesn't raise errors."""
        context.initialize()

        # Should not raise exception
        context.export_events(str(tmp_path))

    def test_full_initialization_flow(self, env: simpy.Environment, scenario: MockScenario) -> None:
        """Test complete initialization flow."""
        context = RetrofitWorkshopContext(env, scenario)

        # Initialize
        context.initialize()

        # Start processes
        context.start_processes()

        # Run brief simulation
        env.run(until=1.0)

        # Get metrics
        metrics = context.get_metrics()
        assert metrics is not None

        # Cleanup
        context.cleanup()

    def test_scenario_without_optional_attributes(self, env: simpy.Environment) -> None:
        """Test context handles scenario without optional attributes."""
        minimal_scenario = Mock()
        minimal_scenario.workshops = []
        minimal_scenario.locomotives = [Mock(id='loco_1', track='depot')]  # Need at least one
        minimal_scenario.tracks = []
        minimal_scenario.routes = []
        minimal_scenario.process_times = Mock(wagon_retrofit_time=timedelta(minutes=10))
        minimal_scenario.collection_track_strategy = Mock(value='round_robin')
        minimal_scenario.retrofit_selection_strategy = Mock(value='least_busy')
        minimal_scenario.parking_selection_strategy = Mock(value='least_busy')
        minimal_scenario.parking_strategy = Mock(value='batch_completion')
        minimal_scenario.parking_normal_threshold = 0.8
        minimal_scenario.parking_critical_threshold = 0.95
        minimal_scenario.parking_idle_check_interval = 5.0

        context = RetrofitWorkshopContext(env, minimal_scenario)

        # Should not raise exception
        context.initialize()

        # Should have minimal collections
        assert len(context.workshops) == 0
        assert len(context.locomotives) == 1
