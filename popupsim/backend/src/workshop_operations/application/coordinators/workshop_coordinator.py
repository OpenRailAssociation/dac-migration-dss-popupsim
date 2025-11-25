"""Workshop coordination logic."""

from collections.abc import Generator
from typing import Any


def move_wagons_to_stations(popupsim: Any) -> Generator[Any]:
    """Move wagons to workshop stations."""
    # Implementation delegated to main popupsim module
    yield popupsim.sim.delay(1.0)


def process_single_wagon(popupsim: Any, _wagon: Any, _track_id: str) -> Generator[Any]:
    """Process a single wagon through workshop."""
    # Implementation delegated to main popupsim module
    yield popupsim.sim.delay(1.0)
