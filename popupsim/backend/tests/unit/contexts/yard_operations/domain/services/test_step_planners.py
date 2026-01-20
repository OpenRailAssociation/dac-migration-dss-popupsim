"""Tests for CollectionToRetrofitPlanner."""

from unittest.mock import Mock

from contexts.yard_operations.domain.services.step_planners import CollectionToRetrofitPlanner
from contexts.yard_operations.domain.services.step_planners import RakeTransportPlan
import pytest
from shared.domain.entities.wagon import Wagon


class TestCollectionToRetrofitPlanner:
    """Test CollectionToRetrofitPlanner functionality."""

    @pytest.fixture
    def mock_railway_context(self) -> Mock:
        """Create mock railway context."""
        context = Mock()
        track_service = Mock()
        context.get_track_selection_service.return_value = track_service
        return context

    @pytest.fixture
    def planner(self, mock_railway_context: Mock) -> CollectionToRetrofitPlanner:
        """Create planner instance."""
        return CollectionToRetrofitPlanner(mock_railway_context)

    @pytest.fixture
    def sample_wagons(self) -> list[Wagon]:
        """Create sample wagons."""
        wagons: list[Wagon] = []
        for i in range(3):
            wagon = Mock(spec=Wagon)
            wagon.id = f'wagon_{i}'
            wagon.length = 15.0
            wagons.append(wagon)
        return wagons

    def test_plan_transport_success(
        self, planner: CollectionToRetrofitPlanner, sample_wagons: list[Wagon], mock_railway_context: Mock
    ) -> None:
        """Test successful transport planning."""
        # Setup mocks
        track = Mock()
        track.id = 'retrofit_1'
        mock_railway_context.get_track_selection_service().get_tracks_by_type.return_value = [track]
        mock_railway_context.get_available_capacity.return_value = 50.0

        # Execute
        plan = planner.plan_transport(sample_wagons, 'collection_1')

        # Assert
        assert plan is not None
        assert isinstance(plan, RakeTransportPlan)
        assert plan.from_track == 'collection_1'
        assert plan.to_track == 'retrofit_1'
        assert len(plan.wagons) == 3
        assert plan.capacity_validated is True

    def test_plan_transport_no_wagons(self, planner: CollectionToRetrofitPlanner) -> None:
        """Test planning with no wagons."""
        plan = planner.plan_transport([], 'collection_1')
        assert plan is None

    def test_plan_transport_no_retrofit_tracks(
        self, planner: CollectionToRetrofitPlanner, sample_wagons: list[Wagon], mock_railway_context: Mock
    ) -> None:
        """Test planning when no retrofit tracks available."""
        mock_railway_context.get_track_selection_service().get_tracks_by_type.return_value = []

        plan = planner.plan_transport(sample_wagons, 'collection_1')
        assert plan is None

    def test_plan_transport_no_capacity(
        self, planner: CollectionToRetrofitPlanner, sample_wagons: list[Wagon], mock_railway_context: Mock
    ) -> None:
        """Test planning when no capacity available."""
        track = Mock()
        track.id = 'retrofit_1'
        mock_railway_context.get_track_selection_service().get_tracks_by_type.return_value = [track]
        mock_railway_context.get_available_capacity.return_value = 0.0

        plan = planner.plan_transport(sample_wagons, 'collection_1')
        assert plan is None

    def test_plan_transport_partial_capacity(
        self, planner: CollectionToRetrofitPlanner, sample_wagons: list[Wagon], mock_railway_context: Mock
    ) -> None:
        """Test planning with partial capacity."""
        track = Mock()
        track.id = 'retrofit_1'
        mock_railway_context.get_track_selection_service().get_tracks_by_type.return_value = [track]
        mock_railway_context.get_available_capacity.return_value = 30.0  # Only fits 2 wagons

        plan = planner.plan_transport(sample_wagons, 'collection_1')

        assert plan is not None
        assert len(plan.wagons) == 2  # Only 2 wagons fit
        assert plan.capacity_validated is True

    def test_select_best_retrofit_track_multiple_tracks(
        self, planner: CollectionToRetrofitPlanner, mock_railway_context: Mock
    ) -> None:
        """Test selecting best track from multiple options."""
        track1 = Mock()
        track1.id = 'retrofit_1'
        track2 = Mock()
        track2.id = 'retrofit_2'

        mock_railway_context.get_track_selection_service().get_tracks_by_type.return_value = [track1, track2]
        mock_railway_context.get_available_capacity.side_effect = (
            lambda track_id: 20.0 if track_id == 'retrofit_1' else 50.0
        )

        best_track = planner._select_best_retrofit_track()
        assert best_track == 'retrofit_2'  # Higher capacity

    def test_select_wagons_for_capacity(self, planner: CollectionToRetrofitPlanner, sample_wagons: list[Wagon]) -> None:
        """Test wagon selection based on capacity."""
        selected = planner._select_wagons_for_capacity(sample_wagons, 30.0)
        assert len(selected) == 2  # 2 * 15.0 = 30.0

        selected = planner._select_wagons_for_capacity(sample_wagons, 10.0)
        assert len(selected) == 0  # No wagons fit
