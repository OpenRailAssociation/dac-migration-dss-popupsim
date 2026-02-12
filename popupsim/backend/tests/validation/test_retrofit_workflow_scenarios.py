"""Timeline validation scenarios for retrofit workshops context."""

from datetime import timedelta
import logging
from unittest.mock import Mock

from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
from contexts.retrofit_workflow.domain.events.observability_events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.exceptions import SimulationDeadlockError
import simpy

from .retrofit_timeline_validator import validate_retrofit_timeline_from_docstring

logger = logging.getLogger(__name__)


def create_test_scenario(
    num_wagons: int,  # noqa: ARG001
    num_workshops: int = 1,
    retrofit_time: float = 10.0,
    workshop_bays: list[int] | None = None,
    retrofit_track_length: float = 80.0,
    coupling_time: float = 0.0,
) -> Mock:
    """Create a mock scenario for timeline testing.

    Args:
        num_wagons: Number of wagons to process
        num_workshops: Number of workshops
        retrofit_time: Time for retrofit in minutes
        workshop_bays: List of bay counts per workshop. If None, defaults to [1] for each workshop
        retrofit_track_length: Length of retrofit track in meters
        coupling_time: Coupling/decoupling time in minutes
    """
    mock_scenario = Mock()

    # Default to 1 bay per workshop if not specified
    if workshop_bays is None:
        workshop_bays = [1] * num_workshops
    elif len(workshop_bays) != num_workshops:
        raise ValueError(f'workshop_bays length ({len(workshop_bays)}) must match num_workshops ({num_workshops})')

    # Create workshops
    mock_scenario.workshops = []
    for i in range(num_workshops):
        workshop = Mock()
        workshop.id = f'WS{i + 1}'
        workshop.track = f'WS{i + 1}'
        workshop.retrofit_stations = workshop_bays[i]
        mock_scenario.workshops.append(workshop)

    # Create locomotives
    mock_scenario.locomotives = [Mock(id='L1', track='loco_parking')]

    # Create tracks
    mock_scenario.tracks = [
        Mock(id='collection', type='collection', length=100.0, fillfactor=0.8),
        Mock(id='retrofit', type='retrofit', length=retrofit_track_length, fillfactor=0.9),
        Mock(id='retrofitted', type='retrofitted', length=120.0, fillfactor=0.8),
        Mock(id='parking_area', type='parking', length=200.0, fillfactor=0.7),
        Mock(id='loco_parking', type='loco_parking', length=50.0, fillfactor=0.5),
    ]

    # Add workshop tracks
    for i in range(num_workshops):
        mock_scenario.tracks.append(Mock(id=f'WS{i + 1}', type='workshop', length=100.0, fillfactor=0.75))

    # Create routes
    mock_scenario.routes = [
        # Locomotive movements
        Mock(
            from_location='loco_parking',
            to_location='collection',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'collection'],
        ),
        Mock(
            from_location='collection',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['collection', 'loco_parking'],
        ),
        Mock(
            from_location='loco_parking',
            to_location='retrofit',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'retrofit'],
        ),
        Mock(
            from_location='retrofit',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['retrofit', 'loco_parking'],
        ),
        Mock(
            from_location='loco_parking', to_location='WS1', duration=timedelta(minutes=1), path=['loco_parking', 'WS1']
        ),
        Mock(
            from_location='WS1', to_location='loco_parking', duration=timedelta(minutes=1), path=['WS1', 'loco_parking']
        ),
        Mock(
            from_location='loco_parking', to_location='WS2', duration=timedelta(minutes=1), path=['loco_parking', 'WS2']
        ),
        Mock(
            from_location='WS2', to_location='loco_parking', duration=timedelta(minutes=1), path=['WS2', 'loco_parking']
        ),
        Mock(
            from_location='loco_parking',
            to_location='retrofitted',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'retrofitted'],
        ),
        Mock(
            from_location='retrofitted',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['retrofitted', 'loco_parking'],
        ),
        Mock(
            from_location='loco_parking',
            to_location='parking_area',
            duration=timedelta(minutes=1),
            path=['loco_parking', 'parking_area'],
        ),
        Mock(
            from_location='parking_area',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            path=['parking_area', 'loco_parking'],
        ),
        # Wagon transport routes
        Mock(
            from_location='collection',
            to_location='retrofit',
            duration=timedelta(minutes=1),
            path=['collection', 'retrofit'],
        ),
        Mock(from_location='retrofit', to_location='WS1', duration=timedelta(minutes=1), path=['retrofit', 'WS1']),
        Mock(from_location='retrofit', to_location='WS2', duration=timedelta(minutes=1), path=['retrofit', 'WS2']),
        Mock(
            from_location='WS1', to_location='retrofitted', duration=timedelta(minutes=1), path=['WS1', 'retrofitted']
        ),
        Mock(
            from_location='WS2', to_location='retrofitted', duration=timedelta(minutes=1), path=['WS2', 'retrofitted']
        ),
        Mock(
            from_location='retrofitted',
            to_location='parking_area',
            duration=timedelta(minutes=1),
            path=['retrofitted', 'parking_area'],
        ),
    ]

    # Process times
    mock_scenario.process_times = Mock(
        wagon_retrofit_time=timedelta(minutes=retrofit_time),
        screw_coupling_time=timedelta(minutes=1.0 if coupling_time > 0 else 0.0),
        screw_decoupling_time=timedelta(minutes=1.0 if coupling_time > 0 else 0.0),
        dac_coupling_time=timedelta(minutes=0.5 if coupling_time > 0 else 0.0),
        dac_decoupling_time=timedelta(minutes=0.5 if coupling_time > 0 else 0.0),
        brake_continuity_check_time=timedelta(seconds=0.0),
        # Locomotive operations - only add if coupling_time > 0 (for coupling tests)
        shunting_preparation_time=timedelta(minutes=1.0 if coupling_time > 0 else 0.0),
        full_brake_test_time=timedelta(minutes=5.0 if coupling_time > 0 else 0.0),
        technical_inspection_time=timedelta(minutes=2.0 if coupling_time > 0 else 0.0),
    )
    # Add get_coupling_time method for dynamic loco coupling
    mock_scenario.process_times.get_coupling_time = lambda coupler_type: (
        timedelta(minutes=0.5 if coupling_time > 0 else 0.0)
        if coupler_type.upper() == 'DAC'
        else timedelta(minutes=1.0 if coupling_time > 0 else 0.0)
    )
    mock_scenario.process_times.get_decoupling_time = lambda coupler_type: (
        timedelta(minutes=0.5 if coupling_time > 0 else 0.0)
        if coupler_type.upper() == 'DAC'
        else timedelta(minutes=1.0 if coupling_time > 0 else 0.0)
    )

    # Add get_coupling_ticks and get_decoupling_ticks methods
    def get_coupling_ticks(coupler_type: str) -> float:
        from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks

        return timedelta_to_sim_ticks(
            timedelta(minutes=0.5 if coupling_time > 0 else 0.0)
            if coupler_type.upper() == 'DAC'
            else timedelta(minutes=1.0 if coupling_time > 0 else 0.0)
        )

    def get_decoupling_ticks(coupler_type: str) -> float:
        from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks

        return timedelta_to_sim_ticks(
            timedelta(minutes=0.5 if coupling_time > 0 else 0.0)
            if coupler_type.upper() == 'DAC'
            else timedelta(minutes=1.0 if coupling_time > 0 else 0.0)
        )

    mock_scenario.process_times.get_coupling_ticks = get_coupling_ticks
    mock_scenario.process_times.get_decoupling_ticks = get_decoupling_ticks

    # Locomotive priority strategy for coordination
    mock_scenario.loco_priority_strategy = Mock(value='batch_completion')

    # Parking strategy configuration
    mock_scenario.parking_strategy = 'opportunistic'  # Use opportunistic for tests
    mock_scenario.parking_normal_threshold = 0.5
    mock_scenario.parking_critical_threshold = 0.8
    mock_scenario.parking_idle_check_interval = 1.0

    # Track selection strategies
    mock_scenario.collection_track_strategy = Mock(value='round_robin')
    mock_scenario.retrofit_selection_strategy = Mock(value='first_available')
    mock_scenario.parking_selection_strategy = Mock(value='best_fit')
    mock_scenario.id = 'test_scenario'

    return mock_scenario


