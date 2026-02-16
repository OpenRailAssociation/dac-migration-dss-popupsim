"""Wagon factory service for creating wagon entities.

Domain service responsible for wagon entity creation with proper validation
and default value handling.
"""

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler


class WagonFactoryService:  # pylint: disable=too-few-public-methods
    """Factory service for creating wagon entities.

    Encapsulates wagon creation logic and provides consistent
    entity instantiation with proper validation.

    Note: Single-purpose domain service with focused responsibility.
    """

    def create_wagon(
        self,
        wagon_id: str,
        length: float,
        coupler_a: Coupler,
        coupler_b: Coupler,
    ) -> Wagon:
        """Create a wagon entity with validation.

        Args:
            wagon_id: Unique wagon identifier
            length: Wagon length in meters
            coupler_a: Coupler A configuration
            coupler_b: Coupler B configuration

        Returns
        -------
            Validated wagon entity

        Raises
        ------
            ValueError: If parameters are invalid
        """
        if not wagon_id or not wagon_id.strip():
            raise ValueError('Wagon ID cannot be empty')

        if length <= 0:
            raise ValueError('Wagon length must be positive')

        return Wagon(
            id=wagon_id.strip(),
            length=length,
            coupler_a=coupler_a,
            coupler_b=coupler_b,
        )
