"""Minimal base domain event - contexts define their own."""

from dataclasses import dataclass
from dataclasses import field
import time
import uuid


@dataclass(frozen=True)
class DomainEvent:
    """Minimal base event - contexts define their own specific events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
