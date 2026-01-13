"""Track occupancy event handler for wagon movement synchronization."""

from typing import Any

from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
from shared.domain.events.wagon_movement_events import WagonMovedEvent


class TrackOccupancyEventHandler:
    """Handles wagon movement events to keep track occupancy synchronized."""

    def __init__(self, railway_context: Any) -> None:
        self.railway_context = railway_context

    def handle_wagon_moved(self, event: WagonMovedEvent) -> None:
        """Handle wagon moved event by updating track occupancy."""
        occupancy_repo = self.railway_context.get_occupancy_repository()

        # Remove from source track if specified
        if event.from_track:
            source_occupancy = occupancy_repo.get(event.from_track)
            if source_occupancy:
                try:
                    source_occupancy.remove_occupant(event.wagon_id, event.timestamp)
                except (ValueError, KeyError):
                    # Wagon not found in source track - ignore
                    pass

        # Add to destination track
        dest_track = self.railway_context.get_track(event.to_track)
        if dest_track:
            dest_occupancy = occupancy_repo.get_or_create(dest_track)

            # Find wagon to get its length
            wagon = self._find_wagon_by_id(event.wagon_id)
            if wagon:
                # Remove wagon from destination track first (in case it's already there)
                try:
                    dest_occupancy.remove_occupant(event.wagon_id, event.timestamp)
                except (ValueError, KeyError):
                    pass

                optimal_position = dest_occupancy.find_optimal_position(wagon.length)
                if optimal_position is not None:
                    occupant = TrackOccupant(
                        id=event.wagon_id,
                        type=OccupantType.WAGON,
                        length=wagon.length,
                        position_start=optimal_position,
                    )
                    dest_occupancy.add_occupant(occupant, event.timestamp)

    def _find_wagon_by_id(self, wagon_id: str) -> Any:
        """Find wagon by ID from yard context."""
        try:
            if hasattr(self.railway_context, '_infra') and self.railway_context._infra:
                yard_context = self.railway_context._infra.contexts.get('yard')
                if yard_context and hasattr(yard_context, 'all_wagons'):
                    for wagon in yard_context.all_wagons:
                        if wagon.id == wagon_id:
                            return wagon
        except Exception:
            pass
        return None
