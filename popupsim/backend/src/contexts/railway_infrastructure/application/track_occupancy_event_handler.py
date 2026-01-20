"""Track occupancy event handler for wagon movement synchronization."""

import contextlib
from typing import Any

from shared.domain.events.wagon_movement_events import WagonMovedEvent


class TrackOccupancyEventHandler:  # pylint: disable=too-few-public-methods
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
                    source_occupancy.remove_wagon(event.wagon_id, event.timestamp)
                except (ValueError, KeyError) as e:
                    print(f'Warning: Could not remove wagon {event.wagon_id} from {event.from_track}: {e}')

        # Add to destination track
        dest_track = self.railway_context.get_track(event.to_track)
        if dest_track:
            dest_occupancy = occupancy_repo.get_or_create(dest_track)

            # Find wagon to get its length
            wagon = self._find_wagon_by_id(event.wagon_id)
            if wagon:
                # Remove wagon from destination track first (in case it's already there)
                with contextlib.suppress(ValueError, KeyError):
                    dest_occupancy.remove_wagon(event.wagon_id, event.timestamp)

                # Add wagon using enhanced occupancy
                try:
                    dest_occupancy.add_wagon(wagon, event.timestamp)
                except ValueError:
                    print(f'Warning: No space on {event.to_track} for wagon {event.wagon_id}')
            else:
                print(f'Warning: Could not find wagon {event.wagon_id} for movement to {event.to_track}')

    def _find_wagon_by_id(self, wagon_id: str) -> Any:
        """Find wagon by ID from yard context."""
        with contextlib.suppress(Exception):
            if self.railway_context._infra:  # pylint: disable=protected-access
                yard_context = self.railway_context._infra.contexts.get('yard')  # pylint: disable=protected-access
                if yard_context and hasattr(yard_context, 'all_wagons'):
                    for wagon in yard_context.all_wagons:
                        if wagon.id == wagon_id:
                            return wagon
        return None
