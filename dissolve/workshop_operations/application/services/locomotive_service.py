"""Locomotive service interface - clean architecture without circular imports."""

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.entities.wagon import CouplerType


class LocomotiveService(ABC):
    """Service interface for locomotive operations."""

    @abstractmethod
    def allocate(self, popupsim: Any) -> Generator[Any, Any, Locomotive]:
        """Allocate locomotive from pool."""

    @abstractmethod
    def release(self, popupsim: Any, loco: Locomotive) -> Generator[Any]:
        """Release locomotive to pool."""

    @abstractmethod
    def move(
        self, popupsim: Any, loco: Locomotive, from_track: str, to_track: str
    ) -> Generator[Any]:
        """Move locomotive between tracks."""

    @abstractmethod
    def couple_wagons(
        self,
        popupsim: Any,
        loco: Locomotive,
        wagon_count: int,
        coupler_type: CouplerType,
    ) -> Generator[Any]:
        """Couple wagons to locomotive."""

    @abstractmethod
    def decouple_wagons(
        self,
        popupsim: Any,
        loco: Locomotive,
        wagon_count: int,
        coupler_type: CouplerType | None = None,
    ) -> Generator[Any]:
        """Decouple wagons from locomotive."""


# DefaultLocomotiveService removed - use ShuntingLocomotiveService directly
# This eliminates circular dependencies and unnecessary wrapper complexity
