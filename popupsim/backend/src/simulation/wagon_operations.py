"""Legacy wagon operations - deprecated, use domain.wagon_operations instead."""

from domain.wagon_operations import WagonSelector
from domain.wagon_operations import WagonStateManager

__all__ = ['WagonSelector', 'WagonStateManager']
