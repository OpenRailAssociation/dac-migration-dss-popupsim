"""Module defining the Workshop model and its validation logic.

Key Features:
- **Workshop Configuration**: Defines the structure of the workshop, including tracks and their properties.
- **Validation Logic**: Ensures that the workshop models adheres to business rules, such as:
  - Unique track IDs.
  - Presence of required track functions.
  - Proper retrofit time constraints for specific track functions.
  - Balanced feeder and exit tracks.
  - Adequate workshop capacity for train arrivals.
"""

import logging

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from .track import Track
from .track import TrackType

# Configure logging
logger = logging.getLogger(__name__)


class Workshop(BaseModel):
    """Model representing the workshop models.

    Contains all available tracks for train processing.
    """

    tracks: list[Track] = Field(min_length=1, description='List of available tracks in the workshop')

    @field_validator('tracks')
    @classmethod
    def validate_unique_track_ids(cls, v: list[Track]) -> list[Track]:
        """Ensure all track IDs are unique.

        Parameters
        ----------
        v : list[WorkshopTrack]
            List of workshop tracks to validate.

        Returns
        -------
        list[WorkshopTrack]
            Validated list of tracks.

        Raises
        ------
        ValueError
            If duplicate track IDs are found.
        """
        track_ids = [track.id for track in v]
        if len(track_ids) != len(set(track_ids)):
            duplicates = [track_id for track_id in track_ids if track_ids.count(track_id) > 1]
            raise ValueError(f'Duplicate track IDs found: {list(set(duplicates))}')
        return v

    def get_werkstatt_throughput_info(self) -> dict[str, int | float | str]:
        """Calculate and return werkstatt throughput information.

        Returns
        -------
        dict
            Dictionary with capacity metrics including total_capacity,
            avg_retrofit_time_min, max_throughput_per_day, and werkstatt_track_count.
            Returns error message if no WORKSHOP tracks found.
        """
        werkstatt_tracks = [track for track in self.tracks if track.type == TrackType.WORKSHOP]

        if not werkstatt_tracks:
            return {'error': 'No WORKSHOP tracks found'}

        # Safely aggregate capacities (t.capacity may be None)
        # Todo clarify capacity handling
        # capacities: list[int] = [t.capacity or 0 for t in werkstatt_tracks]
        # total_capacity: int = sum(capacities)

        # Collect retrofit times, ignoring tracks without a defined retrofit_time_min
        # retrofit_times: list[int] = [t.retrofit_time_min for t in werkstatt_tracks if t.retrofit_time_min is not None]
        # Todo clarify retrofit_time_min handling
        retrofit_times: list[int] = [30, 30]  # Placeholder values for

        if not retrofit_times:
            return {'error': 'No retrofit_time_min defined for WORKSHOP tracks'}

        total_capacity = 1
        avg_retrofit_time: float = sum(retrofit_times) / len(retrofit_times)
        max_throughput_per_day: float = (24 * 60 / avg_retrofit_time) * total_capacity

        return {
            'total_capacity': total_capacity,
            'avg_retrofit_time_min': avg_retrofit_time,
            'max_throughput_per_day': max_throughput_per_day,
            'werkstatt_track_count': len(werkstatt_tracks),
        }

    def validate_capacity_utilization(self, wagons_needing_retrofit_per_day: int) -> list[str]:
        """Validate capacity utilization against expected workload.

        Parameters
        ----------
        wagons_needing_retrofit_per_day : int
            Expected number of wagons requiring retrofit per day.

        Returns
        -------
        list[str]
            List of validation messages (INFO/WARNING/ERROR) about capacity utilization.
        """
        throughput_info = self.get_werkstatt_throughput_info()

        if 'error' in throughput_info:
            return [str(throughput_info['error'])]

        max_throughput = throughput_info['max_throughput_per_day']
        utilization = wagons_needing_retrofit_per_day / int(max_throughput)

        messages = []

        if utilization > 1.0:
            messages.append(
                f'ERROR: Kapazität überschritten: {wagons_needing_retrofit_per_day} Wagen/Tag '
                f'bei max. {max_throughput:.0f} Durchsatz ({utilization * 100:.0f}% Auslastung). '
                f'Erhöhen Sie Kapazität oder reduzieren Sie Zugankünfte'
            )
        elif utilization > 0.8:
            messages.append(
                f'WARNING: Hohe Auslastung: {wagons_needing_retrofit_per_day} Wagen/Tag '
                f'bei max. {max_throughput:.0f} Durchsatz ({utilization * 100:.0f}% Auslastung). '
                f'Erwägen Sie höhere Kapazität für bessere Performance'
            )
        else:
            messages.append(
                f'INFO: Kapazität ausreichend: {wagons_needing_retrofit_per_day} Wagen/Tag '
                f'bei max. {max_throughput:.0f} Durchsatz ({utilization * 100:.0f}% Auslastung)'
            )

        return messages
