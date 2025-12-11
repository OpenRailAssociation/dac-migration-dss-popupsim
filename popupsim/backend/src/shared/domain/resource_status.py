"""Resource status enums for tracking."""

from enum import Enum


class LocoStatus(Enum):
    """Locomotive status events."""

    PARKING = 'parking'
    MOVING = 'moving'
    COUPLING = 'coupling'
    DECOUPLING = 'decoupling'


class WagonStatus(Enum):
    """Wagon status events."""

    ARRIVING = 'arriving'
    CLASSIFYING = 'classifying'
    WAITING = 'waiting'
    RETROFITTING = 'retrofitting'
    DEPARTING = 'departing'


class WorkshopStatus(Enum):
    """Workshop status events."""

    IDLE = 'idle'
    PROCESSING = 'processing'
    MAINTENANCE = 'maintenance'


class TrackStatus(Enum):
    """Track status events."""

    EMPTY = 'empty'
    OCCUPIED = 'occupied'
    BLOCKED = 'blocked'
