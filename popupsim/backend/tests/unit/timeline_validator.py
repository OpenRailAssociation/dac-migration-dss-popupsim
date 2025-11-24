"""Timeline-based test validator for simulation scenarios."""

import re
from typing import Any

from models.locomotive import LocoStatus


def validate_timeline(popup_sim: Any, timeline_spec: str) -> None:
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
        match = re.match(r't=(\d+(?:\.\d+)?)((?:->|→)(\d+(?:\.\d+)?))?\s*:\s*(\w+)\[(\w+)\]\s+(\w+)(?:\s+(.+))?', line)
        if not match:
            continue

        time = float(match.group(1))
        end_time = float(match.group(3)) if match.group(3) else None
        resource_type = match.group(4)
        resource_id = match.group(5)
        status_name = match.group(6)
        rest = match.group(7) or ''

        if resource_type == 'loco':
            _validate_loco(popup_sim, resource_id, time, status_name, rest, end_time)
        elif resource_type == 'wagon':
            _validate_wagon(popup_sim, resource_id, time, status_name, rest)


def _validate_loco(
    popup_sim: Any, loco_id: str, time: float, status_name: str, rest: str, end_time: float | None = None
) -> None:
    """Validate locomotive state at specific time."""
    loco = next((locomotive for locomotive in popup_sim.locomotives_queue if locomotive.locomotive_id == loco_id), None)
    assert loco, f'Loco {loco_id} not found'

    status = LocoStatus[status_name.upper()]
    history = [h for h in loco.status_history if h[0] == time and h[1] == status]
    assert history, f't={time}: loco[{loco_id}] expected {status_name}, not found'

    # Validate route duration if time range and route specified
    if end_time and status == LocoStatus.MOVING:
        route_match = re.search(r'(\w+)(?:->|→)(\w+)', rest)
        if route_match:
            from_track, to_track = route_match.groups()
            expected_duration = end_time - time
            # Find actual route duration
            from simulation.route_finder import find_route

            route = find_route(popup_sim.scenario.routes, from_track, to_track)
            if route and route.duration:
                assert route.duration == expected_duration, (
                    f't={time}->{end_time}: loco[{loco_id}] route {from_track}->{to_track} expected duration {expected_duration}, got {route.duration}'
                )


def _validate_wagon(popup_sim: Any, wagon_id: str, time: float, _status_name: str, rest: str) -> None:
    """Validate wagon state at specific time."""
    wagon = next((w for w in popup_sim.wagons_queue if w.wagon_id == wagon_id), None)
    assert wagon, f'Wagon {wagon_id} not found'

    # Check timing
    if 'retrofit_start' in rest:
        assert wagon.retrofit_start_time == time, (
            f'wagon[{wagon_id}] retrofit_start expected {time}, got {wagon.retrofit_start_time}'
        )
    if 'retrofit_end' in rest:
        assert wagon.retrofit_end_time == time, (
            f'wagon[{wagon_id}] retrofit_end expected {time}, got {wagon.retrofit_end_time}'
        )

    # Check track
    if 'track=' in rest:
        track = re.search(r'track=(\w+)', rest).group(1)
        assert wagon.track_id == track, f'wagon[{wagon_id}] track expected {track}, got {wagon.track_id}'


def validate_loco_timeline(loco: Any, timeline_spec: str) -> None:
    """Validate locomotive state history (legacy format)."""
    transitions = []

    for line in timeline_spec.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        match = re.match(r't=(\d+(?:\.\d+)?)((?:->|→)(\d+(?:\.\d+)?))?\s*:\s*(\w+)', line)
        if not match:
            continue

        time = float(match.group(1))
        status_name = match.group(4)

        try:
            status = LocoStatus[status_name.upper()]
            transitions.append((time, status))
        except KeyError:
            continue

    history = loco.status_history
    assert len(history) == len(transitions), f'Expected {len(transitions)} transitions, got {len(history)}'

    for i, ((exp_time, exp_status), (act_time, act_status)) in enumerate(zip(transitions, history, strict=True)):
        assert act_time == exp_time, f'[{i}] Expected t={exp_time}, got t={act_time}'
        assert act_status == exp_status, f'[{i}] Expected {exp_status}, got {act_status}'


def validate_timeline_from_docstring(popup_sim: Any, test_func: Any) -> None:
    """Extract TIMELINE from test docstring and validate."""
    docstring = test_func.__doc__
    if not docstring or 'TIMELINE:' not in docstring:
        return

    timeline_start = docstring.index('TIMELINE:')
    timeline_section = docstring[timeline_start + len('TIMELINE:') :]
    validate_timeline(popup_sim, timeline_section)
