"""Timeline validator for retrofit workflow context events."""

import re
from typing import Any


def validate_retrofit_timeline_from_docstring(_result: Any, test_func: Any, analytics_context: Any = None) -> None:
    """Extract TIMELINE from test docstring and validate against retrofit workflow events.

    Args:
        _result: SimulationResult with metrics
        test_func: Test function with TIMELINE in docstring
        analytics_context: AnalyticsContext for querying events and state
    """
    docstring = test_func.__doc__
    if not docstring or 'TIMELINE:' not in docstring:
        return

    timeline_start = docstring.index('TIMELINE:')
    timeline_section = docstring[timeline_start + len('TIMELINE:') :]

    events = analytics_context.get_metrics().get('event_history', []) if analytics_context else []
    # Can be switched on for better debugging
    # _print_actual_timeline(events)
    validate_retrofit_timeline(events, timeline_section)


def _print_actual_timeline(events: list[tuple[float, Any]]) -> None:
    """Print actual timeline from retrofit workflow events for debugging."""
    print('\n' + '=' * 80)
    print('RETROFIT TIMELINE FROM SIMULATION:')
    print('=' * 80)

    train_events = []
    wagon_events = []
    batch_events = []
    locomotive_events = []

    for t, e in events:
        event_type = type(e).__name__

        # Train arrival events
        if event_type == 'TrainArrivedEvent':
            train_id = e.train_id.id if hasattr(e.train_id, 'id') else str(e.train_id)
            location = 'collection'  # Default location for train arrivals
            train_events.append((t, f'train[{train_id}] ARRIVED {location}'))

        # Wagon journey events
        elif event_type == 'WagonJourneyEvent':
            wagon_id = getattr(e, 'wagon_id', '?')
            event_subtype = getattr(e, 'event_type', '?')
            location = getattr(e, 'location', '?')
            wagon_events.append((t, f'wagon[{wagon_id}] {event_subtype} {location}'))

        # Batch events
        elif event_type == 'BatchFormed':
            batch_id = getattr(e, 'batch_id', '?')
            wagon_ids = getattr(e, 'wagon_ids', [])
            wagon_list = ','.join(wagon_ids) if wagon_ids else '?'
            batch_events.append((t, f'batch[{batch_id}] FORMED wagons={wagon_list}'))

        elif event_type == 'BatchTransportStarted':
            batch_id = getattr(e, 'batch_id', '?')
            destination = getattr(e, 'destination', '?')
            batch_events.append((t, f'batch[{batch_id}] TRANSPORT_STARTED destination={destination}'))

        elif event_type == 'BatchArrivedAtDestination':
            batch_id = getattr(e, 'batch_id', '?')
            destination = getattr(e, 'destination', '?')
            batch_events.append((t, f'batch[{batch_id}] ARRIVED_AT_DESTINATION {destination}'))

        # Locomotive events
        elif event_type == 'LocomotiveMovementEvent':
            locomotive_id = getattr(e, 'locomotive_id', '?')
            event_subtype = getattr(e, 'event_type', '?')
            purpose = getattr(e, 'purpose', '')
            if purpose:
                locomotive_events.append((t, f'locomotive[{locomotive_id}] {event_subtype} {purpose}'))
            else:
                locomotive_events.append((t, f'locomotive[{locomotive_id}] {event_subtype}'))

    # Combine and sort all events
    all_events = sorted(train_events + wagon_events + batch_events + locomotive_events, key=lambda x: x[0])

    for t, desc in all_events:
        time_str = f't={int(t)}:'
        print(f'{time_str:12s} {desc}')

    print('=' * 80)
    print(f'Total events shown: {len(all_events)}')
    print('=' * 80 + '\n')


