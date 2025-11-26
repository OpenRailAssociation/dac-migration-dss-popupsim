"""Event ID value object."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class EventId:
    """Unique identifier for analytics events."""
    
    value: str
    
    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Event ID cannot be empty")
    
    @classmethod
    def generate(cls) -> 'EventId':
        """Generate new unique event ID."""
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value