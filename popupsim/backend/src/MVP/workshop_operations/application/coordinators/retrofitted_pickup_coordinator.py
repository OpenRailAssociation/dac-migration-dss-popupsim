"""Retrofitted wagon pickup coordination logic."""

from collections.abc import Generator
from typing import Any


def pickup_retrofitted_wagons(popupsim: Any) -> Generator[Any]:
    """Pick up retrofitted wagons."""
    # Implementation delegated to main popupsim module
    yield popupsim.sim.delay(1.0)
