"""Pure domain service for PopUp retrofit processing."""

from workshop_operations.domain.entities.wagon import CouplerType, Wagon, WagonStatus

from ..aggregates.popup_workshop import RetrofitResult


class PopUpRetrofitProcessor:  # pylint: disable=too-few-public-methods
    """Pure domain service for DAC installation logic."""

    def install_dac_coupler(self, wagon: Wagon) -> RetrofitResult:
        """Install DAC coupler on wagon - pure business logic."""
        # Validate wagon can be retrofitted
        if wagon.coupler_type == CouplerType.DAC:
            return RetrofitResult(success=False, duration=0.0, reason="Already has DAC")

        if not wagon.needs_retrofit:
            return RetrofitResult(
                success=False, duration=0.0, reason="No retrofit needed"
            )

        # Perform DAC installation
        wagon.coupler_type = CouplerType.DAC
        wagon.needs_retrofit = False
        wagon.status = WagonStatus.RETROFITTED

        return RetrofitResult(
            success=True, duration=15.0, reason="DAC installed successfully"
        )
