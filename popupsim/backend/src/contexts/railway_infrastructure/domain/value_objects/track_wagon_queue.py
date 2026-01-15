"""Track wagon queue for maintaining wagon sequence."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class TrackWagonQueue:
    """Queue maintaining wagon sequence on a track."""

    track_id: str
    _wagons: list[Any] = field(default_factory=list)

    def add_wagon(self, wagon: Any) -> None:
        """Add wagon to end of queue."""
        self._wagons.append(wagon)

    def remove_wagon(self, wagon_id: str) -> Any | None:
        """Remove wagon by ID, maintaining sequence."""
        for i, wagon in enumerate(self._wagons):
            if wagon.id == wagon_id:
                return self._wagons.pop(i)
        return None

    def get_wagons(self) -> list[Any]:
        """Get wagons in sequence order."""
        return self._wagons.copy()

    def get_wagon_count(self) -> int:
        """Get number of wagons."""
        return len(self._wagons)

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._wagons) == 0

    def clear(self) -> list[Any]:
        """Clear all wagons and return them."""
        wagons = self._wagons.copy()
        self._wagons.clear()
        return wagons
