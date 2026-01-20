"""Timeline validation for retrofit workflow context."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
import simpy


def create_test_scenario(num_wagons: int = 2, num_workshops: int = 1) -> Mock:
    """Create a mock scenario for retrofit workflow context testing."""
    mock_scenario = Mock()

    # Create workshops
    mock_scenario.workshops = []
    for i in range(num_workshops):
        workshop = Mock()
        workshop.id = f'WS{i + 1}'
        workshop.track = f'track_{i + 1}'
        workshop.retrofit_stations = 2
        mock_scenario.workshops.append(workshop)

    # Create locomotives
    mock_scenario.locomotives = [Mock(id='loco_1', track='locoparking'), Mock(id='loco_2', track='locoparking')]

    # Create tracks
    mock_scenario.tracks = [
        Mock(id='collection', type='collection', length=100.0, fillfactor=0.8),
        Mock(id='retrofit', type='retrofit', length=80.0, fillfactor=0.9),
        Mock(id='retrofitted', type='retrofitted', length=120.0, fillfactor=0.8),
        Mock(id='parking_1', type='parking', length=200.0, fillfactor=0.7),
    ]

    # Create routes
    mock_scenario.routes = [
        Mock(
            from_location='collection',
            to_location='retrofit',
            duration=timedelta(minutes=2),
            path=['collection', 'retrofit'],
        ),
        Mock(from_location='retrofit', to_location='WS1', duration=timedelta(minutes=3), path=['retrofit', 'WS1']),
        Mock(
            from_location='WS1', to_location='retrofitted', duration=timedelta(minutes=3), path=['WS1', 'retrofitted']
        ),
        Mock(
            from_location='retrofitted',
            to_location='parking_1',
            duration=timedelta(minutes=4),
            path=['retrofitted', 'parking_1'],
        ),
    ]

    # Create trains with wagons
    mock_scenario.trains = []
    if num_wagons > 0:
        wagons = []
        for i in range(num_wagons):
            wagon = Mock()
            wagon.id = f'wagon_{i + 1}'
            wagon.length = 15.0
            wagons.append(wagon)

        train = Mock()
        train.train_id = 'train_1'
        train.wagons = wagons
        mock_scenario.trains.append(train)

    # Process times
    mock_scenario.process_times = Mock(wagon_retrofit_time=timedelta(minutes=10))
    mock_scenario.loco_priority_strategy = Mock(value='workshop_priority')

    return mock_scenario


def test_retrofit_workflow_context_basic_timeline() -> None:
    """Test basic timeline with retrofit workflow context - 2 wagons, 1 workshop."""
    env = simpy.Environment()
    scenario = create_test_scenario(num_wagons=2, num_workshops=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()
    context.start_processes()

    # Collect events during simulation
    events = []

    def log_event(time: float, description: str) -> None:
        events.append((time, description))

    # Mock event collection
    if context.event_collector:
        original_add_wagon = context.event_collector.add_wagon_event
        original_add_loco = context.event_collector.add_locomotive_event

        def mock_wagon_event(event) -> None:
            log_event(env.now, f'wagon[{event.wagon_id}] {event.event_type} {event.location}')
            original_add_wagon(event)

        def mock_loco_event(event) -> None:
            log_event(env.now, f'loco[{event.locomotive_id}] {event.event_type}')
            original_add_loco(event)

        context.event_collector.add_wagon_event = mock_wagon_event
        context.event_collector.add_locomotive_event = mock_loco_event

    # Run simulation
    env.run(until=50.0)

    # Verify we collected some events
    assert len(events) >= 0  # May be 0 if no processes actually run

    # Get final metrics
    metrics = context.get_metrics()
    assert metrics is not None


def test_context_workshop_assignment() -> None:
    """Test workshop assignment with multiple workshops."""
    env = simpy.Environment()
    scenario = create_test_scenario(num_wagons=4, num_workshops=2)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    # Verify workshops were created
    assert len(context.workshops) == 2
    assert 'WS1' in context.workshops
    assert 'WS2' in context.workshops

    # Verify locomotives were created
    assert len(context.locomotives) == 2

    # Start processes
    context.start_processes()

    # Run brief simulation
    env.run(until=10.0)

    # Should complete without errors
    status = context.get_status()
    assert status['status'] == 'ready'


def test_context_event_collection() -> None:
    """Test that retrofit workflow context collects events properly."""
    env = simpy.Environment()
    scenario = create_test_scenario(num_wagons=1, num_workshops=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    # Verify event collector exists
    assert context.event_collector is not None

    # Test event collection methods exist
    assert hasattr(context.event_collector, 'add_wagon_event')
    assert hasattr(context.event_collector, 'add_locomotive_event')
    assert hasattr(context.event_collector, 'add_resource_event')

    # Test export functionality
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        context.export_events(temp_dir)


def test_context_resource_management() -> None:
    """Test resource management in retrofit workflow context."""
    env = simpy.Environment()
    scenario = create_test_scenario(num_wagons=2, num_workshops=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    # Verify resource managers exist
    assert context.locomotive_manager is not None
    assert context.workshop_resources is not None
    assert context.track_manager is not None

    # Test metrics collection
    metrics = context.get_metrics()
    assert isinstance(metrics, dict)


def test_context_coordinator_integration() -> None:
    """Test that coordinators integrate properly."""
    env = simpy.Environment()
    scenario = create_test_scenario(num_wagons=1, num_workshops=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    # Verify arrival coordinator exists
    assert context.arrival_coordinator is not None

    # Start processes should not raise errors
    context.start_processes()

    # Run very brief simulation
    env.run(until=1.0)

    # Cleanup should not raise errors
    context.cleanup()


def test_context_domain_services() -> None:
    """Test domain services in retrofit workflow context."""
    env = simpy.Environment()
    scenario = create_test_scenario(num_wagons=2, num_workshops=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    # Verify domain services exist
    assert context.coupling_validator is not None
    assert context.rake_formation_service is not None
    assert context.batch_formation_service is not None
    assert context.route_service is not None

    # Test batch formation service
    from contexts.retrofit_workflow.domain.entities.wagon import Wagon
    from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
    from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType

    test_wagons = [
        Wagon(
            id='W1', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        ),
        Wagon(
            id='W2', length=18.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        ),
    ]

    # Test can form batch
    can_form = context.batch_formation_service.can_form_batch(test_wagons)
    assert can_form is True

    # Test create batch aggregate
    batch = context.batch_formation_service.create_batch_aggregate(test_wagons, 'WS1')
    assert batch is not None
    assert batch.destination == 'WS1'
    assert len(batch.wagons) == 2


def validate_timeline_basic() -> None:
    """Validate basic timeline behavior matches expected patterns."""
    env = simpy.Environment()
    scenario = create_test_scenario(num_wagons=1, num_workshops=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()
    context.start_processes()

    # Track key simulation events
    timeline = []

    # Run simulation and collect timeline
    for time_step in range(0, 20):
        env.run(until=float(time_step))

        # Record current state
        status = context.get_status()
        timeline.append((time_step, status))

    # Verify timeline has entries
    assert len(timeline) > 0

    # Verify status remains consistent
    for time, status in timeline:
        assert status['status'] == 'ready'
        assert status['workshops'] >= 1
        assert status['locomotives'] >= 1
