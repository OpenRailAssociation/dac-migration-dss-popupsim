"""PopUp Retrofit Context for coordinating DAC installation operations."""

from typing import TYPE_CHECKING

from workshop_operations.domain.entities.wagon import Wagon

from ..domain.aggregates.popup_workshop import PopUpWorkshop
from ..domain.aggregates.popup_workshop import RetrofitResult
from ..domain.entities.retrofit_bay import RetrofitBay

if TYPE_CHECKING:
    from workshop_operations.infrastructure.simulation.simpy_adapter import SimulationAdapter

    from .services.retrofit_station_service import RetrofitStationService


class PopUpRetrofitContext:
    """Context for managing PopUp retrofit operations."""

    def __init__(self) -> None:
        """Initialize PopUp retrofit context."""
        self._workshops: dict[str, PopUpWorkshop] = {}
        self._station_service: RetrofitStationService | None = None

    def create_workshop(self, workshop_id: str, location: str, num_bays: int = 2) -> PopUpWorkshop:
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
        bays = [RetrofitBay(bay_id=f'{workshop_id}_bay_{i}') for i in range(num_bays)]

        workshop = PopUpWorkshop(workshop_id=workshop_id, location=location, retrofit_bays=bays)

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

    def initialize_station_service(self, sim_adapter: 'SimulationAdapter') -> None:
        """Initialize the station service with SimPy adapter."""
        from .services.retrofit_station_service import RetrofitStationService  # pylint: disable=import-outside-toplevel

        self._station_service = RetrofitStationService(sim_adapter, self)

    def get_station_service(self) -> 'RetrofitStationService':
        """Get the station service."""
        if not self._station_service:
            raise ValueError('Station service not initialized. Call initialize_station_service first.')
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
            raise ValueError(f'Workshop {workshop_id} not found')

        return workshop.process_wagon(wagon)

    def get_workshop_metrics(self, workshop_id: str) -> dict[str, float | str] | None:
        """Get performance metrics for a workshop."""
        workshop = self.get_workshop(workshop_id)
        if not workshop:
            return None
        return workshop.get_performance_summary()

    async def get_all_workshop_metrics_async(self) -> dict[str, dict[str, float | str]]:
        """Get performance metrics for all workshops asynchronously."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._compute_all_workshop_metrics)
    
    def get_all_workshop_metrics(self) -> dict[str, dict[str, float | str]]:
        """Sync version for backward compatibility."""
        return self._compute_all_workshop_metrics()
    
    def _compute_all_workshop_metrics(self) -> dict[str, dict[str, float | str]]:
        """Internal method to compute all workshop metrics."""
        return {workshop_id: workshop.get_performance_summary() for workshop_id, workshop in self._workshops.items()}
