"""Shared entities across all bounded contexts."""

from shared.domain.entities.wagon import CouplerType
from shared.domain.entities.wagon import Wagon
from shared.domain.entities.wagon import WagonStatus

__all__ = ['CouplerType', 'Wagon', 'WagonStatus']
