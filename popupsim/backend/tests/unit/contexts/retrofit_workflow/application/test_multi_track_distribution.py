"""Integration test for multi-track wagon distribution and FIFO pickup."""

from unittest.mock import Mock

from contexts.retrofit_workflow.application.config.coordinator_config import ArrivalCoordinatorConfig
from contexts.retrofit_workflow.application.config.coordinator_config import CollectionCoordinatorConfig

# from contexts.retrofit_workflow.application.coordinators.archive.arrival_coordinator import ArrivalCoordinator  # type: ignore[import-not-found]
from contexts.retrofit_workflow.application.coordinators.arrival_coordinator import ArrivalCoordinator
from contexts.retrofit_workflow.application.coordinators.collection_coordinator import CollectionCoordinator
from contexts.retrofit_workflow.application.services.coordination_service import CoordinationService
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService
from contexts.retrofit_workflow.domain.services.coupling_service import CouplingService
from contexts.retrofit_workflow.domain.services.resource_selection_service import SelectionStrategy
from contexts.retrofit_workflow.domain.services.route_service import RouteService
from contexts.retrofit_workflow.domain.services.track_selection_service import TrackSelectionService
from contexts.retrofit_workflow.domain.services.train_formation_service import TrainFormationService
from contexts.retrofit_workflow.infrastructure.resources.locomotive_resource_manager import LocomotiveResourceManager
from contexts.retrofit_workflow.infrastructure.resources.track_capacity_manager import TrackResourceManager
import pytest
import simpy


