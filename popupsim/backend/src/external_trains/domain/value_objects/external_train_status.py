"""External train status value object."""

from enum import Enum


class ExternalTrainStatus(Enum):
    """Status of external train in the system."""

    SCHEDULED = 'scheduled'
    APPROACHING = 'approaching'
    ARRIVED = 'arrived'
    WAGONS_DELIVERED = 'wagons_delivered'
    DEPARTED = 'departed'