def run_timeline_test(  # noqa: PLR0912
    num_wagons: int,
    num_workshops: int,
    retrofit_time: float,
    until: float,
    workshop_bays: list[int] | None = None,
    retrofit_track_length: float = 80.0,
    coupling_time: float = 0.0,
) -> tuple[list, Mock]:
    """Run  operations context test and collect events."""
    env = simpy.Environment()
    scenario = create_test_scenario(
        num_wagons, num_workshops, retrofit_time, workshop_bays, retrofit_track_length, coupling_time
    )

    # Create context
    context = RetrofitWorkshopContext(env, scenario)

    # Hook into the event collector BEFORE initialization
    events = []
    parked_wagons = set()  # Track parked wagons for termination

    if hasattr(context, 'event_collector') and context.event_collector is None:
        # Event collector will be created during initialization
        pass

    context.initialize()

    # Now hook into the initialized event collector
    if context.event_collector:
        original_wagon_event = context.event_collector.add_wagon_event
        original_loco_event = context.event_collector.add_locomotive_event
        original_batch_event = context.event_collector.add_batch_event

        def capture_wagon_event(event) -> None:
            events.append((env.now, event))
            # Track parked wagons for termination
            if hasattr(event, 'event_type') and event.event_type == 'PARKED':
                parked_wagons.add(event.wagon_id)
                print(f'Wagon {event.wagon_id} parked. Total parked: {len(parked_wagons)}/{num_wagons}')
            original_wagon_event(event)

        def capture_loco_event(event) -> None:
            events.append((env.now, event))
            original_loco_event(event)

        def capture_batch_event(event) -> None:
            print(f'Capturing batch event: {type(event).__name__} at t={env.now}')
            events.append((env.now, event))
            original_batch_event(event)

        context.event_collector.add_wagon_event = capture_wagon_event
        context.event_collector.add_locomotive_event = capture_loco_event
        context.event_collector.add_batch_event = capture_batch_event

        # IMPORTANT: Re-wire the coordinators to use the new event publishers
        if context.collection_coordinator:
            # CollectionCoordinator uses config pattern
            if hasattr(context.collection_coordinator, 'config'):
                context.collection_coordinator.config.batch_event_publisher = capture_batch_event
                context.collection_coordinator.config.loco_event_publisher = capture_loco_event
                context.collection_coordinator.config.wagon_event_publisher = capture_wagon_event
            else:
                context.collection_coordinator.batch_event_publisher = capture_batch_event
                context.collection_coordinator.loco_event_publisher = capture_loco_event
                context.collection_coordinator.wagon_event_publisher = capture_wagon_event

        if context.workshop_coordinator:
            # WorkshopCoordinator not yet refactored to config pattern
            if hasattr(context.workshop_coordinator, 'config'):
                context.workshop_coordinator.config.loco_event_publisher = capture_loco_event
                context.workshop_coordinator.config.wagon_event_publisher = capture_wagon_event
            else:
                # Direct assignment for SOLIDWorkshopCoordinator
                context.workshop_coordinator._event_publisher = capture_wagon_event
                if hasattr(context.workshop_coordinator, 'loco_event_publisher'):
                    context.workshop_coordinator.loco_event_publisher = capture_loco_event
                if hasattr(context.workshop_coordinator, 'wagon_event_publisher'):
                    context.workshop_coordinator.wagon_event_publisher = capture_wagon_event

        if context.parking_coordinator:
            # ParkingCoordinator not yet refactored to config pattern
            if hasattr(context.parking_coordinator, 'config'):
                context.parking_coordinator.config.batch_event_publisher = capture_batch_event
                context.parking_coordinator.config.loco_event_publisher = capture_loco_event
                context.parking_coordinator.config.wagon_event_publisher = capture_wagon_event
            else:
                context.parking_coordinator.batch_event_publisher = capture_batch_event
                context.parking_coordinator.loco_event_publisher = capture_loco_event
                context.parking_coordinator.wagon_event_publisher = capture_wagon_event

    # Start processes
    context.start_processes()
    print(
        f'Started coordinators: collection={context.collection_coordinator is not None}, workshop={context.workshop_coordinator is not None}, parking={context.parking_coordinator is not None}'
    )

    # Add train arrival event
    from contexts.external_trains.domain.events.train_events import TrainArrivedEvent
    from contexts.external_trains.domain.value_objects.arrival_metrics import ArrivalMetrics
    from contexts.external_trains.domain.value_objects.train_id import TrainId

    train_arrival_event = TrainArrivedEvent(
        train_id=TrainId('T1'),
        wagons=[],  # Empty for now, wagons are added separately
        arrival_metrics=ArrivalMetrics(scheduled_time=0.0, actual_time=0.0, wagon_count=num_wagons),
        timestamp=0.0,
    )
    events.append((0.0, train_arrival_event))

    # Simulate train arrival by adding wagons to collection queue
    for i in range(num_wagons):
        from contexts.retrofit_workflow.domain.entities.wagon import Wagon
        from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
        from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType

        wagon = Wagon(
            id=f'W{i + 1:02d}',
            length=15.0,
            coupler_a=Coupler(CouplerType.SCREW, 'A'),
            coupler_b=Coupler(CouplerType.SCREW, 'B'),
        )

        # Set wagon to classified status so it can be processed
        wagon.classify()
        wagon.move_to('collection')
        wagon.current_track_id = 'collection'  # Set physical track ID for coordinator

        # Add wagon arrival event manually

        arrival_event = WagonJourneyEvent(
            timestamp=0.0, wagon_id=wagon.id, event_type='ARRIVED', location='collection', status='ARRIVED'
        )
        events.append((0.0, arrival_event))

        # Add wagon via collection coordinator
        context.collection_coordinator.add_wagon(wagon)
        print(f'Added wagon {wagon.id} to collection coordinator')

    # Create termination process
    def termination_process():
        while True:
            yield env.timeout(1)  # Check every minute
            if len(parked_wagons) >= num_wagons:
                print(f'All {num_wagons} wagons parked. Terminating simulation at t={env.now}')
                break

    env.process(termination_process())

    # Run simulation with exception handling
    try:
        env.run(until=until)
    except SimulationDeadlockError as e:
        logger.error(f'Simulation stopped due to deadlock: {e}')
        print(f'\n{"=" * 80}')
        print('SIMULATION STOPPED GRACEFULLY')
        print(f'{"=" * 80}')
        print(f'Reason: {e}')
        print(f'Context: {e.context}')
        print(f'Time: {env.now}')
        print(f'Wagons parked: {len(parked_wagons)}/{num_wagons}')
        print(f'{"=" * 80}\n')
        # Re-raise to allow test to handle it
        raise

    # Print all events for debugging
    print(f'\nTotal events captured: {len(events)}')
    print('\n' + '=' * 80)
    print('ACTUAL TIMELINE FROM SIMULATION:')
    print('=' * 80)
    for t, e in sorted(events, key=lambda x: x[0]):
        event_type = type(e).__name__
        if event_type == 'TrainArrivedEvent':
            train_id = e.train_id.id if hasattr(e.train_id, 'id') else str(e.train_id)
            print(f't={int(t)}: train[{train_id}] ARRIVED collection')
        elif event_type == 'WagonJourneyEvent':
            print(f't={int(t)}: wagon[{e.wagon_id}] {e.event_type} {e.location}')
        elif event_type == 'BatchFormed':
            wagon_list = ','.join(e.wagon_ids)
            print(f't={int(t)}: batch[{e.batch_id}] FORMED wagons={wagon_list}')
        elif event_type == 'BatchTransportStarted':
            print(f't={int(t)}: batch[{e.batch_id}] TRANSPORT_STARTED destination={e.destination}')
        elif event_type == 'BatchArrivedAtDestination':
            print(f't={int(t)}: batch[{e.batch_id}] ARRIVED_AT_DESTINATION {e.destination}')
        elif event_type == 'LocomotiveMovementEvent':
            if hasattr(e, 'purpose') and e.purpose:
                print(f't={int(t)}: locomotive[{e.locomotive_id}] {e.event_type} {e.purpose}')
            elif hasattr(e, 'from_location') and hasattr(e, 'to_location'):
                print(f't={int(t)}: locomotive[{e.locomotive_id}] MOVING {e.from_location}->{e.to_location}')
            else:
                print(f't={int(t)}: locomotive[{e.locomotive_id}] {e.event_type}')
    print('=' * 80 + '\n')

    # Create mock analytics context for compatibility
    mock_analytics = Mock()
    mock_analytics.get_metrics.return_value = {'event_history': events}

    return events, mock_analytics


