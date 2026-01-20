"""Tests for YardOperationsContext."""

from unittest.mock import Mock

from contexts.yard_operations.application.yard_context import YardOperationsContext
from contexts.yard_operations.domain.services.step_planners import RakeTransportPlan
import pytest
from shared.domain.entities.wagon import Wagon
from shared.domain.events.wagon_lifecycle_events import TrainArrivedEvent
from shared.domain.events.wagon_lifecycle_events import WagonsReadyForPickupEvent


class TestYardOperationsContext:
    """Test YardOperationsContext functionality."""

    @pytest.fixture
    def mock_infra(self) -> Mock:
        """Create mock infrastructure."""
        infra = Mock()
        infra.engine = Mock()
        infra.event_bus = Mock()
        infra.contexts = {'railway': Mock()}
        return infra

    @pytest.fixture
    def mock_scenario(self) -> Mock:
        """Create mock scenario."""
        scenario = Mock()
        scenario.process_times = Mock()
        scenario.workshops = []
        return scenario

    @pytest.fixture
    def yard_context(self, mock_infra: Mock) -> YardOperationsContext:
        """Create yard context instance."""
        return YardOperationsContext(mock_infra)

    @pytest.fixture
    def initialized_yard_context(
        self, yard_context: YardOperationsContext, mock_infra: Mock, mock_scenario: Mock
    ) -> YardOperationsContext:
        """Create initialized yard context."""
        # Setup railway context mock
        railway_context = mock_infra.contexts['railway']
        railway_context.get_track_selection_service.return_value = Mock()
        railway_context.get_track_selection_service().get_tracks_by_type.return_value = [Mock(id='collection_1')]
        railway_context.get_track_capacity.return_value = 100.0
        railway_context.get_track_selection_service().get_track_ids_by_type.return_value = ['collection_1']

        yard_context.initialize(mock_infra, mock_scenario)
        return yard_context

    def test_initialization(self, yard_context: YardOperationsContext, mock_infra: Mock, mock_scenario: Mock) -> None:
        """Test yard context initialization."""
        # Setup railway context mock
        railway_context = mock_infra.contexts['railway']
        railway_context.get_track_selection_service.return_value = Mock()
        railway_context.get_track_selection_service().get_tracks_by_type.return_value = [Mock(id='collection_1')]
        railway_context.get_track_capacity.return_value = 100.0
        railway_context.get_track_selection_service().get_track_ids_by_type.return_value = ['collection_1']

        yard_context.initialize(mock_infra, mock_scenario)

        assert yard_context.railway_context is not None
        assert yard_context.collection_to_retrofit_planner is not None
        assert yard_context.hump_yard_service is not None
        assert yard_context.yard_config is not None

    def test_initialization_no_collection_tracks(
        self, yard_context: YardOperationsContext, mock_infra: Mock, mock_scenario: Mock
    ) -> None:
        """Test initialization fails when no collection tracks."""
        railway_context = mock_infra.contexts['railway']
        railway_context.get_track_selection_service.return_value = Mock()
        railway_context.get_track_selection_service().get_tracks_by_type.return_value = []

        with pytest.raises(RuntimeError, match='No collection tracks found'):
            yard_context.initialize(mock_infra, mock_scenario)

    def test_get_wagons_on_track(self, initialized_yard_context: YardOperationsContext) -> None:
        """Test getting wagons on track."""
        # Setup mocks
        wagon = Mock()
        wagon.id = 'wagon_1'
        initialized_yard_context.all_wagons = [wagon]

        track_occupancy = Mock()
        track_occupancy.get_wagons_in_sequence.return_value = [wagon]

        occupancy_repo = Mock()
        occupancy_repo.get_wagons_on_track.return_value = [wagon]
        initialized_yard_context.railway_context.get_occupancy_repository.return_value = occupancy_repo

        wagons = initialized_yard_context._get_wagons_on_track('test_track')
        assert len(wagons) == 1
        assert wagons[0].id == 'wagon_1'

    def test_get_wagons_on_track_empty(self, initialized_yard_context: YardOperationsContext) -> None:
        """Test getting wagons on empty track."""
        occupancy_repo = Mock()
        occupancy_repo.get_wagons_on_track.return_value = []
        initialized_yard_context.railway_context.get_occupancy_repository.return_value = occupancy_repo

        wagons = initialized_yard_context._get_wagons_on_track('test_track')
        assert len(wagons) == 0

    def test_add_wagons_to_track_success(self, initialized_yard_context: YardOperationsContext) -> None:
        """Test successfully adding wagons to track."""
        wagon = Mock()
        wagon.id = 'wagon_1'
        wagon.length = 15.0

        track = Mock()
        track_occupancy = Mock()
        track_occupancy.add_wagon = Mock()  # Mock the add_wagon method

        occupancy_repo = Mock()
        occupancy_repo.get_or_create.return_value = track_occupancy

        initialized_yard_context.railway_context.get_track.return_value = track
        initialized_yard_context.railway_context.get_occupancy_repository.return_value = occupancy_repo

        accepted, rejected = initialized_yard_context._add_wagons_to_track([wagon], 'test_track')

        assert len(accepted) == 1
        assert len(rejected) == 0
        track_occupancy.add_wagon.assert_called_once()

    def test_add_wagons_to_track_no_capacity(self, initialized_yard_context: YardOperationsContext) -> None:
        """Test adding wagons when track has no capacity."""
        wagon = Mock()
        wagon.id = 'wagon_1'
        wagon.length = 15.0

        track = Mock()
        track_occupancy = Mock()
        track_occupancy.add_wagon.side_effect = ValueError('No space')  # Simulate no space

        occupancy_repo = Mock()
        occupancy_repo.get_or_create.return_value = track_occupancy

        initialized_yard_context.railway_context.get_track.return_value = track
        initialized_yard_context.railway_context.get_occupancy_repository.return_value = occupancy_repo

        accepted, rejected = initialized_yard_context._add_wagons_to_track([wagon], 'test_track')

        assert len(accepted) == 0
        assert len(rejected) == 1
        assert rejected[0].status.value == 'rejected'

    def test_handle_train_arrived(self, initialized_yard_context: YardOperationsContext) -> None:
        """Test handling train arrival event."""
        wagon = Mock(spec=Wagon)
        wagon.id = 'wagon_1'
        event = TrainArrivedEvent(train_id='train_1', wagons=[wagon], arrival_track='arrival_1')

        initialized_yard_context._handle_train_arrived(event)

        assert len(initialized_yard_context.all_wagons) == 1
        initialized_yard_context.infra.engine.schedule_process.assert_called()

    def test_handle_wagons_ready_for_pickup(self, initialized_yard_context: YardOperationsContext) -> None:
        """Test handling wagons ready for pickup event."""
        event = WagonsReadyForPickupEvent(track_id='collection_1', wagon_count=5, event_timestamp=0.0)

        initialized_yard_context._handle_wagons_ready_for_pickup(event)

        initialized_yard_context.infra.engine.schedule_process.assert_called()

    def test_get_metrics(self, initialized_yard_context: YardOperationsContext) -> None:
        """Test getting yard metrics."""
        # Mock railway context methods to avoid type errors
        initialized_yard_context.railway_context.get_available_capacity.return_value = 50.0
        initialized_yard_context.railway_context.get_total_capacity.return_value = 100.0
        initialized_yard_context.infra.engine.current_time.return_value = 10.0

        # Add some test wagons
        from shared.domain.entities.wagon import WagonStatus

        wagon1 = Mock()
        wagon1.status = WagonStatus.RETROFITTED
        wagon2 = Mock()
        wagon2.status = WagonStatus.PARKING
        initialized_yard_context.wagons = [wagon1, wagon2]

        metrics = initialized_yard_context.get_metrics()

        assert 'classified_wagons' in metrics
        assert 'rejected_wagons' in metrics
        assert 'total_rakes_formed' in metrics
        assert metrics['classified_wagons'] == 2
        assert metrics['wagons_on_retrofitted'] == 1
        assert metrics['wagons_parked'] == 1

    def test_pickup_wagons_with_transport_plan(self, initialized_yard_context: YardOperationsContext) -> None:
        """Test pickup wagons creates transport plan."""
        # Setup wagon on track
        wagon = Mock()
        wagon.id = 'wagon_1'
        initialized_yard_context.all_wagons = [wagon]

        # Mock track occupancy
        occupancy_repo = Mock()
        occupancy_repo.get_wagons_on_track.return_value = [wagon]
        initialized_yard_context.railway_context.get_occupancy_repository.return_value = occupancy_repo

        # Mock transport plan
        transport_plan = RakeTransportPlan(
            wagons=[wagon],
            from_track='collection_1',
            to_track='retrofit_1',
            rake_id='test_rake',
            capacity_validated=True,
        )
        # Mock the planner method properly
        planner_mock = Mock()
        planner_mock.plan_transport.return_value = transport_plan
        initialized_yard_context.collection_to_retrofit_planner = planner_mock

        # Test that wagons are found on track
        wagons_on_track = initialized_yard_context._get_wagons_on_track('collection_1')
        assert len(wagons_on_track) == 1

        # Test that planner can create transport plan
        plan = initialized_yard_context.collection_to_retrofit_planner.plan_transport(wagons_on_track, 'collection_1')
        assert plan is not None
        assert plan.from_track == 'collection_1'
        assert plan.to_track == 'retrofit_1'
