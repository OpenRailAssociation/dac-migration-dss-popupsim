"""Event ID value object."""

from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class EventId:
    """Unique identifier for analytics events."""

    value: str

    def __post_init__(self) -> None:
        """Validate event ID is not empty."""
        if not self.value or not self.value.strip():
            raise ValueError('Event ID cannot be empty')

    @classmethod
    def generate(cls) -> 'EventId':
        """Generate new unique event ID."""
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        """Return string representation of event ID."""
        return self.value
