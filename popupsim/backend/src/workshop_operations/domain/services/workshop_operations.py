"""Workshop business logic - no simulation dependencies."""

from collections.abc import Callable

from configuration.domain.models.workshop import Workshop


class WorkshopDistributor:
    """Distributes wagons to workshops based on capacity."""

    @staticmethod
    def select_best_workshop(
        workshops: list[Workshop], get_available_capacity: Callable[[str], int], capacity_claims: dict[str, int]
    ) -> Workshop:
        """Select workshop with most available capacity."""
        return max(workshops, key=lambda w: get_available_capacity(w.track_id) - capacity_claims[w.track_id])

    @staticmethod
    def calculate_batch_size(available: int, remaining_count: int) -> int:
        """Calculate batch size based on available capacity."""
        return min(available, remaining_count)

    @staticmethod
    def is_workshop_ready(track_empty: bool, stations_empty: bool) -> bool:
        """Check if workshop is ready to receive wagons."""
        return track_empty and stations_empty
