"""Layered timeline tests - progressively adding time components.

Test Structure:
- Layer 1: Pure travel times (no coupling, no loco prep)
- Layer 2: Rake coupling/decoupling times (wagon-to-wagon)
- Layer 3: Locomotive operations (loco coupling + prep, no rake coupling)
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
    # Layer controls
    rake_coupling_time: float = 0.0,  # Layer 2: wagon-to-wagon coupling
    loco_coupling_time: float = 0.0,  # Layer 3: locomotive coupling
    loco_prep_time: float = 0.0,  # Layer 3: locomotive preparation (shunting)
    brake_test_time: float = 0.0,  # Layer 3: brake test (mainline)
    inspection_time: float = 0.0,  # Layer 3: inspection (mainline)
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
        Mock(id='parking_area', type='parking_area', length=200.0, fillfactor=0.7),
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
    process_times_mock.full_brake_test_time = timedelta(minutes=brake_test_time)
    process_times_mock.technical_inspection_time = timedelta(minutes=inspection_time)
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

    process_times_mock.get_coupling_time = get_coupling_time
    process_times_mock.get_decoupling_time = get_decoupling_time
    mock_scenario.process_times = process_times_mock

    mock_scenario.loco_priority_strategy = Mock(value='batch_completion')

    return mock_scenario


def run_layered_test(
    num_wagons: int,
    num_workshops: int,
    retrofit_time: float,
    until: float,
    workshop_bays: list[int] | None = None,
    rake_coupling_time: float = 0.0,
    loco_coupling_time: float = 0.0,
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
        rake_coupling_time,
        loco_coupling_time,
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

        def capture_wagon_event(event) -> None:
            events.append((env.now, event))
            if hasattr(event, 'event_type') and event.event_type == 'PARKED':
                parked_wagons.add(event.wagon_id)
            original_wagon_event(event)

        context.event_collector.add_wagon_event = capture_wagon_event

        # Re-wire coordinators
        if context.collection_coordinator and hasattr(context.collection_coordinator, 'config'):
            context.collection_coordinator.config.wagon_event_publisher = capture_wagon_event
        if context.workshop_coordinator:
            if hasattr(context.workshop_coordinator, 'config'):
                context.workshop_coordinator.config.wagon_event_publisher = capture_wagon_event
            else:
                context.workshop_coordinator.wagon_event_publisher = capture_wagon_event
        if context.parking_coordinator:
            if hasattr(context.parking_coordinator, 'config'):
                context.parking_coordinator.config.wagon_event_publisher = capture_wagon_event
            else:
                context.parking_coordinator.wagon_event_publisher = capture_wagon_event

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

        arrival_event = WagonJourneyEvent(
            timestamp=0.0, wagon_id=wagon.id, event_type='ARRIVED', location='collection', status='ARRIVED'
        )
        events.append((0.0, arrival_event))
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
# LAYER 1: PURE TRAVEL TIMES (no coupling, no loco prep)
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
        rake_coupling_time=0.0,
        loco_coupling_time=0.0,
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
    t=18: locomotive[L1] MOVING loco_parking->retrofit
    t=19: locomotive[L1] MOVING retrofit->WS1
    t=22: wagon[W02] RETROFIT_STARTED WS1
    t=20: locomotive[L1] MOVING WS1->loco_parking
    t=21: locomotive[L1] MOVING loco_parking->retrofitted
    t=22: locomotive[L1] MOVING retrofitted->parking_area
    t=23: wagon[W01] PARKED parking_area
    t=32: wagon[W02] RETROFIT_COMPLETED WS1
    t=30: locomotive[L1] MOVING loco_parking->WS1
    t=31: locomotive[L1] MOVING WS1->retrofitted
    t=32: locomotive[L1] MOVING retrofitted->loco_parking
    t=33: locomotive[L1] MOVING loco_parking->retrofitted
    t=34: locomotive[L1] MOVING retrofitted->parking_area
    t=37: wagon[W02] PARKED parking_area
    """
    events, analytics = run_layered_test(
        num_wagons=2,
        num_workshops=1,
        retrofit_time=10.0,
        until=50.0,
        workshop_bays=[1],
        rake_coupling_time=0.0,
        loco_coupling_time=0.0,
        loco_prep_time=0.0,
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 2

    validate_retrofit_timeline_from_docstring(events, test_layer1_two_wagons_pure_travel, analytics)


# ============================================================================
# LAYER 2: RAKE COUPLING/DECOUPLING (wagon-to-wagon)
# ============================================================================


def test_layer2_two_wagons_with_rake_coupling() -> None:
    """Layer 2: Two wagons with rake coupling/decoupling (1 min per coupling).

    Rake has 1 coupling between 2 wagons.
    Decoupling at workshop: 1 min.
    Coupling at workshop: 1 min.

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
    t=5: DECOUPLING (1 min for 1 coupling)
    t=6: DECOUPLING complete
    t=7: wagon[W01] RETROFIT_STARTED WS1
    t=7: locomotive[L1] MOVING WS1->loco_parking
    t=17: wagon[W01] RETROFIT_COMPLETED WS1
    t=17: COUPLING (1 min for 1 coupling)
    t=18: locomotive[L1] MOVING loco_parking->WS1
    t=19: locomotive[L1] MOVING WS1->retrofitted
    t=20: locomotive[L1] MOVING retrofitted->loco_parking
    t=21: locomotive[L1] MOVING loco_parking->retrofit
    t=22: locomotive[L1] MOVING retrofit->WS1
    t=23: DECOUPLING (1 min)
    t=24: DECOUPLING complete
    t=27.5: wagon[W02] RETROFIT_STARTED WS1
    t=27.5: locomotive[L1] MOVING WS1->loco_parking
    t=25: locomotive[L1] MOVING loco_parking->retrofitted
    t=26: locomotive[L1] MOVING retrofitted->parking_area
    t=27: wagon[W01] PARKED parking_area
    t=37.5: wagon[W02] RETROFIT_COMPLETED WS1
    t=37.5: COUPLING (1 min)
    t=38.5: locomotive[L1] MOVING loco_parking->WS1
    t=39.5: locomotive[L1] MOVING WS1->retrofitted
    t=40.5: locomotive[L1] MOVING retrofitted->loco_parking
    t=41.5: locomotive[L1] MOVING loco_parking->retrofitted
    t=42.5: locomotive[L1] MOVING retrofitted->parking_area
    t=43.5: wagon[W02] PARKED parking_area
    """
    events, analytics = run_layered_test(
        num_wagons=2,
        num_workshops=1,
        retrofit_time=10.0,
        until=50.0,
        workshop_bays=[1],
        # Layer 2: Add rake coupling
        rake_coupling_time=1.0,
        loco_coupling_time=0.0,
        loco_prep_time=0.0,
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 2

    validate_retrofit_timeline_from_docstring(events, test_layer2_two_wagons_with_rake_coupling, analytics)


# ============================================================================
# LAYER 3: LOCOMOTIVE OPERATIONS (loco coupling + prep, NO rake coupling)
# ============================================================================


def test_layer3_single_wagon_with_loco_ops() -> None:
    """Layer 3: Single wagon with locomotive operations (no rake coupling).

    Loco coupling: 3 min
    Shunting prep: 1 min
    Total loco prep: 4 min

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: LOCO_COUPLING (3 min)
    t=4: SHUNTING_PREP (1 min)
    t=5: locomotive[L1] MOVING collection->retrofit
    t=6: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=6: locomotive[L1] MOVING retrofit->loco_parking
    t=7: locomotive[L1] MOVING loco_parking->retrofit
    t=8: LOCO_COUPLING (3 min)
    t=11: SHUNTING_PREP (1 min)
    t=12: locomotive[L1] MOVING retrofit->WS1
    t=13: wagon[W01] RETROFIT_STARTED WS1
    t=13: locomotive[L1] MOVING WS1->loco_parking
    t=23: wagon[W01] RETROFIT_COMPLETED WS1
    t=23: locomotive[L1] MOVING loco_parking->WS1
    t=24: LOCO_COUPLING (3 min)
    t=27: SHUNTING_PREP (1 min)
    t=28: locomotive[L1] MOVING WS1->retrofitted
    t=29: locomotive[L1] MOVING retrofitted->loco_parking
    t=30: locomotive[L1] MOVING loco_parking->retrofitted
    t=31: LOCO_COUPLING (3 min)
    t=34: SHUNTING_PREP (1 min)
    t=35: locomotive[L1] MOVING retrofitted->parking_area
    t=36: wagon[W01] PARKED parking_area
    """
    events, analytics = run_layered_test(
        num_wagons=1,
        num_workshops=1,
        retrofit_time=10.0,
        until=50.0,
        workshop_bays=[1],
        # Layer 3: Add loco operations, NO rake coupling
        rake_coupling_time=0.0,
        loco_coupling_time=3.0,
        loco_prep_time=1.0,
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 1

    validate_retrofit_timeline_from_docstring(events, test_layer3_single_wagon_with_loco_ops, analytics)


# ============================================================================
# LAYER 4: COMPLETE TIMES (all operations)
# ============================================================================


def test_layer4_two_wagons_complete_times() -> None:
    """Layer 4: Two wagons with all time components.

    Rake coupling: 1 min (wagon-to-wagon)
    Loco coupling: 1 min SCREW (before retrofit), 0.5 min DAC (after retrofit)
    Shunting prep: 1 min
    Total loco prep: 2 min SCREW (1+1), 1.5 min DAC (0.5+1)

    TIMELINE:
    t=0: wagon[W01] ARRIVED collection
    t=0: wagon[W02] ARRIVED collection
    t=0: locomotive[L1] MOVING loco_parking->collection
    t=1: LOCO_COUPLING (1 min SCREW)
    t=2: SHUNTING_PREP (1 min)
    t=3: locomotive[L1] MOVING collection->retrofit
    t=4: wagon[W01] ON_RETROFIT_TRACK retrofit
    t=4: wagon[W02] ON_RETROFIT_TRACK retrofit
    t=4: locomotive[L1] MOVING retrofit->loco_parking
    t=5: locomotive[L1] MOVING loco_parking->retrofit
    t=6: LOCO_COUPLING (1 min SCREW)
    t=7: SHUNTING_PREP (1 min)
    t=8: locomotive[L1] MOVING retrofit->WS1
    t=9: DECOUPLING (1 min for 1 coupling)
    t=9: wagon[W01] RETROFIT_STARTED WS1
    t=9: locomotive[L1] MOVING WS1->loco_parking
    t=19: wagon[W01] RETROFIT_COMPLETED WS1
    t=20: COUPLING (1 min)
    t=21: locomotive[L1] MOVING loco_parking->WS1
    t=22: LOCO_COUPLING (0.5 min DAC)
    t=22.5: SHUNTING_PREP (1 min)
    t=23.5: locomotive[L1] MOVING WS1->retrofitted
    t=24.5: locomotive[L1] MOVING retrofitted->loco_parking
    t=25.5: locomotive[L1] MOVING loco_parking->retrofit
    t=26.5: LOCO_COUPLING (1 min SCREW)
    t=27.5: SHUNTING_PREP (1 min)
    t=28.5: locomotive[L1] MOVING retrofit->WS1
    t=29.5: DECOUPLING (1 min)
    t=30.5: DECOUPLING complete
    t=32.5: wagon[W02] RETROFIT_STARTED WS1
    t=32.5: locomotive[L1] MOVING WS1->loco_parking
    t=31.5: locomotive[L1] MOVING loco_parking->retrofitted
    t=32.5: LOCO_COUPLING (0.5 min DAC)
    t=33: SHUNTING_PREP (1 min)
    t=34: locomotive[L1] MOVING retrofitted->parking_area
    t=35: wagon[W01] PARKED parking_area
    t=42.5: wagon[W02] RETROFIT_COMPLETED WS1
    t=42.5: COUPLING (1 min)
    t=43.5: locomotive[L1] MOVING loco_parking->WS1
    t=44.5: LOCO_COUPLING (0.5 min DAC)
    t=45: SHUNTING_PREP (1 min)
    t=46: locomotive[L1] MOVING WS1->retrofitted
    t=47: locomotive[L1] MOVING retrofitted->loco_parking
    t=48: locomotive[L1] MOVING loco_parking->retrofitted
    t=49: LOCO_COUPLING (0.5 min DAC)
    t=49.5: SHUNTING_PREP (1 min)
    t=50.5: locomotive[L1] MOVING retrofitted->parking_area
    t=51.5: wagon[W02] PARKED parking_area
    """
    events, analytics = run_layered_test(
        num_wagons=2,
        num_workshops=1,
        retrofit_time=10.0,
        until=80.0,
        workshop_bays=[1],
        # Layer 4: All times with dynamic loco coupling
        rake_coupling_time=1.0,
        loco_coupling_time=1.0,  # Dynamic: 1 min SCREW, 0.5 min DAC
        loco_prep_time=1.0,
    )

    parked = [e for t, e in events if hasattr(e, 'event_type') and e.event_type == 'PARKED']
    assert len(parked) == 2

    validate_retrofit_timeline_from_docstring(events, test_layer4_two_wagons_complete_times, analytics)
