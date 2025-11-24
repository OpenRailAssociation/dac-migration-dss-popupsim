"""Train arrival coordination logic."""

from collections.abc import Generator
from typing import Any


def process_train_arrivals(popupsim: Any) -> Generator[Any]:
    """Process train arrivals in simulation."""
    # Implementation delegated to main popupsim module
    yield popupsim.sim.delay(1.0)
