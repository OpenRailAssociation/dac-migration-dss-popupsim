"""Wagon entity - re-exported from shared kernel for backward compatibility.

DEPRECATED: Import from shared.domain.entities.wagon instead.
This module is kept for backward compatibility with existing MVP code.
"""

# Re-export from shared kernel
from shared.domain.entities.wagon import (
    CouplerType,
    Wagon,
    WagonStatus,
)

__all__ = ["CouplerType", "Wagon", "WagonStatus"]
