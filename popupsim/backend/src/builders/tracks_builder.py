"""Builder for creating Track instances from JSON configuration files.

This module provides the TrackListBuilder class that handles loading track
configurations from JSON files, validating them using the Track model, and
making them available to the simulation.

Classes
-------
TrackListBuilder
    Builder class for loading and managing Track instances from JSON files.

Examples
--------
>>> from pathlib import Path
>>> builder = TrackListBuilder(Path('tracks.json'))
>>> tracks = builder.build()
>>> len(tracks)
5
"""

import json
import logging
from pathlib import Path

from models.track import Track
from models.track import TrackType

logger = logging.getLogger(__name__)


class TrackListBuilder:
    """Builder class for creating lists of Track instances."""

    def __init__(self, tracks_path: Path) -> None:
        """Initialize an empty list to hold Track instances.

        Parameters
        ----------
        tracks_path : Path
            Path to the JSON file containing track data.
        """
        self.tracks_path: Path = tracks_path
        self.tracks: list[Track] = []

    def add_track(self, track: Track) -> None:
        """Add a Track instance to the list.

        Parameters
        ----------
        track : Track
            The Track instance to be added.
        """
        self.tracks.append(track)

    def _load_tracks_from_file(self) -> list[Track]:
        """Load Track instances from a JSON file.

        Returns
        -------
        list[Track]
            A list of Track instances loaded from the file.

        Raises
        ------
        FileNotFoundError
            If the tracks file does not exist.
        ValueError
            If the JSON file is invalid or missing required keys.
        """
        if not self.tracks_path.exists():
            raise FileNotFoundError(f'Tracks file not found: {self.tracks_path}')

        try:
            with self.tracks_path.open('r', encoding='utf-8') as f:
                data: dict[str, object] = json.load(f)

            if 'tracks' not in data:
                raise ValueError('Missing "tracks" key in JSON file')

            tracks_data: list[dict[str, object]] = data['tracks']  # type: ignore[assignment]
            for track_dict in tracks_data:
                if track_dict.get('type') in TrackType:
                    track: Track = Track(**track_dict)  # type: ignore[arg-type]
                    self.add_track(track)

            if len(self.tracks) == 0:
                logger.warning('No valid tracks found in %s', self.tracks_path)
            else:
                logger.info('Successfully loaded %d tracks from %s', len(self.tracks), self.tracks_path)
            return self.tracks

        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON format in {self.tracks_path}: {e!s}') from e

    def build(self) -> list[Track]:
        """Return the list of Track instances.

        Returns
        -------
        list[Track]
            The list of added Track instances.
        """
        self._load_tracks_from_file()
        return self.tracks
