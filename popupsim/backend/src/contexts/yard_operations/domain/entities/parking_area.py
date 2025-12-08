"""Parking area entity."""

from shared.domain.entities.wagon import Wagon


class ParkingArea:
    """Entity managing wagon parking operations."""

    def __init__(self, area_id: str, capacity: int) -> None:
        self.area_id = area_id
        self.capacity = capacity
        self.parked_wagons: list[Wagon] = []

    def park_wagon(self, wagon: Wagon) -> bool:
        """Park wagon if space available."""
        if len(self.parked_wagons) < self.capacity:
            self.parked_wagons.append(wagon)
            return True
        return False

    def remove_wagon(self, wagon_id: str) -> Wagon | None:
        """Remove wagon from parking area."""
        for i, wagon in enumerate(self.parked_wagons):
            if wagon.id == wagon_id:
                return self.parked_wagons.pop(i)
        return None

    def get_available_capacity(self) -> int:
        """Get available parking capacity."""
        return self.capacity - len(self.parked_wagons)

    def is_full(self) -> bool:
        """Check if parking area is full."""
        return len(self.parked_wagons) >= self.capacity