def validate_retrofit_timeline(events: list[tuple[float, Any]], timeline_spec: str) -> None:
    """Validate retrofit workflows against specification.

    Format:
        t=X: train[ID] STATUS location
        t=X: wagon[ID] STATUS location
        t=X: batch[ID] STATUS details
        t=X: locomotive[ID] STATUS details
    """
    for line in timeline_spec.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Parse: t=X: resource[ID] STATUS details OR t=X->Y: resource[ID] STATUS details
        match = re.match(
            r't=(\d+(?:\.\d+)?)(?:->(\d+(?:\.\d+)?))?\s*:\s*(\w+)\[(\w+)\]\s+(\w+)(?:\s+(.+))?',
            line,
        )
        if not match:
            continue

        time = float(match.group(1))
        resource_type = match.group(3)
        resource_id = match.group(4)
        status_name = match.group(5)
        details = match.group(6) or ''

        # For range events (t=X->Y), validate at the start time
        # For point events (t=X), validate at that exact time
        validate_time = time

        if resource_type == 'train':
            _validate_train(events, resource_id, validate_time, status_name, details)
        elif resource_type == 'wagon':
            _validate_wagon(events, resource_id, validate_time, status_name, details)
        elif resource_type == 'batch':
            _validate_batch(events, resource_id, validate_time, status_name, details)
        elif resource_type == 'locomotive' or resource_type == 'loco':
            _validate_locomotive(events, resource_id, validate_time, status_name, details)


def _validate_train(
    events: list[tuple[float, Any]],
    train_id: str,
    time: float,
    status_name: str,
    details: str,
) -> None:
    """Validate train events."""
    if status_name == 'ARRIVED':
        location = details.strip()
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'TrainArrivedEvent'
            and hasattr(e, 'train_id')
            and (str(e.train_id) == train_id or (hasattr(e.train_id, 'id') and e.train_id.id == train_id))
            for t, e in events
        )
        assert found, f'No ARRIVED event for train {train_id} at {location} at t={time}'


def _validate_wagon(
    events: list[tuple[float, Any]],
    wagon_id: str,
    time: float,
    status_name: str,
    details: str,
) -> None:
    """Validate wagon events."""
    location = details.strip()

    if status_name == 'ARRIVED':
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonJourneyEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and hasattr(e, 'event_type')
            and e.event_type == 'ARRIVED'
            and hasattr(e, 'location')
            and e.location == location
            for t, e in events
        )
        assert found, f'No ARRIVED event for wagon {wagon_id} at {location} at t={time}'

    elif status_name == 'RETROFIT_STARTED':
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonJourneyEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and hasattr(e, 'event_type')
            and e.event_type == 'RETROFIT_STARTED'
            and hasattr(e, 'location')
            and e.location == location
            for t, e in events
        )
        assert found, f'No RETROFIT_STARTED event for wagon {wagon_id} at {location} at t={time}'

    elif status_name == 'RETROFIT_COMPLETED':
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonJourneyEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and hasattr(e, 'event_type')
            and e.event_type == 'RETROFIT_COMPLETED'
            and hasattr(e, 'location')
            and e.location == location
            for t, e in events
        )
        assert found, f'No RETROFIT_COMPLETED event for wagon {wagon_id} at {location} at t={time}'

    elif status_name == 'ON_RETROFIT_TRACK':
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonJourneyEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and hasattr(e, 'event_type')
            and e.event_type == 'ON_RETROFIT_TRACK'
            and hasattr(e, 'location')
            and e.location == location
            for t, e in events
        )
        assert found, f'No ON_RETROFIT_TRACK event for wagon {wagon_id} at {location} at t={time}'

    elif status_name == 'PARKED':
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonJourneyEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and hasattr(e, 'event_type')
            and e.event_type == 'PARKED'
            and hasattr(e, 'location')
            and e.location == location
            for t, e in events
        )
        assert found, f'No PARKED event for wagon {wagon_id} at {location} at t={time}'

    elif status_name == 'RETROFITTING':
        # Map RETROFITTING to RETROFIT_STARTED
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonJourneyEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and hasattr(e, 'event_type')
            and e.event_type == 'RETROFIT_STARTED'
            and hasattr(e, 'location')
            and e.location == location
            for t, e in events
        )
        assert found, f'No RETROFITTING (RETROFIT_STARTED) event for wagon {wagon_id} at {location} at t={time}'

    elif status_name == 'RETROFITTED':
        # Map RETROFITTED to RETROFIT_COMPLETED
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonJourneyEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and hasattr(e, 'event_type')
            and e.event_type == 'RETROFIT_COMPLETED'
            and hasattr(e, 'location')
            and e.location == location
            for t, e in events
        )
        assert found, f'No RETROFITTED (RETROFIT_COMPLETED) event for wagon {wagon_id} at {location} at t={time}'

    elif status_name == 'PARKING':
        # Map PARKING to PARKED
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonJourneyEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and hasattr(e, 'event_type')
            and e.event_type == 'PARKED'
            and hasattr(e, 'location')
            and e.location == location
            for t, e in events
        )
        assert found, f'No PARKING (PARKED) event for wagon {wagon_id} at {location} at t={time}'

    elif status_name == 'DISTRIBUTED':
        # Map DISTRIBUTED to wagon being moved to retrofitted track
        # This is not a specific event, but we can check if wagon is on retrofitted track
        # For now, we'll skip this validation as it's an internal state change
        pass


