"""Legacy locomotive coordinator - now uses enhanced shunting operations."""

from collections.abc import Generator
from typing import Any

from MVP.shunting_operations.application.shunting_locomotive_service import (
    ShuntingLocomotiveService,
)
from MVP.workshop_operations.domain.entities.locomotive import (
    Locomotive,
)
from MVP.workshop_operations.domain.entities.wagon import (
    CouplerType,
)


def move_locomotive(
    popupsim: Any, loco: Locomotive, from_track: str, to_track: str
) -> Generator[Any]:
    """Move locomotive between tracks (now enhanced with shunting operations)."""
    service = ShuntingLocomotiveService()
    return service.move(popupsim, loco, from_track, to_track)


def couple_wagons(
    popupsim: Any, loco: Locomotive, wagon_count: int, coupler_type: CouplerType
) -> Generator[Any]:
    """Couple wagons to locomotive (now enhanced with capacity validation)."""
    service = ShuntingLocomotiveService()
    return service.couple_wagons(popupsim, loco, wagon_count, coupler_type)


def decouple_wagons(
    popupsim: Any, loco: Locomotive, wagon_count: int
) -> Generator[Any]:
    """Decouple wagons from locomotive (now enhanced with capacity tracking)."""
    service = ShuntingLocomotiveService()
    return service.decouple_wagons(popupsim, loco, wagon_count)


def allocate_locomotive(popupsim: Any) -> Generator[Any, Any, Locomotive]:
    """Allocate locomotive from pool (now enhanced with shunting capabilities)."""
    service = ShuntingLocomotiveService()
    return service.allocate(popupsim)


def release_locomotive(popupsim: Any, loco: Locomotive) -> Generator[Any]:
    """Release locomotive to pool (now enhanced with shunting operations)."""
    service = ShuntingLocomotiveService()
    return service.release(popupsim, loco)
