"""Integration example for PopUp Retrofit Context."""

from datetime import UTC
from datetime import datetime

from popup_retrofit.application.popup_context import PopUpRetrofitContext
from workshop_operations.domain.entities.wagon import CouplerType
from workshop_operations.domain.entities.wagon import Wagon


def main() -> None:
    """Demonstrate PopUp Retrofit Context usage."""
    # Initialize context
    popup_context = PopUpRetrofitContext()

    # Create a PopUp workshop
    workshop = popup_context.create_workshop(workshop_id='popup_001', location='Hamburg Terminal', num_bays=3)

    print(f'Created workshop: {workshop.workshop_id} at {workshop.location}')
    print(f'Bays: {len(workshop.retrofit_bays)}')

    # Start operations
    popup_context.start_workshop_operations('popup_001')
    print(f'Workshop status: {workshop.status.value}')

    # Create a wagon needing retrofit
    wagon = Wagon(
        id='wagon_001',
        length=15.0,
        is_loaded=False,
        needs_retrofit=True,
        arrival_time=datetime.now(UTC),
        coupler_type=CouplerType.SCREW,
    )

    print(f'Processing wagon {wagon.id} with {wagon.coupler_type.value} coupler')

    # Process retrofit
    result = popup_context.process_wagon_retrofit('popup_001', wagon)

    print(f'Retrofit result: {result.success}, Duration: {result.duration} minutes')
    print(f'Wagon coupler type after retrofit: {wagon.coupler_type.value}')


if __name__ == '__main__':
    main()
