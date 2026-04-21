"""Registry for managing rakes across contexts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.domain.value_objects.rake_type import RakeType

if TYPE_CHECKING:
    from shared.domain.entities.rake import Rake


class RakeRegistry:
    """Central registry for tracking rakes across all contexts."""

    def __init__(self) -> None:
        self._rakes: dict[str, Rake] = {}
        self._rakes_by_type: dict[RakeType, list[str]] = {rake_type: [] for rake_type in RakeType}
        self._rakes_by_track: dict[str, list[str]] = {}

    def register_rake(self, rake: Rake) -> None:
        """Register a new rake in the registry."""
        self._rakes[rake.rake_id] = rake

        # Index by type
        if rake.rake_id not in self._rakes_by_type[rake.rake_type]:
            self._rakes_by_type[rake.rake_type].append(rake.rake_id)

        # Index by track
        track = rake.formation_track
        if track not in self._rakes_by_track:
            self._rakes_by_track[track] = []
        if rake.rake_id not in self._rakes_by_track[track]:
            self._rakes_by_track[track].append(rake.rake_id)

    def get_rake(self, rake_id: str) -> Rake | None:
        """Get rake by ID."""
        return self._rakes.get(rake_id)

    def get_rakes_by_type(self, rake_type: RakeType) -> list[Rake]:
        """Get all rakes of specified type."""
        rake_ids = self._rakes_by_type.get(rake_type, [])
        return [self._rakes[rake_id] for rake_id in rake_ids if rake_id in self._rakes]

    def get_rakes_by_track(self, track_id: str) -> list[Rake]:
        """Get all rakes on specified track."""
        rake_ids = self._rakes_by_track.get(track_id, [])
        return [self._rakes[rake_id] for rake_id in rake_ids if rake_id in self._rakes]

    def update_rake_track(self, rake_id: str, new_track: str) -> None:
        """Update rake track location."""
        rake = self._rakes.get(rake_id)
        if not rake:
            return

        # Remove from old track index
        old_track = rake.formation_track
        if old_track in self._rakes_by_track and rake_id in self._rakes_by_track[old_track]:
            self._rakes_by_track[old_track].remove(rake_id)

        # Add to new track index
        if new_track not in self._rakes_by_track:
            self._rakes_by_track[new_track] = []
        if rake_id not in self._rakes_by_track[new_track]:
            self._rakes_by_track[new_track].append(rake_id)

        # Update rake
        rake.formation_track = new_track

    def remove_rake(self, rake_id: str) -> None:
        """Remove rake from registry."""
        rake = self._rakes.get(rake_id)
        if not rake:
            return

        # Remove from all indexes
        self._rakes_by_type[rake.rake_type].remove(rake_id)

        track = rake.formation_track
        if track in self._rakes_by_track and rake_id in self._rakes_by_track[track]:
            self._rakes_by_track[track].remove(rake_id)

        # Remove from main registry
        del self._rakes[rake_id]

    def get_all_rakes(self) -> list[Rake]:
        """Get all registered rakes."""
        return list(self._rakes.values())
