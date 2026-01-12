"""Repository for managing Railway Yard aggregates."""

from contexts.railway_infrastructure.domain.aggregates.railway_yard import RailwayYard


class RailwayYardRepository:
    """Repository managing Railway Yard aggregates."""

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._yards: dict[str, RailwayYard] = {}

    def save(self, yard: RailwayYard) -> None:
        """Save yard aggregate."""
        self._yards[yard.yard_id] = yard

    def get(self, yard_id: str) -> RailwayYard | None:
        """Get yard by ID."""
        return self._yards.get(yard_id)

    def get_all(self) -> list[RailwayYard]:
        """Get all yards."""
        return list(self._yards.values())

    def exists(self, yard_id: str) -> bool:
        """Check if yard exists."""
        return yard_id in self._yards

    def delete(self, yard_id: str) -> bool:
        """Delete yard by ID."""
        if yard_id in self._yards:
            del self._yards[yard_id]
            return True
        return False
