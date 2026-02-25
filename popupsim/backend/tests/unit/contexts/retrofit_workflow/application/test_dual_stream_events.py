"""Tests for dual-stream event system."""

from pathlib import Path
import tempfile

from contexts.retrofit_workflow.application.event_collector import EventCollector
import pandas as pd


def test_dual_stream_state_and_location_separation() -> None:
    """Test that state and location events are properly separated."""
    collector = EventCollector(start_datetime='2024-01-01T00:00:00')

    # Record state change
    collector.record_state_change(
        timestamp=100.0, resource_id='W001', resource_type='wagon', state='arrived', batch_id='BATCH_001'
    )

    # Record location change
    collector.record_location_change(timestamp=100.0, resource_id='W001', resource_type='wagon', location='collection1')

    # Verify events collected
    assert len(collector._dual_stream_collector.state_events) == 1
    assert len(collector._dual_stream_collector.location_events) == 1

    state_event = collector._dual_stream_collector.state_events[0]
    assert state_event.resource_id == 'W001'
    assert state_event.state.value == 'arrived'
    assert state_event.batch_id == 'BATCH_001'

    location_event = collector._dual_stream_collector.location_events[0]
    assert location_event.resource_id == 'W001'
    assert location_event.location == 'collection1'


def test_dual_stream_process_events() -> None:
    """Test process event recording."""
    collector = EventCollector()

    collector.record_process_event(
        timestamp=50.0,
        resource_id='W001',
        resource_type='wagon',
        process_state='coupling_started',
        location='collection1',
        batch_id='BATCH_001',
    )

    assert len(collector._dual_stream_collector.process_events) == 1
    event = collector._dual_stream_collector.process_events[0]
    assert event.process_state.value == 'coupling_started'
    assert event.location == 'collection1'


def test_dual_stream_csv_export() -> None:
    """Test CSV export of dual-stream events."""
    collector = EventCollector(start_datetime='2024-01-01T00:00:00')

    # Record various events
    collector.record_state_change(100.0, 'W001', 'wagon', 'arrived', batch_id='B1')
    collector.record_location_change(100.0, 'W001', 'wagon', 'collection1')
    collector.record_process_event(110.0, 'W001', 'wagon', 'coupling_started', 'collection1', batch_id='B1')

    # Export to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        collector.export_all(tmpdir)

        # Verify files exist
        assert Path(tmpdir, 'resource_states.csv').exists()
        assert Path(tmpdir, 'resource_locations.csv').exists()
        assert Path(tmpdir, 'resource_processes.csv').exists()

        # Verify content
        states_df = pd.read_csv(Path(tmpdir, 'resource_states.csv'))
        assert len(states_df) == 1
        assert states_df.iloc[0]['state'] == 'arrived'

        locations_df = pd.read_csv(Path(tmpdir, 'resource_locations.csv'))
        assert len(locations_df) == 1
        assert locations_df.iloc[0]['location'] == 'collection1'

        processes_df = pd.read_csv(Path(tmpdir, 'resource_processes.csv'))
        assert len(processes_df) == 1
        assert processes_df.iloc[0]['process_state'] == 'coupling_started'


def test_locomotive_dual_stream() -> None:
    """Test locomotive tracking with dual-stream."""
    collector = EventCollector()

    # Locomotive assigned
    collector.record_state_change(0.0, 'L001', 'locomotive', 'assigned')

    # Locomotive moving to location
    collector.record_state_change(5.0, 'L001', 'locomotive', 'moving')
    collector.record_location_change(5.0, 'L001', 'locomotive', 'collection1', 'depot')

    # Locomotive idle
    collector.record_state_change(15.0, 'L001', 'locomotive', 'idle')

    assert len(collector._dual_stream_collector.state_events) == 3
    assert len(collector._dual_stream_collector.location_events) == 1

    # Verify state progression
    states = [e.state.value for e in collector._dual_stream_collector.state_events]
    assert states == ['assigned', 'moving', 'idle']
