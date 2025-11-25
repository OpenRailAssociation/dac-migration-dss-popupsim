"""Wagon pickup coordination logic."""

from collections.abc import Generator
from typing import Any


def pickup_wagons_to_retrofit(popupsim: Any) -> Generator[Any]:
    """Pick up wagons for retrofitting."""
    # Implementation delegated to main popupsim module
    yield popupsim.sim.delay(1.0)