def test_single_wagon_single_station() -> None:
    """Test 1 wagon, 1 station - validates state at each timestep.

    TIMELINE:
    t=0: train[T1] ARRIVED collection
    t=0: wagon[W01] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: batch[*] FORMED wagons=W01
    t=1: locomotive[L1] ALLOCATED batch_transport
    t=1: batch[*] TRANSPORT_STARTED destination=retrofit
    t=1: locomotive[L1] MOVING collection->retrofit
    t=2: batch[*] ARRIVED_AT_DESTINATION retrofit
    t=2: locomotive[L1] MOVING retrofit->loco_parking
    t=3: locomotive[L1] MOVING loco_parking->retrofit
    t=4: locomotive[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFIT_STARTED WS1
    t=5: locomotive[L1] MOVING WS1->loco_parking
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=15: locomotive[L1] MOVING loco_parking->WS1
    t=16: locomotive[L1] MOVING WS1->retrofitted
    t=17: locomotive[L1] MOVING retrofitted->loco_parking
    t=17: batch[*] FORMED wagons=W01
    t=18: locomotive[L1] ALLOCATED batch_transport
    t=19: batch[*] TRANSPORT_STARTED destination=parking_area
    t=19: locomotive[L1] MOVING retrofitted->parking_area
    t=20: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=20: wagon[W01] PARKED parking_area
    t=20: locomotive[L1] MOVING parking_area->loco_parking
    """
    events, analytics_context = run_timeline_test(1, 1, 10.0, 30.0)  # Reduced timeout

    # Current status: Only manual arrival events are generated
    # The  operations context coordinators are not yet fully functional
    # TODO: Implement full workflow processing in coordinators

    # Verify we have at least the manual arrival event
    assert len(events) >= 1

    # Verify the arrival event is correct
    arrival_events = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'ARRIVED']
    assert len(arrival_events) >= 1
    assert arrival_events[0].wagon_id == 'W01'
    assert arrival_events[0].location == 'collection'

    # Enable timeline validation to compare expected vs actual
    validate_retrofit_timeline_from_docstring(events, test_single_wagon_single_station, analytics_context)


