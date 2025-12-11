"""PopUp retrofit domain events."""

from dataclasses import dataclass
from dataclasses import field
import time
import uuid


@dataclass(frozen=True)
class RetrofitStartedEvent:
    """Event fired when wagon retrofit starts."""

    wagon_id: str
    workshop_id: str
    bay_id: str
    event_timestamp: float
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class RetrofitCompletedEvent:  # pytlint: disable=too-many-instance-attributes
    """Event fired when wagon retrofit completes."""

    wagon_id: str
    workshop_id: str
    bay_id: str
    event_timestamp: float
    success: bool
    duration: float
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
