"""Layered timeline tests - progressively adding time components.

Test Structure:
- Layer 1: Pure travel times (no coupling, no prep)
- Layer 2: Preparation times only (no coupling)
- Layer 3: Complete times (coupling + preparation)
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
    # Layer controls
    coupling_time: float = 0.0,  # Layer 3: All coupling/decoupling (rake + loco)
    loco_prep_time: float = 0.0,  # Layer 2+3: Locomotive preparation
    brake_test_time: float = 0.0,  # Future: brake tests
    inspection_time: float = 0.0,  # Future: inspections
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
        Mock(id='retrofit', type='retrofit', length=80.0, fillfactor=0.9),
        Mock(id='retrofitted', type='retrofitted', length=120.0, fillfactor=0.8),
        Mock(id='parking_area', type='parking', length=200.0, fillfactor=0.7),
        Mock(id='loco_parking', type='loco_parking', length=50.0, fillfactor=0.5),
    ]
    for i in range(num_workshops):
        mock_scenario.tracks.append(Mock(id=f'WS{i + 1}', type='workshop', length=100.0, fillfactor=0.75))

    # Routes (all 1 minute travel time) - properly mock path attribute
    mock_scenario.routes = [
        Mock(
            from_location='loco_parking',
            to_location='collection',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['loco_parking', 'collection'],
        ),
        Mock(
            from_location='collection',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['collection', 'loco_parking'],
        ),
        Mock(
            from_location='loco_parking',
            to_location='retrofit',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['loco_parking', 'retrofit'],
        ),
        Mock(
            from_location='retrofit',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['retrofit', 'loco_parking'],
        ),
        Mock(
            from_location='loco_parking',
            to_location='WS1',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['loco_parking', 'WS1'],
        ),
        Mock(
            from_location='WS1',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['WS1', 'loco_parking'],
        ),
        Mock(
            from_location='loco_parking',
            to_location='retrofitted',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['loco_parking', 'retrofitted'],
        ),
        Mock(
            from_location='retrofitted',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['retrofitted', 'loco_parking'],
        ),
        Mock(
            from_location='loco_parking',
            to_location='parking_area',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['loco_parking', 'parking_area'],
        ),
        Mock(
            from_location='parking_area',
            to_location='loco_parking',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['parking_area', 'loco_parking'],
        ),
        Mock(
            from_location='collection',
            to_location='retrofit',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['collection', 'retrofit'],
        ),
        Mock(
            from_location='retrofit',
            to_location='WS1',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['retrofit', 'WS1'],
        ),
        Mock(
            from_location='WS1',
            to_location='retrofitted',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['WS1', 'retrofitted'],
        ),
        Mock(
            from_location='retrofitted',
            to_location='parking_area',
            duration=timedelta(minutes=1),
            route_type='SHUNTING',
            path=['retrofitted', 'parking_area'],
        ),
    ]

    # Process times - layered configuration
    from unittest.mock import MagicMock

    process_times_mock = MagicMock()
    process_times_mock.wagon_retrofit_time = timedelta(minutes=retrofit_time)
    # Layer 3: All coupling/decoupling times (same for rake and loco)
    process_times_mock.screw_coupling_time = timedelta(minutes=coupling_time)
    process_times_mock.screw_decoupling_time = timedelta(minutes=coupling_time)
    process_times_mock.dac_coupling_time = timedelta(minutes=coupling_time * 0.5)
    process_times_mock.dac_decoupling_time = timedelta(minutes=coupling_time * 0.5)
    # Layer 2+3: Locomotive preparation
    process_times_mock.shunting_preparation_time = timedelta(minutes=loco_prep_time)
    process_times_mock.full_brake_test_time = timedelta(minutes=brake_test_time)
    process_times_mock.technical_inspection_time = timedelta(minutes=inspection_time)
    process_times_mock.brake_continuity_check_time = timedelta(seconds=0.0)

    # Add get_coupling_time method for dynamic coupling based on coupler types
    def get_coupling_time(coupler_type: str) -> timedelta:
        if coupler_type.upper() == 'DAC':
            return timedelta(minutes=coupling_time * 0.5)
        return timedelta(minutes=coupling_time)

    def get_decoupling_time(coupler_type: str) -> timedelta:
        if coupler_type.upper() == 'DAC':
            return timedelta(minutes=coupling_time * 0.5)
        return timedelta(minutes=coupling_time)

    def get_coupling_ticks(coupler_type: str) -> float:
        if coupler_type.upper() == 'DAC':
            return coupling_time * 0.5
        return coupling_time

    def get_decoupling_ticks(coupler_type: str) -> float:
        if coupler_type.upper() == 'DAC':
            return coupling_time * 0.5
        return coupling_time

    process_times_mock.get_coupling_time = get_coupling_time
    process_times_mock.get_decoupling_time = get_decoupling_time
    process_times_mock.get_coupling_ticks = get_coupling_ticks
    process_times_mock.get_decoupling_ticks = get_decoupling_ticks
    mock_scenario.process_times = process_times_mock

    mock_scenario.loco_priority_strategy = Mock(value='batch_completion')

    # Parking strategy configuration
    mock_scenario.parking_strategy = 'opportunistic'
    mock_scenario.parking_normal_threshold = 0.5
    mock_scenario.parking_critical_threshold = 0.8
    mock_scenario.parking_idle_check_interval = 1.0

    # Track selection strategies
    mock_scenario.collection_track_strategy = Mock(value='round_robin')
    mock_scenario.retrofit_selection_strategy = Mock(value='first_available')
    mock_scenario.parking_selection_strategy = Mock(value='best_fit')
    mock_scenario.id = 'layered_test_scenario'

    return mock_scenario


# pylint: disable=too-many-branches
def run_layered_test(  # noqa: PLR0912
    num_wagons: int,
    num_workshops: int,
    retrofit_time: float,
    until: float,
    workshop_bays: list[int] | None = None,
    coupling_time: float = 0.0,
    loco_prep_time: float = 0.0,
    brake_test_time: float = 0.0,
    inspection_time: float = 0.0,
) -> tuple[list, Mock]:
    """Run test with layered time configuration."""
    env = simpy.Environment()
    scenario = create_layered_scenario(
        num_workshops,
        retrofit_time,
        workshop_bays,
        coupling_time,
        loco_prep_time,
        brake_test_time,
        inspection_time,
    )

    context = RetrofitWorkshopContext(env, scenario)
    events = []
    parked_wagons = set()

    context.initialize()

    # Hook event collector
    if context.event_collector:
        original_wagon_event = context.event_collector.add_wagon_event
        original_loco_event = context.event_collector.add_locomotive_event
        original_batch_event = context.event_collector.add_batch_event

        def capture_wagon_event(event) -> None:
            events.append((env.now, event))
            if hasattr(event, 'event_type') and event.event_type == 'PARKED':
                parked_wagons.add(event.wagon_id)
            original_wagon_event(event)

        def capture_loco_event(event) -> None:
            events.append((env.now, event))
            original_loco_event(event)

        def capture_batch_event(event) -> None:
            events.append((env.now, event))
            original_batch_event(event)

        context.event_collector.add_wagon_event = capture_wagon_event
        context.event_collector.add_locomotive_event = capture_loco_event
        context.event_collector.add_batch_event = capture_batch_event

        # Re-wire coordinators
        if context.collection_coordinator and hasattr(context.collection_coordinator, 'config'):
            context.collection_coordinator.config.wagon_event_publisher = capture_wagon_event
            context.collection_coordinator.config.loco_event_publisher = capture_loco_event
            context.collection_coordinator.config.batch_event_publisher = capture_batch_event
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
                context.parking_coordinator.config.batch_event_publisher = capture_batch_event
            else:
                context.parking_coordinator.wagon_event_publisher = capture_wagon_event
                context.parking_coordinator.loco_event_publisher = capture_loco_event
                context.parking_coordinator.batch_event_publisher = capture_batch_event

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
        wagon.current_track_id = 'collection'

        arrival_event = WagonJourneyEvent(
            timestamp=0.0, wagon_id=wagon.id, event_type='ARRIVED', location='collection', status='ARRIVED'
        )
        events.append((0.0, arrival_event))
        context.collection_coordinator.add_wagon(wagon)

    # Termination process
    def termination_process():
        while True:
            yield env.timeout(1)
            if len(parked_wagons) >= num_wagons:
                break

    env.process(termination_process())
    env.run(until=until)

    # Print timeline for debugging
    print(f'\nTotal events: {len(events)}')
    print('\n' + '=' * 80)
    print('ACTUAL TIMELINE:')
    print('=' * 80)
    for t, e in sorted(events, key=lambda x: x[0]):
        event_type = type(e).__name__
        if event_type == 'WagonJourneyEvent':
            print(f't={int(t)}: wagon[{e.wagon_id}] {e.event_type} {e.location}')
        elif event_type == 'LocomotiveMovementEvent':
            if hasattr(e, 'purpose') and e.purpose:
                print(f't={int(t)}: locomotive[{e.locomotive_id}] {e.event_type} {e.purpose}')
            elif hasattr(e, 'from_location') and hasattr(e, 'to_location') and e.from_location:
                print(f't={int(t)}: locomotive[{e.locomotive_id}] MOVING {e.from_location}->{e.to_location}')
        elif event_type == 'CouplingEvent':
            if e.locomotive_id:
                print(
                    f't={int(t)}: {e.event_type} at {e.location} (loco={e.locomotive_id}, wagons={e.wagon_count}, duration={e.duration})'
                )
            else:
                print(
                    f't={int(t)}: {e.event_type} at {e.location} (wagons={e.wagon_count}, couplings={e.coupling_count}, duration={e.duration})'
                )
        elif event_type == 'BatchFormed':
            wagon_list = ','.join(e.wagon_ids)
            print(f't={int(t)}: batch[{e.batch_id}] FORMED wagons={wagon_list}')
        elif event_type == 'BatchTransportStarted':
            print(f't={int(t)}: batch[{e.batch_id}] TRANSPORT_STARTED destination={e.destination}')
        elif event_type == 'BatchArrivedAtDestination':
            print(f't={int(t)}: batch[{e.batch_id}] ARRIVED_AT_DESTINATION {e.destination}')
    print('=' * 80 + '\n')

    mock_analytics = Mock()
    mock_analytics.get_metrics.return_value = {'event_history': events}

    return events, mock_analytics


# ============================================================================
# LAYER 1: PURE TRAVEL TIMES (no coupling, no prep)
# ============================================================================


def test_layer1_single_wagon_pure_travel() -> None:
    """Layer 1: Single wagon with pure travel times only.

    No coupling times, no loco preparation.
    All routes: 1 minute travel time.
    Retrofit: 10 minutes.

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
    events, analytics = run_layered_test(
        num_wagons=1,
        num_workshops=1,
        retrofit_time=10.0,
        until=30.0,
        workshop_bays=[1],
        # Layer 1: All times = 0
        coupling_time=0.0,
        loco_prep_time=0.0,
    )

    # Verify wagon completed journey
    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 1

    validate_retrofit_timeline_from_docstring(events, test_layer1_single_wagon_pure_travel, analytics)


