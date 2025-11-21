"""Declarative sequence validator for simulation tests."""

import re
from typing import Any


def validate_sequence(docstring: str, popup_sim: Any) -> None:
    """Parse docstring and validate simulation sequence.
    
    Format:
        wagon[ID] retrofit_start=TIME retrofit_end=TIME track=TRACK
        loco[ID] at t=TIME status=STATUS
    """
    if not docstring or "SEQUENCE:" not in docstring:
        return
    
    seq_start = docstring.index("SEQUENCE:")
    seq_section = docstring[seq_start:].split("\n\n")[0]
    
    for line in seq_section.split("\n"):
        line = line.strip()
        if not line or line == "SEQUENCE:":
            continue
            
        # Parse wagon timing: wagon[ID] retrofit_start=T1 retrofit_end=T2
        wagon_match = re.match(r'wagon\[(\w+)\]\s+retrofit_start=([\d.]+)\s+retrofit_end=([\d.]+)(?:\s+track=(\w+))?', line)
        if wagon_match:
            wagon_id, start, end, track = wagon_match.groups()
            _validate_wagon_timing(popup_sim, wagon_id, float(start), float(end), track)
            continue
        
        # Parse loco status: loco[ID] at t=TIME status=STATUS
        loco_match = re.match(r'loco\[(\w+)\]\s+at\s+t=([\d.]+)\s+status=(\w+)', line)
        if loco_match:
            loco_id, time, status = loco_match.groups()
            _validate_loco_status(popup_sim, loco_id, float(time), status)


def _validate_wagon_timing(popup_sim: Any, wagon_id: str, start: float, end: float, track: str | None) -> None:
    """Validate wagon retrofit timing."""
    wagon = next((w for w in popup_sim.wagons_queue if w.wagon_id == wagon_id), None)
    assert wagon, f"Wagon {wagon_id} not found"
    assert wagon.retrofit_start_time == start, f"wagon[{wagon_id}] retrofit_start expected {start}, got {wagon.retrofit_start_time}"
    assert wagon.retrofit_end_time == end, f"wagon[{wagon_id}] retrofit_end expected {end}, got {wagon.retrofit_end_time}"
    if track:
        assert wagon.track_id == track, f"wagon[{wagon_id}] track expected {track}, got {wagon.track_id}"


def _validate_loco_status(popup_sim: Any, loco_id: str, time: float, status: str) -> None:
    """Validate locomotive status at specific time."""
    loco = next((l for l in popup_sim.locomotives_queue if l.locomotive_id == loco_id), None)
    assert loco, f"Loco {loco_id} not found"
    history = [h for h in loco.status_history if h['time'] == time and h['status'].name == status]
    assert history, f"loco[{loco_id}] at t={time} expected {status}, not found in history"
