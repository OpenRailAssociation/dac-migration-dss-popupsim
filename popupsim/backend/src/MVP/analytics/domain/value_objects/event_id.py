"""Event ID value object."""

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventId:
    """Unique identifier for analytics events."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def generate(cls) -> "EventId":
        """Generate new event ID for backward compatibility."""
        return cls()

    @property
    def value(self) -> str:
        """Get ID value for backward compatibility."""
        return self.id

    def __str__(self) -> str:
        """Return string representation of event ID."""
        return self.id
