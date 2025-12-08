"""PopUp Retrofit Context for coordinating DAC installation operations."""

import asyncio
from typing import TYPE_CHECKING, Any

from workshop_operations.domain.entities.wagon import Wagon

from popup_retrofit.domain.aggregates.popup_workshop import (
    PopUpWorkshop,
    RetrofitResult,
)
from popup_retrofit.domain.entities.retrofit_bay import RetrofitBay

if TYPE_CHECKING:
    from simulation.domain.aggregates.simulation_session import SimulationSession

    from .services.retrofit_station_service import RetrofitStationService


class PopUpRetrofitContext:
    """Context for managing PopUp retrofit operations implementing BoundedContextPort."""

    def __init__(self) -> None:
        """Initialize PopUp retrofit context."""
        self._workshops: dict[str, PopUpWorkshop] = {}
        self._station_service: RetrofitStationService | None = None
        self._simpy_coordinator: Any = None
        self.session: SimulationSession | None = None

    def initialize(self, simulation_session: "SimulationSession") -> None:
        """Initialize context with simulation session."""
        self.session = simulation_session
        self.initialize_station_service(simulation_session.engine)  # type: ignore[arg-type]

    def start_processes(self) -> None:
        """Start retrofit simulation processes."""
        # PopUp operations are passive (triggered by workshop context)

    def get_metrics(self) -> dict[str, Any]:
        """Get retrofit metrics."""
        return self._compute_all_workshop_metrics()

    def cleanup(self) -> None:
        """Cleanup resources."""

    def create_workshop(
        self, workshop_id: str, location: str, num_bays: int = 2
    ) -> PopUpWorkshop:
        """Create a new PopUp workshop.

        Args:
            workshop_id: Unique identifier for workshop
            location: Workshop location
            num_bays: Number of retrofit bays

        Returns
        -------
            Created PopUp workshop
        """
        # Create retrofit bays
        bays = [RetrofitBay(bay_id=f"{workshop_id}_bay_{i}") for i in range(num_bays)]

        workshop = PopUpWorkshop(
            workshop_id=workshop_id, location=location, retrofit_bays=bays
        )

        self._workshops[workshop_id] = workshop
        return workshop

    def get_workshop(self, workshop_id: str) -> PopUpWorkshop | None:
        """Get workshop by ID."""
        return self._workshops.get(workshop_id)

    def start_workshop_operations(self, workshop_id: str) -> None:
        """Start operations for a workshop."""
        workshop = self.get_workshop(workshop_id)
        if workshop:
            workshop.start_operations()

    def initialize_station_service(self, sim_adapter: Any) -> None:
        """Initialize the station service with simulation engine."""
        from .services.retrofit_station_service import (
            RetrofitStationService,  # pylint: disable=import-outside-toplevel
        )

        self._station_service = RetrofitStationService(sim_adapter)

    def get_station_service(self) -> "RetrofitStationService":
        """Get the station service."""
        if not self._station_service:
            raise ValueError(
                "Station service not initialized. Call initialize_station_service first."
            )
        return self._station_service

    def process_wagon_retrofit(self, workshop_id: str, wagon: Wagon) -> RetrofitResult:
        """Process wagon retrofit at specified workshop.

        Args:
            workshop_id: ID of workshop to use
            wagon: Wagon to retrofit

        Returns
        -------
            Result of retrofit operation

        Raises
        ------
            ValueError: If workshop not found
        """
        workshop = self.get_workshop(workshop_id)
        if not workshop:
            raise ValueError(f"Workshop {workshop_id} not found")

        return workshop.process_wagon(wagon)

    def get_workshop_metrics(self, workshop_id: str) -> dict[str, float | str] | None:
        """Get performance metrics for a workshop."""
        workshop = self.get_workshop(workshop_id)
        if not workshop:
            return None
        return workshop.get_performance_summary()

    async def get_all_workshop_metrics_async(self) -> dict[str, dict[str, float | str]]:
        """Get performance metrics for all workshops asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._compute_all_workshop_metrics)

    def get_all_workshop_metrics(self) -> dict[str, dict[str, float | str]]:
        """Sync version for backward compatibility."""
        return self._compute_all_workshop_metrics()

    def _compute_all_workshop_metrics(self) -> dict[str, dict[str, float | str]]:
        """Compute all workshop metrics."""
        return {
            workshop_id: workshop.get_performance_summary()
            for workshop_id, workshop in self._workshops.items()
        }
