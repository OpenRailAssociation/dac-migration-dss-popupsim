"""Wagon eligibility service for determining if wagons can be processed."""

from dataclasses import dataclass
from typing import Any


@dataclass
class EligibilityResult:
    """Result of wagon eligibility check."""

    is_eligible: bool
    rejection_reason: str | None = None
    rejection_description: str | None = None
    rejection_status: str | None = None


class WagonEligibilityService:
    """Domain service for determining wagon eligibility for retrofit processing."""

    def is_eligible_for_retrofit(self, wagon_config: dict[str, Any]) -> EligibilityResult:
        """Check if wagon is eligible for retrofit processing.

        Args:
            wagon_config: Wagon configuration dictionary

        Returns
        -------
            EligibilityResult with eligibility status and rejection details
        """
        is_loaded = wagon_config.get('is_loaded', False)
        needs_retrofit = wagon_config.get('needs_retrofit', True)

        if is_loaded:
            return EligibilityResult(
                is_eligible=False,
                rejection_reason='Loaded',
                rejection_description='Wagon is loaded',
                rejection_status='REJECTED_LOADED',
            )

        if not needs_retrofit:
            return EligibilityResult(
                is_eligible=False,
                rejection_reason='No Retrofit Needed',
                rejection_description="Wagon doesn't need retrofit",
                rejection_status='REJECTED_NO_RETROFIT_NEEDED',
            )

        return EligibilityResult(is_eligible=True)