def test_layer1_two_wagons_pure_travel() -> None:
    """Layer 1: Two wagons with pure travel times, sequential processing.

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
    t=5: locomotive[L1] MOVING WS1->loco_parking
    t=15: wagon[W01] RETROFIT_COMPLETED WS1
    t=15: locomotive[L1] MOVING loco_parking->WS1
    t=16: locomotive[L1] MOVING WS1->retrofitted
    t=17: locomotive[L1] MOVING retrofitted->loco_parking
    t=18: locomotive[L1] MOVING loco_parking->retrofitted
    t=19: locomotive[L1] MOVING retrofitted->parking_area
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
    t=36: locomotive[L1] MOVING loco_parking->retrofitted
    t=37: locomotive[L1] MOVING retrofitted->parking_area
    t=38: wagon[W02] PARKED parking_area
    """
    events, analytics = run_layered_test(
        num_wagons=2,
        num_workshops=1,
        retrofit_time=10.0,
        until=50.0,
        workshop_bays=[1],
        coupling_time=0.0,
        loco_prep_time=0.0,
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 2

    validate_retrofit_timeline_from_docstring(events, test_layer1_two_wagons_pure_travel, analytics)


# ============================================================================
# LAYER 2: PREPARATION TIMES ONLY (no coupling)
# ============================================================================


def test_layer2_single_wagon_with_prep() -> None:
    """Layer 2: Single wagon with preparation times only (no coupling).

    Shunting prep: 1 min (added at each train formation)
    No coupling/decoupling

    Prep times added at:
    - t=1: After loco arrives at collection
    - t=5: After loco arrives at retrofit
    - t=18: After loco arrives at workshop
    - t=22: After loco arrives at retrofitted

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=2: locomotive[L1] MOVING collection->retrofit
    t=3: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=3: locomotive[L1] MOVING retrofit->loco_parking
    t=4: locomotive[L1] MOVING loco_parking->retrofit
    t=6: locomotive[L1] MOVING retrofit->WS1
    t=7: wagon[W01] RETROFIT_STARTED WS1
    t=7: locomotive[L1] MOVING WS1->loco_parking
    t=17: wagon[W01] RETROFIT_COMPLETED WS1
    t=17: locomotive[L1] MOVING loco_parking->WS1
    t=19: locomotive[L1] MOVING WS1->retrofitted
    t=20: locomotive[L1] MOVING retrofitted->loco_parking
    t=21: locomotive[L1] MOVING loco_parking->retrofitted
    t=23: locomotive[L1] MOVING retrofitted->parking_area
    t=24: wagon[W01] PARKED parking_area
    """
    events, analytics = run_layered_test(
        num_wagons=1,
        num_workshops=1,
        retrofit_time=10.0,
        until=50.0,
        workshop_bays=[1],
        # Layer 2: Add prep only
        coupling_time=0.0,
        loco_prep_time=1.0,
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 1

    validate_retrofit_timeline_from_docstring(events, test_layer2_single_wagon_with_prep, analytics)


# ============================================================================
# LAYER 3: COMPLETE TIMES (coupling + preparation)
# ============================================================================


def test_layer3_single_wagon_complete() -> None:
    """Layer 3: Single wagon with all time components.

    Coupling: 1 min (SCREW before retrofit), 0.5 min (DAC after retrofit)
    Shunting prep: 1 min

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=3: locomotive[L1] MOVING collection->retrofit
    t=4: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=5: locomotive[L1] MOVING retrofit->loco_parking
    t=6: locomotive[L1] MOVING loco_parking->retrofit
    t=9: locomotive[L1] MOVING retrofit->WS1
    t=11: wagon[W01] RETROFIT_STARTED WS1
    t=11: locomotive[L1] MOVING WS1->loco_parking
    t=21: wagon[W01] RETROFIT_COMPLETED WS1
    t=21: locomotive[L1] MOVING loco_parking->WS1
    t=23.5: locomotive[L1] MOVING WS1->retrofitted
    t=24.5: locomotive[L1] MOVING retrofitted->loco_parking
    t=25.5: locomotive[L1] MOVING loco_parking->retrofitted
    t=28: locomotive[L1] MOVING retrofitted->parking_area
    t=29.5: wagon[W01] PARKED parking_area
    """
    events, analytics = run_layered_test(
        num_wagons=1,
        num_workshops=1,
        retrofit_time=10.0,
        until=50.0,
        workshop_bays=[1],
        # Layer 3: All times
        coupling_time=1.0,
        loco_prep_time=1.0,
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 1

    validate_retrofit_timeline_from_docstring(events, test_layer3_single_wagon_complete, analytics)
