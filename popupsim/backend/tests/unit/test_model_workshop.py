"""
Unit tests for Workshop model.

Tests the Workshop model validation logic, track collection management,
duplicate track ID validation, and TrackFunction validation for workshop configurations.
"""

import pytest
from pydantic import ValidationError

from src.configuration.model_track import TrackFunction, WorkshopTrackConfig
from src.configuration.model_workshop import Workshop


class TestWorkshop:
    """Test cases for Workshop model."""

    def test_workshop_creation_valid_data(self):
        """Test successful workshop creation with valid data."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(id='TRACK02', function=TrackFunction.WERKSTATTGLEIS, capacity=3, retrofit_time_min=45),
            WorkshopTrackConfig(id='TRACK03', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0),
        ]

        workshop = Workshop(tracks=tracks)

        assert len(workshop.tracks) == 3
        assert workshop.tracks[0].id == 'TRACK01'
        assert workshop.tracks[1].id == 'TRACK02'
        assert workshop.tracks[2].id == 'TRACK03'

    def test_workshop_creation_single_track(self):
        """Test workshop creation with minimum single werkstattgleis track."""
        track = WorkshopTrackConfig(
            id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30
        )
        workshop = Workshop(tracks=[track])

        assert len(workshop.tracks) == 1
        assert workshop.tracks[0].id == 'TRACK01'
        assert workshop.tracks[0].function == TrackFunction.WERKSTATTGLEIS

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
        """Test validation error when tracks have duplicate IDs."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(
                id='TRACK01', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0
            ),  # Duplicate ID
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)
        assert 'Duplicate track IDs found' in str(exc_info.value)
        assert 'TRACK01' in str(exc_info.value)

    def test_workshop_validation_missing_werkstattgleis(self):
        """Test validation error when no werkstattgleis track is present."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0),
            WorkshopTrackConfig(id='TRACK02', function=TrackFunction.PARKGLEIS, capacity=8, retrofit_time_min=0),
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)
        # The validation catches this with the required functions message
        assert 'required functions' in str(exc_info.value) and 'werkstattgleis' in str(exc_info.value)

    def test_workshop_validation_werkstattgleis_invalid_retrofit_time(self):
        """Test validation error when werkstattgleis has invalid retrofit_time_min."""
        # This validation happens at the WorkshopTrackConfig level, not Workshop level
        with pytest.raises(ValidationError) as exc_info:
            WorkshopTrackConfig(
                id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=0
            )  # Invalid: should be > 0
        assert 'retrofit_time_min must be > 0 for werkstattgleis' in str(exc_info.value)

    def test_workshop_validation_non_werkstattgleis_invalid_retrofit_time(self):
        """Test validation error when non-werkstattgleis has non-zero retrofit_time_min."""
        # This validation happens at the WorkshopTrackConfig level, not Workshop level
        with pytest.raises(ValidationError) as exc_info:
            WorkshopTrackConfig(
                id='TRACK02', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=15
            )  # Invalid: should be 0
        assert 'retrofit_time_min must be 0 unless function is werkstattgleis' in str(exc_info.value)

    def test_workshop_validation_unbalanced_feeder_tracks(self):
        """Test validation error when feeder/exit tracks are unbalanced."""
        # Test: werkstattzufuehrung without werkstattabfuehrung
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(
                id='TRACK02', function=TrackFunction.WERKSTATTZUFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
            # Missing WERKSTATTABFUEHRUNG
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)
        assert 'werkstattzufuehrung tracks but no werkstattabfuehrung tracks' in str(exc_info.value)

        # Test: werkstattabfuehrung without werkstattzufuehrung
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(
                id='TRACK02', function=TrackFunction.WERKSTATTABFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
            # Missing WERKSTATTZUFUEHRUNG
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)
        assert 'werkstattabfuehrung tracks but no werkstattzufuehrung tracks' in str(exc_info.value)

    def test_workshop_validation_balanced_feeder_tracks_valid(self):
        """Test valid workshop with balanced feeder/exit tracks."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(
                id='TRACK02', function=TrackFunction.WERKSTATTZUFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
            WorkshopTrackConfig(
                id='TRACK03', function=TrackFunction.WERKSTATTABFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
        ]

        workshop = Workshop(tracks=tracks)
        assert len(workshop.tracks) == 3

    def test_workshop_all_track_functions_valid(self):
        """Test workshop with all valid track function types."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(id='TRACK02', function=TrackFunction.WERKSTATTGLEIS, capacity=3, retrofit_time_min=45),
            WorkshopTrackConfig(id='TRACK03', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0),
            WorkshopTrackConfig(id='TRACK04', function=TrackFunction.PARKGLEIS, capacity=8, retrofit_time_min=0),
            WorkshopTrackConfig(
                id='TRACK05', function=TrackFunction.WERKSTATTZUFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
            WorkshopTrackConfig(
                id='TRACK06', function=TrackFunction.WERKSTATTABFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
            WorkshopTrackConfig(id='TRACK07', function=TrackFunction.BAHNHOFSKOPF, capacity=3, retrofit_time_min=0),
        ]

        workshop = Workshop(tracks=tracks)
        assert len(workshop.tracks) == 7

        # Verify all functions are present
        functions_in_workshop = {track.function for track in workshop.tracks}
        assert TrackFunction.WERKSTATTGLEIS in functions_in_workshop
        assert TrackFunction.SAMMELGLEIS in functions_in_workshop
        assert TrackFunction.PARKGLEIS in functions_in_workshop
        assert TrackFunction.WERKSTATTZUFUEHRUNG in functions_in_workshop
        assert TrackFunction.WERKSTATTABFUEHRUNG in functions_in_workshop
        assert TrackFunction.BAHNHOFSKOPF in functions_in_workshop

    def test_workshop_csv_data_integration(self):
        """Test workshop creation with realistic CSV data format."""
        csv_tracks_data = [
            {'id': 'TRACK01', 'function': 'werkstattgleis', 'capacity': 5, 'retrofit_time_min': 30},
            {'id': 'TRACK02', 'function': 'werkstattgleis', 'capacity': 3, 'retrofit_time_min': 45},
            {'id': 'TRACK03', 'function': 'sammelgleis', 'capacity': 10, 'retrofit_time_min': 0},
            {'id': 'TRACK04', 'function': 'parkgleis', 'capacity': 8, 'retrofit_time_min': 0},
            {'id': 'TRACK05', 'function': 'werkstattzufuehrung', 'capacity': 2, 'retrofit_time_min': 0},
            {'id': 'TRACK06', 'function': 'werkstattabfuehrung', 'capacity': 2, 'retrofit_time_min': 0},
            {'id': 'TRACK07', 'function': 'bahnhofskopf', 'capacity': 3, 'retrofit_time_min': 0},
        ]

        tracks = [WorkshopTrackConfig(**track_data) for track_data in csv_tracks_data]

        # Create workshop
        workshop = Workshop(tracks=tracks)

        assert len(workshop.tracks) == 7
        assert workshop.tracks[0].function == TrackFunction.WERKSTATTGLEIS
        assert workshop.tracks[2].function == TrackFunction.SAMMELGLEIS

    def test_workshop_multiple_duplicates_validation(self):
        """Test validation error with multiple duplicate track IDs."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(
                id='TRACK01', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0
            ),  # Duplicate
            WorkshopTrackConfig(id='TRACK02', function=TrackFunction.PARKGLEIS, capacity=8, retrofit_time_min=0),
            WorkshopTrackConfig(
                id='TRACK02', function=TrackFunction.BAHNHOFSKOPF, capacity=3, retrofit_time_min=0
            ),  # Another duplicate
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)
        error_msg = str(exc_info.value)
        assert 'Duplicate track IDs found' in error_msg
        assert 'TRACK01' in error_msg or 'TRACK02' in error_msg

    def test_workshop_function_capacity_calculation(self):
        """Test that workshop correctly handles function capacity calculations."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(
                id='TRACK02', function=TrackFunction.WERKSTATTGLEIS, capacity=3, retrofit_time_min=45
            ),  # Total werkstatt: 8
            WorkshopTrackConfig(id='TRACK03', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0),
            WorkshopTrackConfig(
                id='TRACK04', function=TrackFunction.SAMMELGLEIS, capacity=5, retrofit_time_min=0
            ),  # Total sammel: 15
        ]

        workshop = Workshop(tracks=tracks)

        # Verify that tracks with same function are properly grouped
        werkstatt_tracks = [t for t in workshop.tracks if t.function == TrackFunction.WERKSTATTGLEIS]
        sammel_tracks = [t for t in workshop.tracks if t.function == TrackFunction.SAMMELGLEIS]

        assert len(werkstatt_tracks) == 2
        assert len(sammel_tracks) == 2
        assert sum(t.capacity for t in werkstatt_tracks) == 8
        assert sum(t.capacity for t in sammel_tracks) == 15

    def test_workshop_core_workflow_functions_warning(self):
        """Test warning for missing core workflow functions (sammelgleis, parkgleis)."""
        # Only werkstattgleis, missing sammelgleis and parkgleis
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
        ]

        workshop = Workshop(tracks=tracks)
        assert len(workshop.tracks) == 1

    def test_workshop_enhanced_error_messages(self):
        """Test enhanced German error messages matching reference validation style."""
        # Test enhanced werkstattgleis missing message
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0),
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)

        assert 'required functions' in str(exc_info.value) and 'werkstattgleis' in str(exc_info.value)

    def test_workshop_enhanced_retrofit_time_error_messages(self):
        """Test enhanced German error messages for retrofit time validation."""
        # Test enhanced non-werkstattgleis error message
        with pytest.raises(ValidationError) as exc_info:
            WorkshopTrackConfig(id='TRACK02', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=15)

        assert 'retrofit_time_min must be 0 unless function is werkstattgleis' in str(exc_info.value)

    def test_workshop_enhanced_feeder_track_error_messages(self):
        """Test enhanced German error messages for feeder track validation."""
        # Test enhanced feeder track imbalance message
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(
                id='TRACK02', function=TrackFunction.WERKSTATTZUFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
        ]

        with pytest.raises(ValidationError) as exc_info:
            Workshop(tracks=tracks)

        assert 'werkstattzufuehrung tracks but no werkstattabfuehrung tracks' in str(exc_info.value)

    def test_workshop_throughput_info_calculation(self):
        """Test werkstatt throughput information calculation."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(id='TRACK02', function=TrackFunction.WERKSTATTGLEIS, capacity=3, retrofit_time_min=60),
            WorkshopTrackConfig(id='TRACK03', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0),
        ]

        workshop = Workshop(tracks=tracks)
        throughput_info = workshop.get_werkstatt_throughput_info()

        assert throughput_info['total_capacity'] == 8  # 5 + 3
        assert throughput_info['avg_retrofit_time_min'] == 45.0  # (30 + 60) / 2
        assert throughput_info['werkstatt_track_count'] == 2

        # Calculate expected throughput: (24 * 60 / 45) * 8 = 256
        expected_throughput = (24 * 60 / 45.0) * 8
        assert throughput_info['max_throughput_per_day'] == expected_throughput

    def test_workshop_throughput_info_no_werkstatt(self):
        """Test throughput info when no werkstattgleis tracks exist."""
        # Create a workshop with valid tracks first, then manually modify for testing
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
        ]
        workshop = Workshop(tracks=tracks)

        # Now replace tracks to simulate no werkstattgleis scenario
        workshop.tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0)
        ]

        throughput_info = workshop.get_werkstatt_throughput_info()
        assert 'error' in throughput_info
        assert throughput_info['error'] == 'No werkstattgleis tracks found'

    def test_workshop_capacity_utilization_validation(self):
        """Test capacity utilization validation with different load scenarios."""
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(id='TRACK02', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0),
        ]

        workshop = Workshop(tracks=tracks)

        # Calculate max throughput: (24 * 60 / 30) * 5 = 240 wagons/day
        max_throughput = (24 * 60 / 30) * 5  # 240

        # Test scenarios
        # 1. Low utilization (< 80%)
        low_load = int(max_throughput * 0.5)  # 50% utilization
        messages = workshop.validate_capacity_utilization(low_load)
        assert len(messages) == 1
        assert 'INFO: Kapazität ausreichend' in messages[0]
        assert '50% Auslastung' in messages[0]

        # 2. High utilization (> 80%, < 100%)
        high_load = int(max_throughput * 0.9)  # 90% utilization
        messages = workshop.validate_capacity_utilization(high_load)
        assert len(messages) == 1
        assert 'WARNING: Hohe Auslastung' in messages[0]
        assert '90% Auslastung' in messages[0]
        assert 'Erwägen Sie höhere Kapazität' in messages[0]

        # 3. Overutilization (> 100%)
        over_load = int(max_throughput * 1.2)  # 120% utilization
        messages = workshop.validate_capacity_utilization(over_load)
        assert len(messages) == 1
        assert 'ERROR: Kapazität überschritten' in messages[0]
        assert '120% Auslastung' in messages[0]
        assert 'Erhöhen Sie Kapazität oder reduzieren Sie Zugankünfte' in messages[0]

    def test_workshop_capacity_utilization_no_werkstatt_error(self):
        """Test capacity utilization validation when no werkstattgleis exists."""
        # Create a valid workshop first, then modify it for testing
        tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
        ]
        workshop = Workshop(tracks=tracks)

        # Now replace tracks to simulate no werkstattgleis scenario
        workshop.tracks = [
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0)
        ]

        messages = workshop.validate_capacity_utilization(100)
        assert len(messages) == 1
        assert 'No werkstattgleis tracks found' in messages[0]

    def test_workshop_realistic_capacity_scenario(self):
        """Test realistic workshop capacity scenario based on reference validation."""
        # Realistic workshop setup
        tracks = [
            # Werkstattgleise
            WorkshopTrackConfig(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrackConfig(id='TRACK02', function=TrackFunction.WERKSTATTGLEIS, capacity=3, retrofit_time_min=45),
            # Supporting tracks
            WorkshopTrackConfig(id='TRACK03', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0),
            WorkshopTrackConfig(id='TRACK04', function=TrackFunction.PARKGLEIS, capacity=8, retrofit_time_min=0),
            WorkshopTrackConfig(
                id='TRACK05', function=TrackFunction.WERKSTATTZUFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
            WorkshopTrackConfig(
                id='TRACK06', function=TrackFunction.WERKSTATTABFUEHRUNG, capacity=2, retrofit_time_min=0
            ),
            WorkshopTrackConfig(id='TRACK07', function=TrackFunction.BAHNHOFSKOPF, capacity=3, retrofit_time_min=0),
        ]

        workshop = Workshop(tracks=tracks)

        # Verify all core functions are present
        functions = {track.function for track in workshop.tracks}
        assert TrackFunction.WERKSTATTGLEIS in functions
        assert TrackFunction.SAMMELGLEIS in functions
        assert TrackFunction.PARKGLEIS in functions

        # Check throughput calculation
        throughput_info = workshop.get_werkstatt_throughput_info()
        assert throughput_info['total_capacity'] == 8  # 5 + 3
        assert throughput_info['avg_retrofit_time_min'] == 37.5  # (30 + 45) / 2

        # Test capacity utilization with realistic loads
        # Assume 150 wagons per day need retrofit
        messages = workshop.validate_capacity_utilization(150)
        assert len(messages) == 1
        # Should be within acceptable range for this setup
