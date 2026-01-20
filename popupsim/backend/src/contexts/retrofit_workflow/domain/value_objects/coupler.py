"""Coupler value objects with compatibility rules."""

from dataclasses import dataclass
from enum import Enum


class CouplerType(Enum):
    """Coupler type enum."""

    SCREW = 'SCREW'
    DAC = 'DAC'
    HYBRID = 'HYBRID'


@dataclass(frozen=True)
class Coupler:
    """Coupler value object.

    Attributes
    ----------
        type: Type of coupler
        side: Which side ('A' or 'B' for wagons, 'FRONT' or 'BACK' for locos)
    """

    type: CouplerType
    side: str

    def can_couple_to(self, other: 'Coupler') -> bool:
        """Check if this coupler can couple to another.

        Rules:
        - SCREW couples only to SCREW
        - DAC couples only to DAC
        - HYBRID couples to SCREW, DAC, or HYBRID
        """
        if CouplerType.HYBRID in (self.type, other.type):
            return True

        return self.type == other.type