def test_two_wagons_one_station() -> None:
    """Test 2 wagons, 1 station with one bay.

    TIMELINE:
    t=0: train[T1] ARRIVED collection
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: batch[*] FORMED wagons=W01,W02
    t=1: locomotive[L1] ALLOCATED batch_transport
    t=1: batch[*] TRANSPORT_STARTED destination=retrofit
    t=1: locomotive[L1] MOVING collection->retrofit
    t=2: batch[*] ARRIVED_AT_DESTINATION retrofit
    t=2: locomotive[L1] MOVING retrofit->loco_parking
    t=3: locomotive[L1] MOVING loco_parking->retrofit
    t=4: locomotive[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFIT_STARTED WS1
    t=5: locomotive[L1] MOVING WS1->loco_parking
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=15: locomotive[L1] MOVING loco_parking->WS1
    t=16: locomotive[L1] MOVING WS1->retrofitted
    t=17: locomotive[L1] MOVING retrofitted->loco_parking
    t=17: batch[*] FORMED wagons=W01
    t=18: locomotive[L1] ALLOCATED batch_transport
    t=18: locomotive[L1] MOVING loco_parking->retrofitted
    t=19: batch[*] TRANSPORT_STARTED destination=parking_area
    t=19: locomotive[L1] MOVING retrofitted->parking_area
    t=20: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=20: wagon[W01] PARKED parking_area
    t=20: locomotive[L1] MOVING parking_area->loco_parking
    t=21: locomotive[L1] MOVING loco_parking->retrofit
    t=22: locomotive[L1] MOVING retrofit->WS1
    t=23: wagon[W02] RETROFIT_STARTED WS1
    t=23: locomotive[L1] MOVING WS1->loco_parking
    t=33: wagon[W02] RETROFIT_COMPLETED WS1
    t=33: locomotive[L1] MOVING loco_parking->WS1
    t=34: locomotive[L1] MOVING WS1->retrofitted
    t=35: locomotive[L1] MOVING retrofitted->loco_parking
    t=35: batch[*] FORMED wagons=W02
    t=36: locomotive[L1] ALLOCATED batch_transport
    t=36: locomotive[L1] MOVING loco_parking->retrofitted
    t=37: batch[*] TRANSPORT_STARTED destination=parking_area
    t=37: locomotive[L1] MOVING retrofitted->parking_area
    t=38: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=38: wagon[W02] PARKED parking_area
    t=38: locomotive[L1] MOVING parking_area->loco_parking
    """
    events, analytics_context = run_timeline_test(2, 1, 10.0, 50.0, workshop_bays=[1])

    # Verify we have arrival events for both wagons
    arrival_events = [
        e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'ARRIVED' and hasattr(e, 'wagon_id')
    ]
    assert len(arrival_events) >= 2
    wagon_ids = {e.wagon_id for e in arrival_events}
    assert 'W01' in wagon_ids
    assert 'W02' in wagon_ids

    # Verify both wagons completed retrofit
    retrofit_completed = [
        e
        for t, e in events
        if hasattr(e, 'event_type') and e.event_type == 'RETROFIT_COMPLETED' and hasattr(e, 'wagon_id')
    ]
    assert len(retrofit_completed) == 2

    # Verify both wagons were parked
    parked_events = [
        e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED' and hasattr(e, 'wagon_id')
    ]
    assert len(parked_events) == 2

    validate_retrofit_timeline_from_docstring(events, test_two_wagons_one_station, analytics_context)
    print('[PASS] Test passed: 2 wagons processed sequentially through 1 bay')


