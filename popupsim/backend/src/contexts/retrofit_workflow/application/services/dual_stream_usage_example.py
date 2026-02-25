"""Example usage of dual-stream event system.

This shows how to migrate from the mixed wagon_states.csv to clean separation.
"""

from contexts.retrofit_workflow.application.event_collector import EventCollector


def example_wagon_flow(event_collector: EventCollector, env_now: float) -> None:
    """Track wagon through retrofit process with dual-stream events (example)."""
    wagon_id = 'W0001'
    batch_id = 'BATCH_001'

    # 1. Wagon arrives - STATE + LOCATION change
    event_collector.record_state_change(
        timestamp=env_now, resource_id=wagon_id, resource_type='wagon', state='arrived', batch_id=batch_id
    )
    event_collector.record_location_change(
        timestamp=env_now, resource_id=wagon_id, resource_type='wagon', location='collection1'
    )

    # 2. Coupling starts - PROCESS event (no state/location change)
    event_collector.record_process_event(
        timestamp=env_now + 10,
        resource_id=wagon_id,
        resource_type='wagon',
        process_state='coupling_started',
        location='collection1',
        batch_id=batch_id,
    )

    # 3. Coupling completes - PROCESS event
    event_collector.record_process_event(
        timestamp=env_now + 12,
        resource_id=wagon_id,
        resource_type='wagon',
        process_state='coupling_completed',
        location='collection1',
        batch_id=batch_id,
    )

    # 4. Wagon queued for retrofit - STATE change (no location change)
    event_collector.record_state_change(
        timestamp=env_now + 20, resource_id=wagon_id, resource_type='wagon', state='queued', batch_id=batch_id
    )

    # 5. Wagon enters workshop - STATE + LOCATION change
    event_collector.record_state_change(
        timestamp=env_now + 30, resource_id=wagon_id, resource_type='wagon', state='in_workshop', batch_id=batch_id
    )
    event_collector.record_location_change(
        timestamp=env_now + 30,
        resource_id=wagon_id,
        resource_type='wagon',
        location='WS_01',
        previous_location='collection1',
    )

    # 6. Retrofit completes - STATE change (location stays same)
    event_collector.record_state_change(
        timestamp=env_now + 90, resource_id=wagon_id, resource_type='wagon', state='retrofitted', batch_id=batch_id
    )

    # 7. Wagon parked - STATE + LOCATION change
    event_collector.record_state_change(
        timestamp=env_now + 100, resource_id=wagon_id, resource_type='wagon', state='parked', batch_id=batch_id
    )
    event_collector.record_location_change(
        timestamp=env_now + 100,
        resource_id=wagon_id,
        resource_type='wagon',
        location='parking10',
        previous_location='WS_01',
    )


def example_locomotive_flow(event_collector: EventCollector, env_now: float) -> None:
    """Track locomotive with dual-stream events (example)."""
    loco_id = 'L001'

    # 1. Locomotive assigned - STATE change
    event_collector.record_state_change(
        timestamp=env_now, resource_id=loco_id, resource_type='locomotive', state='assigned'
    )

    # 2. Locomotive starts moving - STATE + LOCATION change
    event_collector.record_state_change(
        timestamp=env_now + 5, resource_id=loco_id, resource_type='locomotive', state='moving'
    )
    event_collector.record_location_change(
        timestamp=env_now + 5,
        resource_id=loco_id,
        resource_type='locomotive',
        location='collection1',
        previous_location='depot',
    )

    # 3. Locomotive arrives and becomes idle - STATE change (location stays)
    event_collector.record_state_change(
        timestamp=env_now + 15, resource_id=loco_id, resource_type='locomotive', state='idle'
    )


# Output files generated:
# - resource_states.csv: timestamp, resource_id, resource_type, state, train_id, batch_id,
#   rejection_reason
# - resource_locations.csv: timestamp, resource_id, resource_type, location, previous_location
# - resource_processes.csv: timestamp, resource_id, resource_type, process_state, location,
#   batch_id, rake_id, locomotive_id