class TestMultiTrackDistribution:
    """Test wagon distribution across multiple collection tracks."""

    @pytest.fixture
    def env(self) -> simpy.Environment:
        """Create SimPy environment."""
        return simpy.Environment()

    @pytest.fixture
    def collection_queue(self, env: simpy.Environment) -> simpy.FilterStore:
        """Create collection queue."""
        return simpy.FilterStore(env)

    @pytest.fixture
    def retrofit_queue(self, env: simpy.Environment) -> simpy.FilterStore:
        """Create retrofit queue."""
        return simpy.FilterStore(env)

    @pytest.fixture
    def track_manager(self, env: simpy.Environment) -> TrackResourceManager:
        """Create track manager with multiple collection tracks."""
        track_capacities = {
            'collection_1': 10000.0,  # Large capacity
            'collection_2': 10000.0,  # Large capacity
            'retrofit_1': 10000.0,
        }
        return TrackResourceManager(env, track_capacities)

    @pytest.fixture
    def track_selector(self, track_manager: TrackResourceManager) -> TrackSelectionService:
        """Create track selector with round-robin strategy."""
        tracks_by_type = {
            'collection': [
                track_manager.get_track('collection_1'),
                track_manager.get_track('collection_2'),
            ],
            'retrofit': [track_manager.get_track('retrofit_1')],
        }
        return TrackSelectionService(tracks_by_type, default_strategy=SelectionStrategy.ROUND_ROBIN)

    @pytest.fixture
    def arrival_coordinator(
        self, env: simpy.Environment, collection_queue: simpy.FilterStore, track_selector: TrackSelectionService
    ) -> ArrivalCoordinator:
        """Create arrival coordinator."""
        collection_coordinator = Mock()
        config = ArrivalCoordinatorConfig(
            env=env,
            collection_queue=collection_queue,
            track_selector=track_selector,
            collection_coordinator=collection_coordinator,
            event_publisher=None,
        )
        coordinator = ArrivalCoordinator(config)
        # Store mock for test access
        coordinator.collection_coordinator = collection_coordinator
        return coordinator

    @pytest.fixture
    def collection_coordinator(
        self,
        env: simpy.Environment,
        collection_queue: simpy.FilterStore,
        retrofit_queue: simpy.FilterStore,
        track_selector: TrackSelectionService,
    ) -> CollectionCoordinator:
        """Create collection coordinator."""
        # Mock dependencies
        loco_manager = Mock(spec=LocomotiveResourceManager)
        mock_loco = Mock(id='loco_1', home_track='depot')
        loco_manager.allocate = Mock(return_value=iter([mock_loco]))
        loco_manager.release = Mock(return_value=iter([None]))

        route_service = Mock(spec=RouteService)
        route_service.get_duration.return_value = 2.0
        route_service.get_route_type.return_value = 'YARD'

        batch_service = BatchFormationService()

        # Create mock process_times for CouplingService
        mock_process_times = Mock()
        mock_process_times.get_coupling_ticks.return_value = 1.0
        mock_process_times.get_decoupling_ticks.return_value = 1.0

        coupling_service = CouplingService(mock_process_times)
        train_service = TrainFormationService(coupling_service)

        scenario = Mock()
        scenario.process_times = Mock(
            loco_coupling_time=Mock(total_seconds=Mock(return_value=60)),
            brake_test_time=Mock(total_seconds=Mock(return_value=60)),
            train_inspection_time=Mock(total_seconds=Mock(return_value=60)),
        )

        config = CollectionCoordinatorConfig(
            env=env,
            collection_queue=collection_queue,
            retrofit_queue=retrofit_queue,
            locomotive_manager=loco_manager,
            track_selector=track_selector,
            batch_service=batch_service,
            route_service=route_service,
            train_service=train_service,
            scenario=scenario,
        )
        return CollectionCoordinator(config, CoordinationService())

    def test_round_robin_distributes_wagons_across_tracks(
        self,
        env: simpy.Environment,
        arrival_coordinator: ArrivalCoordinator,
        collection_queue: simpy.FilterStore,
    ) -> None:
        """Test round-robin strategy distributes wagons across multiple collection tracks."""
        # Schedule train with 6 wagons
        wagon_configs = [
            {'id': f'W{i:03d}', 'length': 15.0, 'is_loaded': False, 'needs_retrofit': True} for i in range(1, 7)
        ]

        arrival_coordinator.schedule_train(train_id='T1', arrival_time=0.0, wagon_configs=wagon_configs)

        # Run simulation
        env.run(until=1.0)

        # Check collection_coordinator.add_wagon was called 6 times
        assert arrival_coordinator.collection_coordinator.add_wagon.call_count == 6

        # Get wagons from mock calls
        wagons = [call[0][0] for call in arrival_coordinator.collection_coordinator.add_wagon.call_args_list]
        track_assignments = [w.current_track_id for w in wagons]

        # Round-robin should alternate: collection_1, collection_2, collection_1, collection_2, ...
        assert track_assignments[0] == 'collection_1'
        assert track_assignments[1] == 'collection_2'
        assert track_assignments[2] == 'collection_1'
        assert track_assignments[3] == 'collection_2'
        assert track_assignments[4] == 'collection_1'
        assert track_assignments[5] == 'collection_2'

        # Count distribution
        track_1_count = sum(1 for t in track_assignments if t == 'collection_1')
        track_2_count = sum(1 for t in track_assignments if t == 'collection_2')

        assert track_1_count == 3
        assert track_2_count == 3

    def test_collection_coordinator_picks_from_one_track_at_time(
        self,
        env: simpy.Environment,
        arrival_coordinator: ArrivalCoordinator,
        collection_coordinator: CollectionCoordinator,
        collection_queue: simpy.FilterStore,
        retrofit_queue: simpy.FilterStore,
    ) -> None:
        """Test collection coordinator receives wagons distributed across tracks."""
        # Schedule train with 4 wagons (will be distributed 2 per track)
        wagon_configs = [
            {'id': f'W{i:03d}', 'length': 15.0, 'is_loaded': False, 'needs_retrofit': True} for i in range(1, 5)
        ]

        arrival_coordinator.schedule_train(train_id='T1', arrival_time=0.0, wagon_configs=wagon_configs)

        # Run arrival to distribute wagons
        env.run(until=1.0)

        # Verify wagons were distributed via collection_coordinator.add_wagon()
        assert arrival_coordinator.collection_coordinator.add_wagon.call_count == 4

        # Get wagons from mock calls
        wagons = [call[0][0] for call in arrival_coordinator.collection_coordinator.add_wagon.call_args_list]

        # Verify wagons are distributed across tracks
        track_1_wagons = [w for w in wagons if w.current_track_id == 'collection_1']
        track_2_wagons = [w for w in wagons if w.current_track_id == 'collection_2']

        # Should be evenly distributed (2 per track)
        assert len(track_1_wagons) == 2
        assert len(track_2_wagons) == 2

    def test_multiple_trains_distributed_across_tracks(
        self,
        env: simpy.Environment,
        arrival_coordinator: ArrivalCoordinator,
        collection_queue: simpy.FilterStore,
    ) -> None:
        """Test multiple trains have wagons distributed across tracks."""
        # Schedule two trains
        for train_num in range(1, 3):
            wagon_configs = [
                {'id': f'T{train_num}W{i:03d}', 'length': 15.0, 'is_loaded': False, 'needs_retrofit': True}
                for i in range(1, 4)
            ]
            arrival_coordinator.schedule_train(train_id=f'T{train_num}', arrival_time=0.0, wagon_configs=wagon_configs)

        # Run simulation
        env.run(until=1.0)

        # Check collection_coordinator.add_wagon was called 6 times
        assert arrival_coordinator.collection_coordinator.add_wagon.call_count == 6

        # Get wagons from mock calls
        wagons = [call[0][0] for call in arrival_coordinator.collection_coordinator.add_wagon.call_args_list]
        track_1_wagons = [w for w in wagons if w.current_track_id == 'collection_1']
        track_2_wagons = [w for w in wagons if w.current_track_id == 'collection_2']

        # Should be evenly distributed
        assert len(track_1_wagons) == 3
        assert len(track_2_wagons) == 3

        # Verify FIFO within each track
        # Track 1 should have: T1W001, T1W003, T2W002 (in queue order)
        # Track 2 should have: T1W002, T2W001, T2W003 (in queue order)
        assert track_1_wagons[0].id == 'T1W001'
        assert track_2_wagons[0].id == 'T1W002'

    def test_fifo_maintained_per_track(
        self,
        env: simpy.Environment,
        arrival_coordinator: ArrivalCoordinator,
        collection_queue: simpy.FilterStore,
    ) -> None:
        """Test FIFO order is maintained per track."""
        # Schedule wagons at different times
        arrival_coordinator.schedule_train(
            train_id='T1',
            arrival_time=0.0,
            wagon_configs=[{'id': 'W001', 'length': 15.0, 'is_loaded': False, 'needs_retrofit': True}],
        )

        arrival_coordinator.schedule_train(
            train_id='T2',
            arrival_time=1.0,
            wagon_configs=[{'id': 'W002', 'length': 15.0, 'is_loaded': False, 'needs_retrofit': True}],
        )

        arrival_coordinator.schedule_train(
            train_id='T3',
            arrival_time=2.0,
            wagon_configs=[{'id': 'W003', 'length': 15.0, 'is_loaded': False, 'needs_retrofit': True}],
        )

        # Run simulation
        env.run(until=5.0)

        # Check collection_coordinator.add_wagon was called 3 times
        assert arrival_coordinator.collection_coordinator.add_wagon.call_count == 3

        # Get wagons from mock calls
        wagons = [call[0][0] for call in arrival_coordinator.collection_coordinator.add_wagon.call_args_list]
        track_1_wagons = [w for w in wagons if w.current_track_id == 'collection_1']
        track_2_wagons = [w for w in wagons if w.current_track_id == 'collection_2']

        # Round-robin: W001->track1, W002->track2, W003->track1
        assert len(track_1_wagons) == 2
        assert len(track_2_wagons) == 1

        # FIFO order within track 1: W001 before W003
        track_1_order = [w.id for w in track_1_wagons]
        assert track_1_order == ['W001', 'W003']
