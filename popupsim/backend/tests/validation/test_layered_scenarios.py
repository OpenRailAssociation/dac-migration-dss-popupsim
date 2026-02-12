"""Comprehensive layered timeline tests.

Each scenario has 4 layers:
- Layer 1: Pure travel times (no coupling, no loco prep)
- Layer 2: Rake coupling/decoupling (wagon-to-wagon)
- Layer 3: Locomotive operations (loco coupling + prep, NO rake coupling)
- Layer 4: Complete times (all operations)
"""

from datetime import timedelta
from unittest.mock import Mock

from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
from contexts.retrofit_workflow.domain.events.observability_events import WagonJourneyEvent
import simpy

from .retrofit_timeline_validator import validate_retrofit_timeline_from_docstring


def create_layered_scenario(
    num_workshops: int = 1,
    retrofit_time: float = 10.0,
    workshop_bays: list[int] | None = None,
    retrofit_track_length: float = 80.0,
    # Layer controls
    rake_coupling_time: float = 0.0,
    loco_coupling_time: float = 0.0,
    loco_prep_time: float = 0.0,
) -> Mock:
    """Create scenario with layered time configuration."""
    mock_scenario = Mock()

    if workshop_bays is None:
        workshop_bays = [1] * num_workshops

    # Workshops
    mock_scenario.workshops = []
    for i in range(num_workshops):
        workshop = Mock()
        workshop.id = f'WS{i + 1}'
        workshop.track = f'WS{i + 1}'
        workshop.retrofit_stations = workshop_bays[i]
        mock_scenario.workshops.append(workshop)

    # Locomotives
    mock_scenario.locomotives = [Mock(id='L1', track='loco_parking')]

    # Tracks
    mock_scenario.tracks = [
        Mock(id='collection', type='collection', length=100.0, fillfactor=0.8),
        Mock(id='retrofit', type='retrofit', length=retrofit_track_length, fillfactor=0.9),
        Mock(id='retrofitted', type='retrofitted', length=120.0, fillfactor=0.8),
        Mock(id='parking_area', type='parking', length=200.0, fillfactor=0.7),
        Mock(id='loco_parking', type='loco_parking', length=50.0, fillfactor=0.5),
    ]
    for i in range(num_workshops):
        mock_scenario.tracks.append(Mock(id=f'WS{i + 1}', type='workshop', length=100.0, fillfactor=0.75))

    # Routes (all 1 minute travel time, all SHUNTING type)
    mock_scenario.routes = [
        Mock(
            from_location='loco_parking',
            to_location='collection',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'collection'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='collection',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['collection', 'loco_parking'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='loco_parking',
            to_location='retrofit',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'retrofit'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='retrofit',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['retrofit', 'loco_parking'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='loco_parking',
            to_location='WS1',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'WS1'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='WS1',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['WS1', 'loco_parking'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='loco_parking',
            to_location='WS2',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'WS2'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='WS2',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['WS2', 'loco_parking'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='loco_parking',
            to_location='retrofitted',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'retrofitted'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='retrofitted',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['retrofitted', 'loco_parking'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='loco_parking',
            to_location='parking_area',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'parking_area'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='parking_area',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['parking_area', 'loco_parking'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='collection',
            to_location='retrofit',
            duration=timedelta(minutes=1),
            path=['collection', 'retrofit'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='retrofit',
            to_location='WS1',
            duration=timedelta(minutes=1),
            path=['retrofit', 'WS1'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='retrofit',
            to_location='WS2',
            duration=timedelta(minutes=1),
            path=['retrofit', 'WS2'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='WS1',
            to_location='retrofitted',
            duration=timedelta(minutes=1),
            path=['WS1', 'retrofitted'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='WS2',
            to_location='retrofitted',
            duration=timedelta(minutes=1),
            path=['WS2', 'retrofitted'],
            route_type='SHUNTING',
        ),
        Mock(
            from_location='retrofitted',
            to_location='parking_area',
            duration=timedelta(minutes=1),
            path=['retrofitted', 'parking_area'],
            route_type='SHUNTING',
        ),
    ]

    # Process times - layered configuration
    from unittest.mock import MagicMock

    process_times_mock = MagicMock()
    process_times_mock.wagon_retrofit_time = timedelta(minutes=retrofit_time)
    # Layer 2: Rake coupling/decoupling (wagon-to-wagon)
    process_times_mock.screw_coupling_time = timedelta(
        minutes=rake_coupling_time if rake_coupling_time > 0 else loco_coupling_time
    )
    process_times_mock.screw_decoupling_time = timedelta(
        minutes=rake_coupling_time if rake_coupling_time > 0 else loco_coupling_time
    )
    process_times_mock.dac_coupling_time = timedelta(
        minutes=(rake_coupling_time * 0.5) if rake_coupling_time > 0 else (loco_coupling_time * 0.5)
    )
    process_times_mock.dac_decoupling_time = timedelta(
        minutes=(rake_coupling_time * 0.5) if rake_coupling_time > 0 else (loco_coupling_time * 0.5)
    )
    # Layer 3: Locomotive operations
    process_times_mock.shunting_preparation_time = timedelta(minutes=loco_prep_time)
    process_times_mock.full_brake_test_time = timedelta(minutes=5.0)
    process_times_mock.technical_inspection_time = timedelta(minutes=2.0)
    process_times_mock.brake_continuity_check_time = timedelta(seconds=0.0)

    # Add get_coupling_time method for dynamic loco coupling based on wagon coupler types
    def get_coupling_time(coupler_type: str) -> timedelta:
        coupling_time = loco_coupling_time if loco_coupling_time > 0 else rake_coupling_time
        if coupler_type.upper() == 'DAC':
            return timedelta(minutes=coupling_time * 0.5)
        return timedelta(minutes=coupling_time)

    def get_decoupling_time(coupler_type: str) -> timedelta:
        coupling_time = loco_coupling_time if loco_coupling_time > 0 else rake_coupling_time
        if coupler_type.upper() == 'DAC':
            return timedelta(minutes=coupling_time * 0.5)
        return timedelta(minutes=coupling_time)

    def get_coupling_ticks(coupler_type: str) -> float:
        """Get coupling time in SimPy ticks."""
        from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks

        return timedelta_to_sim_ticks(get_coupling_time(coupler_type))

    def get_decoupling_ticks(coupler_type: str) -> float:
        """Get decoupling time in SimPy ticks."""
        from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks

        return timedelta_to_sim_ticks(get_decoupling_time(coupler_type))

    process_times_mock.get_coupling_time = get_coupling_time
    process_times_mock.get_decoupling_time = get_decoupling_time
    process_times_mock.get_coupling_ticks = get_coupling_ticks
    process_times_mock.get_decoupling_ticks = get_decoupling_ticks
    mock_scenario.process_times = process_times_mock

    mock_scenario.loco_priority_strategy = Mock(value='batch_completion')
    mock_scenario.collection_track_strategy = Mock(value='round_robin')
    mock_scenario.retrofit_selection_strategy = Mock(value='least_busy')
    mock_scenario.parking_selection_strategy = Mock(value='least_busy')
    mock_scenario.parking_strategy = Mock(value='batch_completion')
    mock_scenario.parking_normal_threshold = 0.8
    mock_scenario.parking_critical_threshold = 0.95
    mock_scenario.parking_idle_check_interval = 5.0
    mock_scenario.process_logger = None  # No process logging in tests

    return mock_scenario


def run_layered_test(
    num_wagons: int,
    num_workshops: int,
    retrofit_time: float,
    until: float,
    workshop_bays: list[int] | None = None,
    retrofit_track_length: float = 80.0,
    rake_coupling_time: float = 0.0,
    loco_coupling_time: float = 0.0,
    loco_prep_time: float = 0.0,
) -> tuple[list, Mock]:
    """Run test with layered time configuration."""
    env = simpy.Environment()
    scenario = create_layered_scenario(
        num_workshops,
        retrofit_time,
        workshop_bays,
        retrofit_track_length,
        rake_coupling_time,
        loco_coupling_time,
        loco_prep_time,
    )

    context = RetrofitWorkshopContext(env, scenario)
    events = []
    parked_wagons = set()

    context.initialize()

    # Hook event collector BEFORE starting processes
    if context.event_collector:
        original_wagon_event = context.event_collector.add_wagon_event
        original_loco_event = context.event_collector.add_locomotive_event

        def capture_wagon_event(event) -> None:
            events.append((env.now, event))
            if hasattr(event, 'event_type') and event.event_type == 'PARKED':
                parked_wagons.add(event.wagon_id)
            # Print wagon events for timeline debugging
            if hasattr(event, 'wagon_id') and hasattr(event, 'event_type') and hasattr(event, 'location'):
                print(f't={env.now}: wagon[{event.wagon_id}] {event.event_type} {event.location}')
            original_wagon_event(event)

        def capture_loco_event(event) -> None:
            events.append((env.now, event))
            # Print locomotive events for timeline debugging
            if hasattr(event, 'locomotive_id'):
                event_type = getattr(event, 'event_type', type(event).__name__)
                from_loc = getattr(event, 'from_location', '')
                to_loc = getattr(event, 'to_location', '')
                if from_loc and to_loc:
                    print(f't={env.now}: locomotive[{event.locomotive_id}] {event_type} {from_loc}->{to_loc}')
                else:
                    print(f't={env.now}: locomotive[{event.locomotive_id}] {event_type}')
            original_loco_event(event)

        context.event_collector.add_wagon_event = capture_wagon_event
        context.event_collector.add_locomotive_event = capture_loco_event

        # Re-wire coordinators BEFORE starting processes
        if context.collection_coordinator and hasattr(context.collection_coordinator, 'config'):
            context.collection_coordinator.config.wagon_event_publisher = capture_wagon_event
            context.collection_coordinator.config.loco_event_publisher = capture_loco_event
        if context.workshop_coordinator:
            if hasattr(context.workshop_coordinator, 'config'):
                context.workshop_coordinator.config.wagon_event_publisher = capture_wagon_event
                context.workshop_coordinator.config.loco_event_publisher = capture_loco_event
            else:
                context.workshop_coordinator.wagon_event_publisher = capture_wagon_event
                context.workshop_coordinator.loco_event_publisher = capture_loco_event
        if context.parking_coordinator:
            if hasattr(context.parking_coordinator, 'config'):
                context.parking_coordinator.config.wagon_event_publisher = capture_wagon_event
                context.parking_coordinator.config.loco_event_publisher = capture_loco_event
                context.parking_coordinator.config.batch_event_publisher = lambda e: events.append((env.now, e))
            else:
                context.parking_coordinator.wagon_event_publisher = capture_wagon_event
                context.parking_coordinator.loco_event_publisher = capture_loco_event

    context.start_processes()

    # Add wagons to collection queue
    from contexts.retrofit_workflow.domain.entities.wagon import Wagon
    from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
    from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType

    for i in range(num_wagons):
        wagon = Wagon(
            id=f'W{i + 1:02d}',
            length=15.0,
            coupler_a=Coupler(CouplerType.SCREW, 'A'),
            coupler_b=Coupler(CouplerType.SCREW, 'B'),
        )
        wagon.classify()
        wagon.move_to('collection')
        wagon.current_track_id = 'collection'  # Set physical track ID

        arrival_event = WagonJourneyEvent(
            timestamp=0.0, wagon_id=wagon.id, event_type='ARRIVED', location='collection', status='ARRIVED'
        )
        events.append((0.0, arrival_event))
        # Add wagon via collection coordinator instead of directly to queue
        if context.collection_coordinator:
            context.collection_coordinator.add_wagon(wagon)
        else:
            context.collection_queue.put(wagon)

    # Termination process
    def termination_process():
        while True:
            yield env.timeout(1)
            if len(parked_wagons) >= num_wagons:
                break

    env.process(termination_process())
    env.run(until=until)

    mock_analytics = Mock()
    mock_analytics.get_metrics.return_value = {'event_history': events}

    return events, mock_analytics


# ============================================================================
# SCENARIO 1: Single Wagon, Single Bay
# ============================================================================


def test_scenario1_layer1_single_wagon_pure_travel() -> None:
    """Scenario 1, Layer 1: Single wagon with pure travel times only.

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: locomotive[L1] MOVING collection->retrofit
    t=2: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=2: locomotive[L1] MOVING retrofit->loco_parking
    t=3: locomotive[L1] MOVING loco_parking->retrofit
    t=4: locomotive[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFIT_STARTED WS1
    t=5: locomotive[L1] MOVING WS1->loco_parking
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=15: locomotive[L1] MOVING loco_parking->WS1
    t=16: locomotive[L1] MOVING WS1->retrofitted
    t=17: locomotive[L1] MOVING retrofitted->loco_parking
    t=18: locomotive[L1] MOVING loco_parking->retrofitted
    t=19: locomotive[L1] MOVING retrofitted->parking_area
    t=20: wagon[W01] PARKED parking_area
    """
    events, analytics = run_layered_test(1, 1, 10.0, 30.0, workshop_bays=[1])

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 1

    validate_retrofit_timeline_from_docstring(events, test_scenario1_layer1_single_wagon_pure_travel, analytics)


def test_scenario1_layer3_single_wagon_with_loco_ops() -> None:
    """Scenario 1, Layer 3: Single wagon with locomotive operations (no rake coupling).

    Loco coupling: 1 min (SCREW before retrofit), 0.5 min (DAC after retrofit)
    Shunting prep: 1 min
    Total prep: 2 min (SCREW), 1.5 min (DAC)

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=4: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=9: wagon[W01] RETROFIT_STARTED WS1
    t=19: wagon[W01] RETROFIT_COMPLETED WS1
    t=26.5: wagon[W01] PARKED parking_area
    """
    events, analytics = run_layered_test(
        1, 1, 10.0, 50.0, workshop_bays=[1], loco_coupling_time=1.0, loco_prep_time=1.0
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 1

    validate_retrofit_timeline_from_docstring(events, test_scenario1_layer3_single_wagon_with_loco_ops, analytics)


# ============================================================================
# SCENARIO 2: Two Wagons, One Bay (Sequential Processing)
# ============================================================================


def test_scenario2_layer1_two_wagons_one_bay_pure_travel() -> None:
    """Scenario 2, Layer 1: Two wagons, one bay, pure travel times.

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=2: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W02] ON_RETROFIT_TRACK retrofit
    t=5: wagon[W01] RETROFIT_STARTED WS1
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=19: wagon[W01] PARKED parking_area
    t=20: wagon[W02] RETROFIT_STARTED WS1
    t=30: wagon[W02] RETROFIT_COMPLETED WS1
    t=36: wagon[W02] PARKED parking_area
    """
    events, analytics = run_layered_test(2, 1, 10.0, 50.0, workshop_bays=[1])

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 2

    validate_retrofit_timeline_from_docstring(events, test_scenario2_layer1_two_wagons_one_bay_pure_travel, analytics)


def test_scenario2_layer3_two_wagons_one_bay_with_loco_ops() -> None:
    """Scenario 2, Layer 3: Two wagons, one bay, with locomotive operations.

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=4: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=4: wagon[W02] ON_RETROFIT_TRACK retrofit
    t=9: wagon[W01] RETROFIT_STARTED WS1
    t=19: wagon[W01] RETROFIT_COMPLETED WS1
    t=26.5: wagon[W01] PARKED parking_area
    t=32.5: wagon[W02] RETROFIT_STARTED WS1
    t=42.5: wagon[W02] RETROFIT_COMPLETED WS1
    t=50: wagon[W02] PARKED parking_area
    """
    events, analytics = run_layered_test(
        2, 1, 10.0, 80.0, workshop_bays=[1], loco_coupling_time=1.0, loco_prep_time=1.0
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 2

    validate_retrofit_timeline_from_docstring(events, test_scenario2_layer3_two_wagons_one_bay_with_loco_ops, analytics)


# ============================================================================
# SCENARIO 3: Two Wagons, Two Bays (Parallel Processing)
# ============================================================================


def test_scenario3_layer1_two_wagons_two_bays_pure_travel() -> None:
    """Scenario 3, Layer 1: Two wagons, two bays, pure travel times.

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: locomotive[L1] MOVING collection->retrofit
    t=2: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W02] ON_RETROFIT_TRACK retrofit
    t=2: locomotive[L1] MOVING retrofit->loco_parking
    t=3: locomotive[L1] MOVING loco_parking->retrofit
    t=4: locomotive[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFIT_STARTED WS1
    t=5: wagon[W02] RETROFIT_STARTED WS1
    t=5: locomotive[L1] MOVING WS1->loco_parking
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=15: wagon[W02] RETROFIT_COMPLETED WS1
    t=15: locomotive[L1] MOVING loco_parking->WS1
    t=16: locomotive[L1] MOVING WS1->retrofitted
    t=17: locomotive[L1] MOVING retrofitted->loco_parking
    t=18: locomotive[L1] MOVING loco_parking->retrofitted
    t=19: locomotive[L1] MOVING retrofitted->parking_area
    t=20: wagon[W01] PARKED parking_area
    t=20: wagon[W02] PARKED parking_area
    """
    events, analytics = run_layered_test(2, 1, 10.0, 30.0, workshop_bays=[2])

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 2

    validate_retrofit_timeline_from_docstring(events, test_scenario3_layer1_two_wagons_two_bays_pure_travel, analytics)


def test_scenario3_layer3_two_wagons_two_bays_with_loco_ops() -> None:
    """Scenario 3, Layer 3: Two wagons, two bays, with locomotive operations.

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=6: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=6: wagon[W02] ON_RETROFIT_TRACK retrofit
    t=10: wagon[W01] RETROFIT_STARTED WS1
    t=10: wagon[W02] RETROFIT_STARTED WS1
    t=20: wagon[W01] RETROFIT_COMPLETED WS1
    t=20: wagon[W02] RETROFIT_COMPLETED WS1
    t=29: wagon[W01] PARKED parking_area
    t=29: wagon[W02] PARKED parking_area
    """
    events, analytics = run_layered_test(
        2, 1, 10.0, 50.0, workshop_bays=[2], loco_coupling_time=1.0, loco_prep_time=1.0
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 2

    validate_retrofit_timeline_from_docstring(
        events, test_scenario3_layer3_two_wagons_two_bays_with_loco_ops, analytics
    )