def test_two_wagons_two_stations() -> None:
    """Test 2 wagons, 2 stations - parallel processing.

    TIMELINE:
    t=0: train[T1] ARRIVED collection
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: batch[*] FORMED wagons=W01,W02
    t=1: locomotive[L1] ALLOCATED batch_transport
    t=1: batch[*] TRANSPORT_STARTED destination=retrofit
    t=1: locomotive[L1] MOVING collection->retrofit
    t=2: batch[*] ARRIVED_AT_DESTINATION retrofit
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
    t=17: batch[*] FORMED wagons=W01,W02
    t=18: locomotive[L1] ALLOCATED batch_transport
    t=18: locomotive[L1] MOVING loco_parking->retrofitted
    t=19: batch[*] TRANSPORT_STARTED destination=parking_area
    t=19: locomotive[L1] MOVING retrofitted->parking_area
    t=20: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=20: wagon[W01] PARKED parking_area
    t=20: wagon[W02] PARKED parking_area
    t=20: locomotive[L1] MOVING parking_area->loco_parking
    """
    # Use 1 workshop with 2 bays for parallel processing
    events, analytics_context = run_timeline_test(2, 1, 10.0, 50.0, workshop_bays=[2])

    # Verify we have arrival events for both wagons
    arrival_events = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'ARRIVED']
    assert len(arrival_events) >= 2

    # Validate timeline
    validate_retrofit_timeline_from_docstring(events, test_two_wagons_two_stations, analytics_context)
    print('[PASS] Test passed: 2 wagons processed in parallel through 2 bays')


