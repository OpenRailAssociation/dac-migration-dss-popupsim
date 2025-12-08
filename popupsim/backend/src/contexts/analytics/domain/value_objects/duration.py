"""Duration value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Duration:
    """Time duration in seconds."""

    seconds: float

    def __post_init__(self) -> None:
        """Validate duration."""
        if self.seconds < 0:
            msg = 'Duration cannot be negative'
            raise ValueError(msg)

    def to_minutes(self) -> float:
        """Convert to minutes."""
        return self.seconds / 60

    def to_hours(self) -> float:
        """Convert to hours."""
        return self.seconds / 3600

    def to_days(self) -> float:
        """Convert to days."""
        return self.seconds / 86400

    @classmethod
    def from_minutes(cls, minutes: float) -> 'Duration':
        """Create from minutes."""
        return cls(minutes * 60)

    @classmethod
    def from_hours(cls, hours: float) -> 'Duration':
        """Create from hours."""
        return cls(hours * 3600)

    def __str__(self) -> str:
        """Return string representation."""
        if self.seconds < 60:
            return f'{self.seconds:.1f}s'
        if self.seconds < 3600:
            return f'{self.to_minutes():.1f}m'
        return f'{self.to_hours():.1f}h'
