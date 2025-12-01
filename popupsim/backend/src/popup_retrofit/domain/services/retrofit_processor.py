"""Retrofit processor service for DAC installation workflow."""
# pylint: disable=too-few-public-methods

from typing import Protocol

from workshop_operations.domain.entities.wagon import Wagon

from ..aggregates.popup_workshop import PopUpWorkshop
from ..aggregates.popup_workshop import RetrofitResult


class RetrofitProcessor(Protocol):  # pylint: disable=too-few-public-methods
    """Service for processing DAC retrofits."""

    def process_retrofit(self, workshop: PopUpWorkshop, wagon: Wagon) -> RetrofitResult:
        """Process DAC retrofit for a wagon.

        Args:
            workshop: PopUp workshop to perform retrofit
            wagon: Wagon to retrofit

        Returns
        -------
            Result of retrofit operation
        """
