"""PopUp Retrofit Context for coordinating DAC installation operations."""

from workshop_operations.domain.entities.wagon import Wagon

from ..domain.aggregates.popup_workshop import PopUpWorkshop
from ..domain.aggregates.popup_workshop import RetrofitResult
from ..domain.entities.retrofit_bay import RetrofitBay


class PopUpRetrofitContext:
    """Context for managing PopUp retrofit operations."""

    def __init__(self) -> None:
        """Initialize PopUp retrofit context."""
        self._workshops: dict[str, PopUpWorkshop] = {}

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