def test_four_wagons_two_stations() -> None:
    """Test 4 wagons, 2 workshops - parallel processing.

    TIMELINE:
    t=0: train[T1] ARRIVED collection
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=0: wagon[W03] ARRIVED collection
    t=0: wagon[W04] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: batch[*] FORMED wagons=W01,W02,W03,W04
    t=1: locomotive[L1] ALLOCATED batch_transport
    t=1: batch[*] TRANSPORT_STARTED destination=retrofit
    t=1: locomotive[L1] MOVING collection->retrofit
    t=2: batch[*] ARRIVED_AT_DESTINATION retrofit
    t=2: locomotive[L1] MOVING retrofit->loco_parking
    t=3: locomotive[L1] MOVING loco_parking->retrofit
    t=4: locomotive[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFIT_STARTED WS1
    t=5: wagon[W02] RETROFIT_STARTED WS1
    t=5: locomotive[L1] MOVING WS1->loco_parking
    t=6: locomotive[L1] MOVING loco_parking->retrofit
    t=7: locomotive[L1] MOVING retrofit->WS2
    t=8: wagon[W03] RETROFIT_STARTED WS2
    t=8: wagon[W04] RETROFIT_STARTED WS2
    t=8: locomotive[L1] MOVING WS2->loco_parking
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=15: wagon[W02] RETROFIT_COMPLETED WS1
    t=15: locomotive[L1] MOVING loco_parking->WS1
    t=16: locomotive[L1] MOVING WS1->retrofitted
    t=17: locomotive[L1] MOVING retrofitted->loco_parking
    t=18: wagon[W03] RETROFIT_COMPLETED WS2
    t=18: wagon[W04] RETROFIT_COMPLETED WS2
    t=18: locomotive[L1] ALLOCATED batch_transport
    t=18: locomotive[L1] MOVING loco_parking->retrofitted
    t=19: batch[*] FORMED wagons=W01,W02
    t=19: batch[*] TRANSPORT_STARTED destination=parking_area
    t=19: locomotive[L1] MOVING retrofitted->parking_area
    t=20: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=20: wagon[W01] PARKED parking_area
    t=20: wagon[W02] PARKED parking_area
    t=20: locomotive[L1] MOVING parking_area->loco_parking
    t=21: locomotive[L1] MOVING loco_parking->WS2
    t=22: locomotive[L1] MOVING WS2->retrofitted
    t=23: locomotive[L1] MOVING retrofitted->loco_parking
    t=24: locomotive[L1] ALLOCATED batch_transport
    t=24: locomotive[L1] MOVING loco_parking->retrofitted
    t=25: batch[*] FORMED wagons=W03,W04
    t=25: batch[*] TRANSPORT_STARTED destination=parking_area
    t=25: locomotive[L1] MOVING retrofitted->parking_area
    t=26: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=26: wagon[W03] PARKED parking_area
    t=26: wagon[W04] PARKED parking_area
    t=26: locomotive[L1] MOVING parking_area->loco_parking
    """
    # Use 2 workshops with 2 bays each
    events, analytics_context = run_timeline_test(4, 2, 10.0, 50.0, workshop_bays=[2, 2])

    # Verify we have arrival events for all wagons
    arrival_events = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'ARRIVED']
    assert len(arrival_events) >= 4

    validate_retrofit_timeline_from_docstring(events, test_four_wagons_two_stations, analytics_context)
    print('Test passed: 4 wagons processed in parallel through 2 workshops')


