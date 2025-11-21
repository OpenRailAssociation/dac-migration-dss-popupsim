"""Timeline-based test validator for simulation scenarios."""

import re
from typing import Any
from models.locomotive import LocoStatus
from models.wagon import WagonStatus


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
        resource_type = match.group(4)
        resource_id = match.group(5)
        status_name = match.group(6)
        rest = match.group(7) or ""
        
        if resource_type == "loco":
            _validate_loco(popup_sim, resource_id, time, status_name, rest)
        elif resource_type == "wagon":
            _validate_wagon(popup_sim, resource_id, time, status_name, rest)


def _validate_loco(popup_sim: Any, loco_id: str, time: float, status_name: str, rest: str) -> None:
    """Validate locomotive state at specific time."""
    loco = next((l for l in popup_sim.locomotives_queue if l.locomotive_id == loco_id), None)
    assert loco, f"Loco {loco_id} not found"
    
    status = LocoStatus[status_name.upper()]
    history = [h for h in loco.status_history if h[0] == time and h[1] == status]
    assert history, f"t={time}: loco[{loco_id}] expected {status_name}, not found"


def _validate_wagon(popup_sim: Any, wagon_id: str, time: float, status_name: str, rest: str) -> None:
    """Validate wagon state at specific time."""
    wagon = next((w for w in popup_sim.wagons_queue if w.wagon_id == wagon_id), None)
    assert wagon, f"Wagon {wagon_id} not found"
    
    # Check timing
    if "retrofit_start" in rest:
        assert wagon.retrofit_start_time == time, f"wagon[{wagon_id}] retrofit_start expected {time}, got {wagon.retrofit_start_time}"
    if "retrofit_end" in rest:
        assert wagon.retrofit_end_time == time, f"wagon[{wagon_id}] retrofit_end expected {time}, got {wagon.retrofit_end_time}"
    
    # Check track
    if "track=" in rest:
        track = re.search(r'track=(\w+)', rest).group(1)
        assert wagon.track_id == track, f"wagon[{wagon_id}] track expected {track}, got {wagon.track_id}"


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
    assert len(history) == len(transitions), f"Expected {len(transitions)} transitions, got {len(history)}"
    
    for i, ((exp_time, exp_status), (act_time, act_status)) in enumerate(zip(transitions, history)):
        assert act_time == exp_time, f"[{i}] Expected t={exp_time}, got t={act_time}"
        assert act_status == exp_status, f"[{i}] Expected {exp_status}, got {act_status}"
