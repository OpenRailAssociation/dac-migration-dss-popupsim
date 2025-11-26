"""Unit tests for TrackListBuilder class.

Tests for loading tracks from JSON files and building track lists.
"""

from collections.abc import Generator
import json
from pathlib import Path
import tempfile

from builders.tracks_builder import TrackListBuilder
from models.track import Track
from models.track import TrackType
import pytest


@pytest.fixture
def temp_json_file() -> Generator[Path]:
    """Create a temporary JSON file.

    Yields
    ------
    Path
        Path to temporary JSON file.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def valid_tracks_json(temp_json_file: Path) -> Path:
    """Create a valid tracks JSON file.

    Parameters
    ----------
    temp_json_file : Path
        Temporary file path.

    Returns
    -------
    Path
        Path to JSON file with valid track data.
    """
    data = {
        'metadata': {'version': '1.0.0'},
        'tracks': [
            {
                'id': 'track_1',
                'type': 'mainline',
                'edges': ['edge_1', 'edge_2'],
            },
            {
                'id': 'track_2',
                'type': 'workshop_area',
                'edges': ['edge_3'],
            },
        ],
    }
    temp_json_file.write_text(json.dumps(data))
    return temp_json_file


@pytest.mark.unit
class TestTrackListBuilder:
    """Test suite for TrackListBuilder class."""

    def test_init_creates_empty_list(self, temp_json_file: Path) -> None:
        """Test that initialization creates empty track list.

        Parameters
        ----------
        temp_json_file : Path
            Temporary file path.
        """
        builder: TrackListBuilder = TrackListBuilder(temp_json_file)

        assert builder.tracks == []
        assert builder.tracks_path == temp_json_file

    def test_add_track(self, temp_json_file: Path) -> None:
        """Test adding track to builder.

        Parameters
        ----------
        temp_json_file : Path
            Temporary file path.
        """
        builder: TrackListBuilder = TrackListBuilder(temp_json_file)
        track: Track = Track(id='test_track', type=TrackType.MAINLINE, edges=['edge_1'])

        builder.add_track(track)

        assert len(builder.tracks) == 1
        assert builder.tracks[0] == track

    def test_load_tracks_from_valid_file(self, valid_tracks_json: Path) -> None:
        """Test loading tracks from valid JSON file.

        Parameters
        ----------
        valid_tracks_json : Path
            Path to valid tracks JSON file.
        """
        builder: TrackListBuilder = TrackListBuilder(valid_tracks_json)

        tracks: list[Track] = builder._load_tracks_from_file()

        assert len(tracks) == 2
        assert tracks[0].id == 'track_1'
        assert tracks[0].type == TrackType.MAINLINE
        assert tracks[0].edges == ['edge_1', 'edge_2']
        assert tracks[1].id == 'track_2'
        assert tracks[1].type == TrackType.WORKSHOP

    def test_load_tracks_nonexistent_file(self, temp_json_file: Path) -> None:
        """Test loading from nonexistent file raises error.

        Parameters
        ----------
        temp_json_file : Path
            Temporary file path.
        """
        nonexistent: Path = temp_json_file.parent / 'nonexistent.json'
        builder: TrackListBuilder = TrackListBuilder(nonexistent)

        with pytest.raises(FileNotFoundError, match='Tracks file not found'):
            builder._load_tracks_from_file()

    def test_load_tracks_invalid_json(self, temp_json_file: Path) -> None:
        """Test loading from file with invalid JSON syntax.

        Parameters
        ----------
        temp_json_file : Path
            Temporary file path.
        """
        temp_json_file.write_text('{ invalid json }')
        builder: TrackListBuilder = TrackListBuilder(temp_json_file)

        with pytest.raises(ValueError, match='Invalid JSON format'):
            builder._load_tracks_from_file()

    def test_load_tracks_missing_tracks_key(self, temp_json_file: Path) -> None:
        """Test loading from JSON without 'tracks' key.

        Parameters
        ----------
        temp_json_file : Path
            Temporary file path.
        """
        temp_json_file.write_text('{"metadata": {"version": "1.0"}}')
        builder: TrackListBuilder = TrackListBuilder(temp_json_file)

        with pytest.raises(ValueError, match='Missing "tracks" key'):
            builder._load_tracks_from_file()

    def test_load_tracks_invalid_track_data(self, temp_json_file: Path) -> None:
        """Test loading tracks with invalid track data.

        Parameters
        ----------
        temp_json_file : Path
            Temporary file path.
        """
        data = {
            'tracks': [
                {'id': 'invalid', 'type': 'mainline', 'edges': []},  # Empty edges
            ],
        }
        temp_json_file.write_text(json.dumps(data))
        builder: TrackListBuilder = TrackListBuilder(temp_json_file)

        with pytest.raises(ValueError):  # noqa: PT011
            builder._load_tracks_from_file()

    def test_build_loads_and_returns_tracks(self, valid_tracks_json: Path) -> None:
        """Test build method loads file and returns tracks.

        Parameters
        ----------
        valid_tracks_json : Path
            Path to valid tracks JSON file.
        """
        builder: TrackListBuilder = TrackListBuilder(valid_tracks_json)

        tracks: list[Track] = builder.build()

        assert len(tracks) == 2
        assert all(isinstance(track, Track) for track in tracks)
        assert builder.tracks == tracks

    def test_build_with_manually_added_tracks(self, valid_tracks_json: Path) -> None:
        """Test build method with manually added tracks.

        Parameters
        ----------
        valid_tracks_json : Path
            Path to valid tracks JSON file.
        """
        builder: TrackListBuilder = TrackListBuilder(valid_tracks_json)
        manual_track: Track = Track(id='manual', type=TrackType.PARKING, edges=['edge_m'])
        builder.add_track(manual_track)

        tracks: list[Track] = builder.build()

        # build() calls _load_tracks_from_file() which resets self.tracks
        assert len(tracks) == 3
        assert manual_track in tracks

    def test_multiple_tracks_different_types(self, temp_json_file: Path) -> None:
        """Test loading tracks with different types.

        Parameters
        ----------
        temp_json_file : Path
            Temporary file path.
        """
        data = {
            'tracks': [
                {'id': 't1', 'type': 'mainline', 'edges': ['e1']},
                {'id': 't2', 'type': 'workshop_area', 'edges': ['e2']},
                {'id': 't3', 'type': 'retrofit', 'edges': ['e3']},
                {'id': 't4', 'type': 'retrofitted', 'edges': ['e4']},
                {'id': 't5', 'type': 'parking_area', 'edges': ['e5']},
                {'id': 't6', 'type': 'loco_parking', 'edges': ['e6']},
            ],
        }
        temp_json_file.write_text(json.dumps(data))
        builder: TrackListBuilder = TrackListBuilder(temp_json_file)

        tracks: list[Track] = builder.build()

        assert len(tracks) == 6
        assert tracks[0].type == TrackType.MAINLINE
        assert tracks[1].type == TrackType.WORKSHOP
        assert tracks[2].type == TrackType.RETROFIT
        assert tracks[3].type == TrackType.RETROFITTED
        assert tracks[4].type == TrackType.PARKING
        assert tracks[5].type == TrackType.LOCOPARKING

    def test_load_tracks_from_fixture_path(self, fixtures_path: Path) -> None:
        """Test loading tracks from fixture file.

        Parameters
        ----------
        fixtures_path : Path
            Path to fixtures directory.

        Generic test loading the track.json file from the fixtures directory.
        """
        fixture_file: Path = fixtures_path / 'tracks.json'

        tracks: list[Track] = TrackListBuilder(fixture_file).build()

        assert len(tracks) == 7
        assert tracks[0].id == 'track_1'
        assert tracks[0].type == TrackType.MAINLINE
        assert tracks[0].edges[0] == 'edge_21'