def test_six_wagons_two_workshops() -> None:
    """Test 6 wagons, 2 workshops - processes in two batches.

    Batch 1: W01-W04 (60m) transported to retrofit at t=2
    Batch 2: W05-W06 (30m) wait at collection, transported at t=7 after WS1 frees capacity at t=5

    TIMELINE:
    t=0: train[T1] ARRIVED collection
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=0: wagon[W03] ARRIVED collection
    t=0: wagon[W04] ARRIVED collection
    t=0: wagon[W05] ARRIVED collection
    t=0: wagon[W06] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: locomotive[L1] MOVING collection->retrofit
    t=2: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W02] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W03] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W04] ON_RETROFIT_TRACK retrofit
    t=2: locomotive[L1] MOVING retrofit->loco_parking
    t=3: locomotive[L1] MOVING loco_parking->retrofit
    t=4: locomotive[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFIT_STARTED WS1
    t=5: wagon[W02] RETROFIT_STARTED WS1
    t=5: locomotive[L1] MOVING WS1->loco_parking
    t=6: locomotive[L1] MOVING loco_parking->collection
    t=7: locomotive[L1] MOVING collection->retrofit
    t=8: wagon[W05] ON_RETROFIT_TRACK retrofit
    t=8: wagon[W06] ON_RETROFIT_TRACK retrofit
    t=8: locomotive[L1] MOVING retrofit->loco_parking
    t=9: locomotive[L1] MOVING loco_parking->retrofit
    t=10: locomotive[L1] MOVING retrofit->WS2
    t=11: wagon[W03] RETROFIT_STARTED WS2
    t=11: wagon[W04] RETROFIT_STARTED WS2
    t=11: locomotive[L1] MOVING WS2->loco_parking
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=15: wagon[W02] RETROFIT_COMPLETED WS1
    t=15: locomotive[L1] MOVING loco_parking->WS1
    t=16: locomotive[L1] MOVING WS1->retrofitted
    t=17: locomotive[L1] MOVING retrofitted->loco_parking
    t=18: locomotive[L1] MOVING loco_parking->retrofitted
    t=19: wagon[W01] PARKED parking_area
    t=19: wagon[W02] PARKED parking_area
    t=21: wagon[W03] RETROFIT_COMPLETED WS2
    t=21: wagon[W04] RETROFIT_COMPLETED WS2
    t=21: locomotive[L1] MOVING loco_parking->WS2
    t=22: locomotive[L1] MOVING WS2->retrofitted
    t=23: locomotive[L1] MOVING retrofitted->loco_parking
    t=24: locomotive[L1] MOVING loco_parking->retrofitted
    t=25: wagon[W03] PARKED parking_area
    t=25: wagon[W04] PARKED parking_area
    t=27: locomotive[L1] MOVING loco_parking->retrofit
    t=28: locomotive[L1] MOVING retrofit->WS1
    t=29: wagon[W05] RETROFIT_STARTED WS1
    t=29: wagon[W06] RETROFIT_STARTED WS1
    t=29: locomotive[L1] MOVING WS1->loco_parking
    t=39: wagon[W05] RETROFIT_COMPLETED WS1
    t=39: wagon[W06] RETROFIT_COMPLETED WS1
    t=39: locomotive[L1] MOVING loco_parking->WS1
    t=40: locomotive[L1] MOVING WS1->retrofitted
    t=41: locomotive[L1] MOVING retrofitted->loco_parking
    t=42: locomotive[L1] MOVING loco_parking->retrofitted
    t=43: wagon[W05] PARKED parking_area
    t=43: wagon[W06] PARKED parking_area
    """
    events, analytics_context = run_timeline_test(6, 2, 10.0, 100.0, workshop_bays=[2, 2])

    # Verify all 6 wagons arrived
    arrival_events = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'ARRIVED']
    assert len(arrival_events) >= 6

    # Verify all 6 wagons were retrofitted
    retrofit_started = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'RETROFIT_STARTED']
    assert len(retrofit_started) == 6, f'Expected 6 wagons to start retrofit, got {len(retrofit_started)}'

    # Verify all 6 wagons were parked
    parked_events = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked_events) == 6, f'Expected 6 wagons to be parked, got {len(parked_events)}'

    print('[PASS] Test passed: All 6 wagons processed in two batches')


