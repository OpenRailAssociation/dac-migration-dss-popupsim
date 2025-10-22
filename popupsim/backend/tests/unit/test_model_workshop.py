"""
Unit tests for Workshop model.

Tests the Workshop model validation logic, track collection management,
and duplicate track ID validation for workshop configurations.
"""

import pytest
from pydantic import ValidationError

from src.configuration.model_track import Track
from src.configuration.model_workshop import Workshop


class TestWorkshop:
    """Test cases for Workshop model."""

    def test_workshop_creation_valid_data(self):
        """Test successful workshop creation with valid data."""
        tracks = [
            Track(id='TRACK01', capacity=5, retrofit_time_min=30),
            Track(id='TRACK02', capacity=3, retrofit_time_min=45),
            Track(id='TRACK03', capacity=4, retrofit_time_min=35),
        ]

        workshop = Workshop(tracks=tracks)

        assert len(workshop.tracks) == 3
        assert workshop.tracks[0].id == 'TRACK01'
        assert workshop.tracks[1].id == 'TRACK02'
        assert workshop.tracks[2].id == 'TRACK03'

    def test_workshop_creation_single_track(self):
        """Test workshop creation with minimum single track."""
        track = Track(id='TRACK01', capacity=5, retrofit_time_min=30)
        workshop = Workshop(tracks=[track])

        assert len(workshop.tracks) == 1
        assert workshop.tracks[0].id == 'TRACK01'

    def test_workshop_validation_empty_tracks_list(self):
        """Test validation error when tracks list is empty."""
        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=[])
        assert 'at least 1 item' in str(exc_info.value)

    def test_workshop_validation_missing_tracks(self):
        """Test validation error when tracks field is missing."""
        with pytest.raises(ValidationError) as exc_info:
            Workshop()
        assert 'Field required' in str(exc_info.value)

    def test_workshop_validation_duplicate_track_ids(self):
        """Test validation error when duplicate track IDs are provided."""
        tracks = [
            Track(id='TRACK01', capacity=5, retrofit_time_min=30),
            Track(id='TRACK02', capacity=3, retrofit_time_min=45),
            Track(id='TRACK01', capacity=4, retrofit_time_min=35),  # Duplicate ID
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)
        assert "Duplicate track IDs found: ['TRACK01']" in str(exc_info.value)

    def test_workshop_validation_multiple_duplicate_track_ids(self):
        """Test validation error with multiple sets of duplicate track IDs."""
        tracks = [
            Track(id='TRACK01', capacity=5, retrofit_time_min=30),
            Track(id='TRACK02', capacity=3, retrofit_time_min=45),
            Track(id='TRACK01', capacity=4, retrofit_time_min=35),  # Duplicate TRACK01
            Track(id='TRACK02', capacity=2, retrofit_time_min=40),  # Duplicate TRACK02
            Track(id='TRACK03', capacity=6, retrofit_time_min=50),
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)
        error_msg = str(exc_info.value)
        assert 'Duplicate track IDs found:' in error_msg
        assert 'TRACK01' in error_msg
        assert 'TRACK02' in error_msg

    def test_workshop_validation_track_id_case_sensitive(self):
        """Test that track ID validation is case sensitive."""
        tracks = [
            Track(id='TRACK01', capacity=5, retrofit_time_min=30),
            Track(id='track01', capacity=3, retrofit_time_min=45),  # Different case
            Track(id='Track01', capacity=4, retrofit_time_min=35),  # Different case
        ]

        # Should not raise validation error as IDs are case sensitive
        workshop = Workshop(tracks=tracks)
        assert len(workshop.tracks) == 3

    def test_workshop_validation_invalid_track_data(self):
        """Test validation error when track data is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            Workshop(
                tracks=[
                    {'id': '', 'capacity': -1, 'retrofit_time_min': 0}  # Invalid track data
                ]
            )
        error_msg = str(exc_info.value)
        # Should contain validation errors for the invalid track
        assert 'String should match pattern' in error_msg or 'greater than 0' in error_msg

    def test_workshop_tracks_property_access(self):
        """Test access to individual track properties."""
        tracks = [
            Track(id='TRACK01', capacity=5, retrofit_time_min=30),
            Track(id='TRACK02', capacity=10, retrofit_time_min=60),
        ]

        workshop = Workshop(tracks=tracks)

        # Test accessing track properties
        assert workshop.tracks[0].capacity == 5
        assert workshop.tracks[0].retrofit_time_min == 30
        assert workshop.tracks[1].capacity == 10
        assert workshop.tracks[1].retrofit_time_min == 60

    def test_workshop_dict_conversion(self):
        """Test workshop conversion to dictionary."""
        tracks = [
            Track(id='TRACK01', capacity=5, retrofit_time_min=30),
            Track(id='TRACK02', capacity=3, retrofit_time_min=45),
        ]

        workshop = Workshop(tracks=tracks)
        workshop_dict = workshop.model_dump()

        assert 'tracks' in workshop_dict
        assert len(workshop_dict['tracks']) == 2
        assert workshop_dict['tracks'][0]['id'] == 'TRACK01'
        assert workshop_dict['tracks'][1]['id'] == 'TRACK02'

    def test_workshop_json_serialization(self):
        """Test workshop JSON serialization."""
        tracks = [Track(id='TRACK01', capacity=5, retrofit_time_min=30)]

        workshop = Workshop(tracks=tracks)
        json_str = workshop.model_dump_json()

        # Should be valid JSON that can be parsed back
        import json

        parsed = json.loads(json_str)

        assert 'tracks' in parsed
        assert len(parsed['tracks']) == 1
        assert parsed['tracks'][0]['id'] == 'TRACK01'

    def test_workshop_from_dict(self):
        """Test workshop creation from dictionary."""
        workshop_data = {
            'tracks': [
                {'id': 'TRACK01', 'capacity': 5, 'retrofit_time_min': 30},
                {'id': 'TRACK02', 'capacity': 3, 'retrofit_time_min': 45},
            ]
        }

        workshop = Workshop(**workshop_data)

        assert len(workshop.tracks) == 2
        assert workshop.tracks[0].id == 'TRACK01'
        assert workshop.tracks[1].id == 'TRACK02'

    def test_workshop_equality(self):
        """Test workshop equality comparison."""
        tracks1 = [Track(id='TRACK01', capacity=5, retrofit_time_min=30)]
        tracks2 = [Track(id='TRACK01', capacity=5, retrofit_time_min=30)]
        tracks3 = [Track(id='TRACK02', capacity=5, retrofit_time_min=30)]

        workshop1 = Workshop(tracks=tracks1)
        workshop2 = Workshop(tracks=tracks2)
        workshop3 = Workshop(tracks=tracks3)

        assert workshop1 == workshop2
        assert workshop1 != workshop3

    def test_workshop_large_number_of_tracks(self):
        """Test workshop with a large number of tracks."""
        tracks = [
            Track(id=f'TRACK{i:02d}', capacity=5, retrofit_time_min=30)
            for i in range(1, 101)  # 100 tracks
        ]

        workshop = Workshop(tracks=tracks)

        assert len(workshop.tracks) == 100
        assert workshop.tracks[0].id == 'TRACK01'
        assert workshop.tracks[99].id == 'TRACK100'

    def test_workshop_track_modification_after_creation(self):
        """Test that tracks can be accessed after workshop creation."""
        tracks = [Track(id='TRACK01', capacity=5, retrofit_time_min=30)]
        workshop = Workshop(tracks=tracks)

        # Verify we can access track properties
        assert workshop.tracks[0].capacity == 5

        # The tracks should be the same objects
        assert workshop.tracks[0] is tracks[0]
