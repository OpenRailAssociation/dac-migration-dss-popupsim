"""Orchestration context protocol for coordinators."""

from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from configuration.domain.models.scenario import Scenario
    from popup_retrofit.application.popup_context import PopUpRetrofitContext
    from workshop_operations.domain.entities.track import Track
    from workshop_operations.domain.entities.wagon import Wagon
    from workshop_operations.domain.entities.workshop import Workshop
    from workshop_operations.domain.services.wagon_operations import (
        WagonSelector,
        WagonStateManager,
    )
    from workshop_operations.infrastructure.resources.track_capacity_manager import (
        TrackCapacityManager,
    )
    from workshop_operations.infrastructure.resources.workshop_capacity_manager import (
        WorkshopCapacityManager,
    )
    from yard_operations.application.yard_operations_context import (
        YardOperationsContext,
    )


class OrchestrationContext(Protocol):  # pylint: disable=too-many-public-methods
    """Protocol for objects providing orchestration context to coordinators."""

    @property
    def sim(self) -> Any:
        """Simulation engine."""

    @property
    def scenario(self) -> "Scenario":
        """Scenario configuration."""

    @property
    def locomotives(self) -> Any:
        """Locomotive resource pool."""

    @property
    def wagons(self) -> list["Wagon"]:
        """Collection of wagons to process."""

    @property
    def rejected_wagons(self) -> list["Wagon"]:
        """Collection of rejected wagons."""

    @property
    def workshops(self) -> list["Workshop"]:
        """Collection of workshops."""

    @property
    def workshop_capacity(self) -> "WorkshopCapacityManager":
        """Workshop capacity manager."""

    @property
    def yard_operations(self) -> "YardOperationsContext":
        """Yard operations context."""

    @property
    def wagons_ready_for_stations(self) -> dict[str, Any]:
        """Wagons ready for retrofit stations."""

    @property
    def wagons_completed(self) -> dict[str, Any]:
        """Completed wagons."""

    @property
    def retrofitted_wagons_ready(self) -> Any:
        """Retrofitted wagons ready store."""

    @property
    def train_processed_event(self) -> Any:
        """Train processed event."""

    @train_processed_event.setter
    def train_processed_event(self, value: Any) -> None:
        """Set train processed event."""

    @property
    def track_capacity(self) -> "TrackCapacityManager":
        """Track capacity manager."""

    @property
    def locomotive_service(self) -> Any:
        """Locomotive service."""

    @property
    def parking_tracks(self) -> list["Track"]:
        """Parking tracks."""

    @property
    def popup_retrofit(self) -> "PopUpRetrofitContext":
        """PopUp retrofit context."""

    @property
    def metrics(self) -> Any:
        """Metrics collector."""

    @property
    def wagon_selector(self) -> "WagonSelector":
        """Wagon selector service."""

    @property
    def wagon_state(self) -> "WagonStateManager":
        """Wagon state manager."""

    def put_wagon_for_station(
        self, workshop_track_id: str, retrofit_track_id: str, wagon: "Wagon"
    ) -> Generator[Any, Any, bool]:
        """Put wagon for station processing."""

    def put_completed_wagon(
        self, workshop_track_id: str, wagon: "Wagon"
    ) -> Generator[Any, Any, bool]:
        """Put completed wagon."""
