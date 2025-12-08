"""Shared entities across all bounded contexts."""

from shared.domain.entities.wagon import (
    CouplerType,
    Wagon,
    WagonStatus,
)

__all__ = ["CouplerType", "Wagon", "WagonStatus"]