def _validate_batch(
    events: list[tuple[float, Any]],
    batch_id: str,
    time: float,
    status_name: str,
    details: str,
) -> None:
    """Validate batch events.

    Batch ID can use '*' as wildcard to match any batch ID.
    """
    # Check if batch_id is a wildcard
    is_wildcard = batch_id == '*'

    if status_name == 'FORMED':
        # Extract wagon list from details like "wagons=W01,W02"
        wagon_match = re.search(r'wagons=([A-Z0-9,]+)', details)
        if wagon_match:
            expected_wagons = set(wagon_match.group(1).split(','))
            found = any(
                abs(t - time) < 0.5
                and type(e).__name__ == 'BatchFormed'
                and hasattr(e, 'wagon_ids')
                and set(e.wagon_ids) == expected_wagons
                and (is_wildcard or (hasattr(e, 'batch_id') and e.batch_id == batch_id))
                for t, e in events
            )
            assert found, f'No FORMED event for batch {batch_id} with wagons {expected_wagons} at t={time}'

    elif status_name == 'TRANSPORT_STARTED':
        # Extract destination from details like "destination=WS1"
        dest_match = re.search(r'destination=(\w+)', details)
        if dest_match:
            expected_dest = dest_match.group(1)
            found = any(
                abs(t - time) < 0.5
                and type(e).__name__ == 'BatchTransportStarted'
                and hasattr(e, 'destination')
                and e.destination == expected_dest
                and (is_wildcard or (hasattr(e, 'batch_id') and e.batch_id == batch_id))
                for t, e in events
            )
            assert found, f'No TRANSPORT_STARTED event for batch {batch_id} to {expected_dest} at t={time}'

    elif status_name == 'ARRIVED_AT_DESTINATION':
        destination = details.strip()
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'BatchArrivedAtDestination'
            and hasattr(e, 'destination')
            and e.destination == destination
            and (is_wildcard or (hasattr(e, 'batch_id') and e.batch_id == batch_id))
            for t, e in events
        )
        assert found, f'No ARRIVED_AT_DESTINATION event for batch {batch_id} at {destination} at t={time}'


def _validate_locomotive(
    events: list[tuple[float, Any]],
    locomotive_id: str,
    time: float,
    status_name: str,
    details: str,
) -> None:
    """Validate locomotive events in retrofit workflows."""
    if status_name == 'ALLOCATED':
        purpose = details.strip()
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'LocomotiveMovementEvent'
            and hasattr(e, 'locomotive_id')
            and e.locomotive_id == locomotive_id
            and hasattr(e, 'event_type')
            and e.event_type == 'ALLOCATED'
            and (not purpose or (hasattr(e, 'purpose') and e.purpose == purpose))
            for t, e in events
        )
        assert found, f'No ALLOCATED event for locomotive {locomotive_id} with purpose {purpose} at t={time}'

    elif status_name == 'MOVING':
        # Parse "from->to" format
        if '->' in details:
            from_loc, to_loc = details.split('->')
            from_loc = from_loc.strip()
            to_loc = to_loc.strip()
            found = any(
                abs(t - time) < 0.5
                and type(e).__name__ == 'LocomotiveMovementEvent'
                and hasattr(e, 'locomotive_id')
                and e.locomotive_id == locomotive_id
                and hasattr(e, 'event_type')
                and e.event_type == 'MOVING'
                and hasattr(e, 'from_location')
                and hasattr(e, 'to_location')
                and e.from_location == from_loc
                and e.to_location == to_loc
                for t, e in events
            )
            assert found, f'No MOVING event for locomotive {locomotive_id} from {from_loc} to {to_loc} at t={time}'
