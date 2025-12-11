"""Session ID value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionId:
    """Unique identifier for analytics session."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            msg = 'Session ID cannot be empty'
            raise ValueError(msg)

    def __str__(self) -> str:
        return self.value
