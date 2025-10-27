"""
Module defining the Workshop model and its validation logic.

Key Features:
- **Workshop Configuration**: Defines the structure of the workshop, including tracks and their properties.
- **Validation Logic**: Ensures that the workshop configuration adheres to business rules, such as:
  - Unique track IDs.
  - Presence of required track functions.
  - Proper retrofit time constraints for specific track functions.
  - Balanced feeder and exit tracks.
  - Adequate workshop capacity for train arrivals.
"""

import logging
from typing import List

from pydantic import BaseModel, Field, field_validator

from .model_track import TrackFunction, WorkshopTrack

# Configure logging
logger = logging.getLogger(__name__)


class Workshop(BaseModel):
    """
    Model representing the workshop configuration.

    Contains all available tracks for train processing.
    """

    tracks: List[WorkshopTrack] = Field(min_length=1, description='List of available tracks in the workshop')

    @field_validator('tracks')
    @classmethod
    def validate_unique_track_ids(cls, v: List[WorkshopTrack]) -> List[WorkshopTrack]:
        """Ensure all track IDs are unique."""
        track_ids = [track.id for track in v]
        if len(track_ids) != len(set(track_ids)):
            duplicates = [id for id in track_ids if track_ids.count(id) > 1]
            raise ValueError(f'Duplicate track IDs found: {list(set(duplicates))}')
        return v

    @field_validator('tracks')
    @classmethod
    def validate_track_functions(cls, v: List[WorkshopTrack]) -> List[WorkshopTrack]:
        """Validate track functions for workshop operation requirements."""
        # Get all functions present in the workshop
        functions_present = {track.function for track in v}

        # Required functions for basic workshop operation
        required_functions = {TrackFunction.WERKSTATTGLEIS}

        # Check for required functions
        missing_required = required_functions - functions_present
        if missing_required:
            missing_names = [f.value for f in missing_required]
            raise ValueError(f'Workshop must have at least one track with required functions: {missing_names}')

        # Business rule: Verify werkstattgleis tracks have proper retrofit times
        werkstatt_tracks = [track for track in v if track.function == TrackFunction.WERKSTATTGLEIS]
        for track in werkstatt_tracks:
            if track.retrofit_time_min <= 0:
                raise ValueError(f'Werkstattgleis track {track.id} must have retrofit_time_min > 0')

        # Business rule: Non-werkstattgleis tracks should have retrofit_time_min = 0
        non_werkstatt_tracks = [track for track in v if track.function != TrackFunction.WERKSTATTGLEIS]
        for track in non_werkstatt_tracks:
            if track.retrofit_time_min != 0:
                raise ValueError(
                    f'Non-werkstattgleis track {track.id} ({track.function.value}) must have retrofit_time_min = 0'
                )

        return v

    @field_validator('tracks')
    @classmethod
    def validate_workshop_capacity(cls, v: List[WorkshopTrack]) -> List[WorkshopTrack]:
        """Validate workshop capacity and configuration."""
        # Calculate total capacity by function
        function_capacities = {}
        for track in v:
            if track.function not in function_capacities:
                function_capacities[track.function] = 0
            function_capacities[track.function] += track.capacity

        # Warning: Low werkstattgleis capacity
        werkstatt_capacity = function_capacities.get(TrackFunction.WERKSTATTGLEIS, 0)
        if werkstatt_capacity < 3:
            logger.warning(
                'Low werkstattgleis capacity: %s. Consider adding more retrofit capacity.', werkstatt_capacity
            )

        # Business rule: If feeder/exit tracks exist, they should be balanced
        zufuehrung_capacity = function_capacities.get(TrackFunction.WERKSTATTZUFUEHRUNG, 0)
        abfuehrung_capacity = function_capacities.get(TrackFunction.WERKSTATTABFUEHRUNG, 0)

        if zufuehrung_capacity > 0 and abfuehrung_capacity == 0:
            raise ValueError('Workshop has werkstattzufuehrung tracks but no werkstattabfuehrung tracks')
        if abfuehrung_capacity > 0 and zufuehrung_capacity == 0:
            raise ValueError('Workshop has werkstattabfuehrung tracks but no werkstattzufuehrung tracks')

        return v

    def get_werkstatt_throughput_info(self) -> dict:
        """
        Calculate and return werkstatt throughput information.

        Returns dictionary with capacity metrics for external validation use.
        """
        werkstatt_tracks = [track for track in self.tracks if track.function == TrackFunction.WERKSTATTGLEIS]

        if not werkstatt_tracks:
            return {'error': 'No werkstattgleis tracks found'}

        total_capacity = sum(t.capacity for t in werkstatt_tracks)
        avg_retrofit_time = sum(t.retrofit_time_min for t in werkstatt_tracks) / len(werkstatt_tracks)
        max_throughput_per_day = (24 * 60 / avg_retrofit_time) * total_capacity

        return {
            'total_capacity': total_capacity,
            'avg_retrofit_time_min': avg_retrofit_time,
            'max_throughput_per_day': max_throughput_per_day,
            'werkstatt_track_count': len(werkstatt_tracks),
        }

    def validate_capacity_utilization(self, wagons_needing_retrofit_per_day: int) -> List[str]:
        """
        Validate capacity utilization against expected workload.

        Returns list of validation messages (warnings/errors).
        """
        throughput_info = self.get_werkstatt_throughput_info()

        if 'error' in throughput_info:
            return [throughput_info['error']]

        max_throughput = throughput_info['max_throughput_per_day']
        utilization = wagons_needing_retrofit_per_day / max_throughput

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
