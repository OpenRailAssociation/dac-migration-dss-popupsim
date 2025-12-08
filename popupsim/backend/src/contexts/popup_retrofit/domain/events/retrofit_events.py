"""PopUp retrofit domain events."""

import time
import uuid
from dataclasses import dataclass, field


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
class RetrofitCompletedEvent:
    """Event fired when wagon retrofit completes."""

    wagon_id: str
    workshop_id: str
    bay_id: str
    event_timestamp: float
    success: bool
    duration: float
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
