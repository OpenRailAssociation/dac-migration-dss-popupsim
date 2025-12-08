"""Train ID value object for External Trains Context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainId:
    """Unique identifier for external trains."""

    id: str

    @property
    def value(self) -> str:
        """Get ID value for backward compatibility."""
        return self.id