def test_seven_wagons_two_workshops() -> None:
    """Test 7 wagons, 2 workshops - all collected at once, distributed 2-2-2-1.

    All 7 wagons (105m) fit on retrofit track (120m capacity).
    With opportunistic parking: W01+W02 parked first, then W05+W06 picked up.
    WS1: W01+W02 (t=5-15), then W05+W06 (t=26-36)
    WS2: W03+W04 (t=8-18), then W07 (t=32-42)

    TIMELINE:
    t=0: train[T1] ARRIVED collection
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=0: wagon[W03] ARRIVED collection
    t=0: wagon[W04] ARRIVED collection
    t=0: wagon[W05] ARRIVED collection
    t=0: wagon[W06] ARRIVED collection
    t=0: wagon[W07] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: locomotive[L1] MOVING collection->retrofit
    t=2: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W02] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W03] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W04] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W05] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W06] ON_RETROFIT_TRACK retrofit
    t=2: wagon[W07] ON_RETROFIT_TRACK retrofit
    t=2: locomotive[L1] MOVING retrofit->loco_parking
    t=3: locomotive[L1] MOVING loco_parking->retrofit
    t=4: locomotive[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFIT_STARTED WS1
    t=5: wagon[W02] RETROFIT_STARTED WS1
    t=5: locomotive[L1] MOVING WS1->loco_parking
    t=6: locomotive[L1] MOVING loco_parking->retrofit
    t=7: locomotive[L1] MOVING retrofit->WS2
    t=8: wagon[W03] RETROFIT_STARTED WS2
    t=8: wagon[W04] RETROFIT_STARTED WS2
    t=8: locomotive[L1] MOVING WS2->loco_parking
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=15: wagon[W02] RETROFIT_COMPLETED WS1
    t=15: locomotive[L1] MOVING loco_parking->WS1
    t=16: locomotive[L1] MOVING WS1->retrofitted
    t=17: locomotive[L1] MOVING retrofitted->loco_parking
    t=18: wagon[W03] RETROFIT_COMPLETED WS2
    t=18: wagon[W04] RETROFIT_COMPLETED WS2
    t=18: locomotive[L1] ALLOCATED batch_transport
    t=18: locomotive[L1] MOVING loco_parking->retrofitted
    t=19: batch[*] FORMED wagons=W01,W02
    t=19: batch[*] TRANSPORT_STARTED destination=parking_area
    t=19: locomotive[L1] MOVING retrofitted->parking_area
    t=20: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=20: wagon[W01] PARKED parking_area
    t=20: wagon[W02] PARKED parking_area
    t=20: locomotive[L1] MOVING parking_area->loco_parking
    t=21: locomotive[L1] MOVING loco_parking->WS2
    t=22: locomotive[L1] MOVING WS2->retrofitted
    t=23: locomotive[L1] MOVING retrofitted->loco_parking
    t=24: locomotive[L1] MOVING loco_parking->retrofit
    t=25: locomotive[L1] MOVING retrofit->WS1
    t=26: wagon[W05] RETROFIT_STARTED WS1
    t=26: wagon[W06] RETROFIT_STARTED WS1
    t=26: locomotive[L1] MOVING WS1->loco_parking
    t=27: locomotive[L1] ALLOCATED batch_transport
    t=27: locomotive[L1] MOVING loco_parking->retrofitted
    t=28: batch[*] FORMED wagons=W03,W04
    t=28: batch[*] TRANSPORT_STARTED destination=parking_area
    t=28: locomotive[L1] MOVING retrofitted->parking_area
    t=29: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=29: wagon[W03] PARKED parking_area
    t=29: wagon[W04] PARKED parking_area
    t=29: locomotive[L1] MOVING parking_area->loco_parking
    t=30: locomotive[L1] MOVING loco_parking->retrofit
    t=31: locomotive[L1] MOVING retrofit->WS2
    t=32: wagon[W07] RETROFIT_STARTED WS2
    t=32: locomotive[L1] MOVING WS2->loco_parking
    t=36: wagon[W05] RETROFIT_COMPLETED WS1
    t=36: wagon[W06] RETROFIT_COMPLETED WS1
    t=36: locomotive[L1] MOVING loco_parking->WS1
    t=37: locomotive[L1] MOVING WS1->retrofitted
    t=38: locomotive[L1] MOVING retrofitted->loco_parking
    t=39: locomotive[L1] ALLOCATED batch_transport
    t=39: locomotive[L1] MOVING loco_parking->retrofitted
    t=40: batch[*] FORMED wagons=W05,W06
    t=40: batch[*] TRANSPORT_STARTED destination=parking_area
    t=40: locomotive[L1] MOVING retrofitted->parking_area
    t=41: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=41: wagon[W05] PARKED parking_area
    t=41: wagon[W06] PARKED parking_area
    t=41: locomotive[L1] MOVING parking_area->loco_parking
    t=42: wagon[W07] RETROFIT_COMPLETED WS2
    t=42: locomotive[L1] MOVING loco_parking->WS2
    t=43: locomotive[L1] MOVING WS2->retrofitted
    t=44: locomotive[L1] MOVING retrofitted->loco_parking
    t=45: locomotive[L1] ALLOCATED batch_transport
    t=45: locomotive[L1] MOVING loco_parking->retrofitted
    t=46: batch[*] FORMED wagons=W07
    t=46: batch[*] TRANSPORT_STARTED destination=parking_area
    t=46: locomotive[L1] MOVING retrofitted->parking_area
    t=47: batch[*] ARRIVED_AT_DESTINATION parking_area
    t=47: wagon[W07] PARKED parking_area
    t=47: locomotive[L1] MOVING parking_area->loco_parking
    """
    # Retrofit track: 130m * 0.9 = 117m capacity, 7 wagons * 15m = 105m (fits all)
    events, analytics_context = run_timeline_test(7, 2, 10.0, 100.0, workshop_bays=[2, 2], retrofit_track_length=130.0)

    # Verify all 7 wagons arrived
    arrival_events = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'ARRIVED']
    assert len(arrival_events) >= 7, f'Expected 7 arrival events, got {len(arrival_events)}'

    # Verify all 7 wagons were retrofitted
    retrofit_started = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'RETROFIT_STARTED']
    assert len(retrofit_started) == 7, f'Expected 7 wagons to start retrofit, got {len(retrofit_started)}'

    # Verify all 7 wagons were parked
    parked_events = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked_events) == 7, f'Expected 7 wagons to be parked, got {len(parked_events)}'

    validate_retrofit_timeline_from_docstring(events, test_seven_wagons_two_workshops, analytics_context)
    print('Test passed: All 7 wagons collected at once, distributed 2-2-2-1 across workshops')
