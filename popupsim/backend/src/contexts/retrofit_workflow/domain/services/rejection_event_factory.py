"""Rejection event factory for creating wagon rejection events."""

from typing import Any

from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.services.wagon_eligibility_service import EligibilityResult


class RejectionEventFactory:  # pylint: disable=too-few-public-methods
    """Factory for creating wagon rejection events.

    Note: Single-purpose domain service with focused responsibility.
    """

    def create_rejection_event(
        self,
        wagon_config: dict[str, Any],
        eligibility_result: EligibilityResult,
        train_id: str,
        arrival_time: float,
    ) -> WagonJourneyEvent:
        """Create a rejection event for an ineligible wagon.

        Args:
            wagon_config: Wagon configuration
            eligibility_result: Result from eligibility check
            train_id: Train identifier
            arrival_time: Arrival time

        Returns
        -------
            WagonJourneyEvent for the rejection
        """
        return WagonJourneyEvent(
            timestamp=arrival_time,
            wagon_id=wagon_config['id'],
            event_type='REJECTED',
            location='collection',
            status=eligibility_result.rejection_status or 'REJECTED_UNKNOWN',
            train_id=train_id,
            rejection_reason=eligibility_result.rejection_reason or 'Unknown',
            rejection_description=eligibility_result.rejection_description or 'Unknown rejection reason',
        )
