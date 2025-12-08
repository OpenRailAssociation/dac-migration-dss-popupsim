"""Factory for creating workshop_operations entities from configuration DTOs."""

from datetime import UTC, datetime

from MVP.configuration.application.dtos.locomotive_input_dto import (
    LocomotiveInputDTO,
)
from MVP.configuration.application.dtos.route_input_dto import (
    RouteInputDTO,
)
from MVP.configuration.application.dtos.workshop_input_dto import (
    WorkshopInputDTO,
)
from MVP.workshop_operations.domain.entities.locomotive import (
    Locomotive,
    LocoStatus,
)
from MVP.workshop_operations.domain.entities.workshop import (
    Workshop,
)
from MVP.workshop_operations.domain.value_objects.route import (
    Route,
)


class EntityFactory:
    """Factory for creating domain entities from DTOs."""

    @staticmethod
    def create_locomotive(dto: LocomotiveInputDTO) -> Locomotive:
        """Create Locomotive entity from DTO."""
        # Map DTO status to enum
        status_map = {
            "AVAILABLE": LocoStatus.PARKING,
            "MOVING": LocoStatus.MOVING,
            "COUPLING": LocoStatus.COUPLING,
            "DECOUPLING": LocoStatus.DECOUPLING,
        }

        return Locomotive(
            id=dto.id,
            name=f"Locomotive {dto.id}",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            track=dto.track,
            status=status_map.get(dto.status, LocoStatus.PARKING),
        )

    @staticmethod
    def create_workshop(dto: WorkshopInputDTO) -> Workshop:
        """Create Workshop entity from DTO."""
        return Workshop(
            id=dto.id,
            start_date="2025-01-01 00:00:00",
            end_date="2025-01-02 00:00:00",
            track=dto.track,
            retrofit_stations=dto.retrofit_stations,
        )

    @staticmethod
    def create_route(dto: RouteInputDTO) -> Route:
        """Create Route entity from DTO."""
        return Route(
            route_id=dto.id,
            from_track=dto.from_track,
            to_track=dto.to_track,
            duration=dto.duration,
            description=dto.description,
            path=dto.track_sequence,
        )
