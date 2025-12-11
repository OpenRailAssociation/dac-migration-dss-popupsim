"""Timeline-based test validator for new architecture simulation scenarios."""

import re
from typing import Any


def validate_timeline_from_docstring(result: Any, test_func: Any, analytics_context: Any = None) -> None:
    """Extract TIMELINE from test docstring and validate against simulation result.

    Args:
        result: SimulationResult with metrics
        test_func: Test function with TIMELINE in docstring
        analytics_context: AnalyticsContext for querying events and state
    """
    docstring = test_func.__doc__
    if not docstring or 'TIMELINE:' not in docstring:
        return

    timeline_start = docstring.index('TIMELINE:')
    timeline_section = docstring[timeline_start + len('TIMELINE:') :]

    events = analytics_context.get_metrics().get('event_history', []) if analytics_context else []
    _print_actual_timeline(events)
    validate_timeline(events, timeline_section)


def _print_actual_timeline(events: list[tuple[float, Any]]) -> None:
    """Print actual timeline from events for debugging."""
    print('\n' + '=' * 80)
    print('ACTUAL TIMELINE FROM SIMULATION:')
    print('=' * 80)

    loco_events = []
    wagon_events = []

    for t, e in events:
        event_type = type(e).__name__

        if event_type == 'LocomotiveMovementStartedEvent':
            loco_id = getattr(e, 'locomotive_id', '?')
            from_track = getattr(e, 'from_track', '?')
            to_track = getattr(e, 'to_track', '?')
            loco_events.append((t, f'loco[{loco_id}] MOVING {from_track}->{to_track}'))
        elif event_type == 'RetrofitStartedEvent':
            wagon_id = getattr(e, 'wagon_id', '?')
            wagon_events.append((t, f'wagon[{wagon_id}] RETROFITTING retrofit_start'))
        elif event_type in ('RetrofitCompletedEvent', 'WagonRetrofitCompletedEvent'):
            wagon_id = getattr(e, 'wagon_id', '?')
            wagon_events.append((t, f'wagon[{wagon_id}] RETROFITTED retrofit_end'))
        elif event_type == 'WagonParkedEvent':
            wagon_id = getattr(e, 'wagon_id', '?')
            track_id = getattr(e, 'track_id', '?')
            wagon_events.append((t, f'wagon[{wagon_id}] PARKING track={track_id}'))
        elif event_type == 'WagonDistributedEvent':
            wagon_id = getattr(e, 'wagon_id', '?')
            track_id = getattr(e, 'track_id', '?')
            wagon_events.append((t, f'wagon[{wagon_id}] DISTRIBUTED track={track_id}'))

    all_events = sorted(loco_events + wagon_events, key=lambda x: x[0])

    prev_time = None
    for t, desc in all_events:
        if prev_time is not None and t != prev_time:
            time_str = f't={int(prev_time)}->{int(t)}:' if t - prev_time >= 1.0 else f't={t:.1f}:'
        else:
            time_str = f't={int(t)}:'
        print(f'{time_str:12s} {desc}')
        prev_time = t

    if not any('PARKING' in e[1] or 'DISTRIBUTED' in e[1] for e in wagon_events):
        print('\n*** WARNING: No wagon parking/distribution events found!')

    print('=' * 80)
    print(f'Total events shown: {len(all_events)}')
    print('=' * 80 + '\n')


def validate_timeline(events: list[tuple[float, Any]], timeline_spec: str) -> None:
    """Validate simulation timeline against specification.

    Format:
        t=X: loco[ID] STATUS description
        t=X: wagon[ID] STATUS track=TRACK
        t=X->Y: loco[ID] STATUS from->to
    """
    for line in timeline_spec.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Parse: t=X: resource[ID] STATUS ...
        match = re.match(
            r't=(\d+(?:\.\d+)?)((?:->|→)(\d+(?:\.\d+)?))?\s*:\s*(\w+)\[(\w+)\]\s+(\w+)(?:\s+(.+))?',
            line,
        )
        if not match:
            continue

        time = float(match.group(1))
        end_time = float(match.group(3)) if match.group(3) else None
        resource_type = match.group(4)
        resource_id = match.group(5)
        status_name = match.group(6)
        rest = match.group(7) or ''

        if resource_type == 'loco':
            _validate_loco(events, resource_id, time, status_name, rest, end_time)
        elif resource_type == 'wagon':
            _validate_wagon(events, resource_id, time, status_name, rest)


def _validate_loco(
    events: list[tuple[float, Any]],
    loco_id: str,
    time: float,
    status_name: str,
    rest: str,
    end_time: float | None = None,
) -> None:
    """Validate locomotive state at specific time."""
    if status_name == 'MOVING':
        track_match = re.search(r'(\w+)->(\w+)', rest)
        if track_match:
            from_track = track_match.group(1)
            to_track = track_match.group(2)
            # Check if movement started within time window
            found = any(
                time <= t <= (end_time if end_time else time + 1.0)
                and type(e).__name__ == 'LocomotiveMovementStartedEvent'
                and hasattr(e, 'locomotive_id')
                and e.locomotive_id == loco_id
                and hasattr(e, 'from_track')
                and hasattr(e, 'to_track')
                and e.from_track == from_track
                and e.to_track == to_track
                for t, e in events
            )
            assert found, (
                f'No MOVING event for loco {loco_id} from {from_track} to {to_track} in window t={time}-{end_time or time + 1.0}'
            )


def _validate_wagon(
    events: list[tuple[float, Any]],
    wagon_id: str,
    time: float,
    status_name: str,
    rest: str,
) -> None:
    """Validate wagon state at specific time."""
    track_match = re.search(r'track=(\w+)', rest)
    if track_match:
        expected_track = track_match.group(1)
        # For track validation, check if wagon reached the track by this time
        found = any(
            t <= time
            and type(e).__name__
            in (
                'WagonLocationChangedEvent',
                'WagonDistributedEvent',
                'WagonParkedEvent',
            )
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            and (
                (hasattr(e, 'to_location') and e.to_location == expected_track)
                or (hasattr(e, 'track_id') and e.track_id == expected_track)
                or (hasattr(e, 'parking_area_id') and e.parking_area_id == expected_track)
            )
            for t, e in events
        )
        assert found, f'Wagon {wagon_id} not on track {expected_track} by t={time}'

    if status_name == 'RETROFITTING' and 'retrofit_start' in rest:
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'RetrofitStartedEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            for t, e in events
        )
        assert found, f'No RETROFITTING start for wagon {wagon_id} at t={time}'
    elif status_name == 'RETROFITTED' and 'retrofit_end' in rest:
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ in ('RetrofitCompletedEvent', 'WagonRetrofitCompletedEvent')
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            for t, e in events
        )
        assert found, f'No RETROFITTED event for wagon {wagon_id} at t={time}'
    elif status_name == 'PARKING':
        found = any(
            abs(t - time) < 0.5
            and type(e).__name__ == 'WagonParkedEvent'
            and hasattr(e, 'wagon_id')
            and e.wagon_id == wagon_id
            for t, e in events
        )
        assert found, f'No PARKING event for wagon {wagon_id} at t={time}'
