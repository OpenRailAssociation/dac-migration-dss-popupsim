"""Parking coordination logic."""

from collections.abc import Generator
from typing import Any


def move_to_parking(popupsim: Any) -> Generator[Any]:
    """Move wagons to parking."""
    # Implementation delegated to main popupsim module
    yield popupsim.sim.delay(1.0)
