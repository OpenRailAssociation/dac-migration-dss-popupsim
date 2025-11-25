"""Legacy locomotive coordinator - deprecated, use simulation.services instead."""

from collections.abc import Generator
from typing import Any

from workshop_operations.application.services.locomotive_service import DefaultLocomotiveService

from configuration.domain.models.locomotive import Locomotive
from configuration.domain.models.wagon import CouplerType


def move_locomotive(popupsim: Any, loco: Locomotive, from_track: str, to_track: str) -> Generator[Any]:
    """Move locomotive between tracks (deprecated)."""
    service = DefaultLocomotiveService()
    return service.move(popupsim, loco, from_track, to_track)


def couple_wagons(popupsim: Any, loco: Locomotive, wagon_count: int, coupler_type: CouplerType) -> Generator[Any]:
    """Couple wagons to locomotive (deprecated)."""
    service = DefaultLocomotiveService()
    return service.couple_wagons(popupsim, loco, wagon_count, coupler_type)


def decouple_wagons(popupsim: Any, loco: Locomotive, wagon_count: int) -> Generator[Any]:
    """Decouple wagons from locomotive (deprecated)."""
    service = DefaultLocomotiveService()
    return service.decouple_wagons(popupsim, loco, wagon_count)


def allocate_locomotive(popupsim: Any) -> Generator[Locomotive]:
    """Allocate locomotive from pool (deprecated)."""
    service = DefaultLocomotiveService()
    return service.allocate(popupsim)


def release_locomotive(popupsim: Any, loco: Locomotive) -> Generator[Any]:
    """Release locomotive to pool (deprecated)."""
    service = DefaultLocomotiveService()
    return service.release(popupsim, loco)
