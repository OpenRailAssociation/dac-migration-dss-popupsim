"""Overview tab - simulation results summary."""

from typing import Any

import streamlit as st


def _render_kpi_cards(metrics: dict) -> None:
    """Render KPI cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        trains = metrics.get('trains_arrived', 0)
        wagons = metrics.get('wagons_arrived', 0)
        st.metric('Trains / Wagons', f'{trains} / {wagons}')

    with col2:
        rejected = metrics.get('wagons_rejected', 0)
        st.metric('Rejected', rejected)

    with col3:
        wagons = metrics.get('wagons_arrived', 0)
        rejected = metrics.get('wagons_rejected', 0)
        in_simulation = wagons - rejected
        st.metric('In Simulation', in_simulation)

    with col4:
        retrofitted = metrics.get('retrofits_completed', 0)
        st.metric('Retrofitted', retrofitted)


def _render_workshop_stats(workshop_stats: dict) -> None:
    """Render workshop statistics."""
    col1, col2 = st.columns(2)

    with col1:
        st.metric('Total Workshops', workshop_stats.get('total_workshops', 0))
        st.metric('Total Wagons Processed', workshop_stats.get('total_wagons_processed', 0))

    with col2:
        workshops = workshop_stats.get('workshops', {})
        if workshops:
            st.markdown('**Per-Workshop Breakdown:**')
            for ws_id, ws_data in workshops.items():
                st.write(f'- {ws_id}: {ws_data.get("wagons_processed", 0)} wagons')


def _render_loco_summary_metrics(loco_stats: dict) -> None:
    """Render locomotive summary metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric('Total Operations', loco_stats['total_operations'])
        st.metric('Coupling Operations', loco_stats['coupling_count'])

    with col2:
        st.metric('Movements', loco_stats['movement_count'])
        st.metric('Decoupling Operations', loco_stats['decoupling_count'])

    with col3:
        st.metric('Total Coupling Time', f'{loco_stats["total_coupling_time"]:.1f} min')
        st.metric('Total Decoupling Time', f'{loco_stats["total_decoupling_time"]:.1f} min')

    with col4:
        st.metric('Brake Tests', loco_stats['brake_test_count'])
        st.metric('Inspections', loco_stats['inspection_count'])


def _render_loco_time_breakdown(loco_stats: dict) -> None:
    """Render locomotive time breakdown."""
    col1, col2 = st.columns(2)

    with col1:
        st.write('🔗 **Coupling:**')
        st.write(f'  - SCREW: {loco_stats["screw_coupling_time"]:.1f} min ({loco_stats["screw_coupling_count"]} ops)')
        st.write(f'  - DAC: {loco_stats["dac_coupling_time"]:.1f} min ({loco_stats["dac_coupling_count"]} ops)')
        st.write('')
        st.write('🔓 **Decoupling:**')
        st.write(
            f'  - SCREW: {loco_stats["screw_decoupling_time"]:.1f} min ({loco_stats["screw_decoupling_count"]} ops)'
        )
        st.write(f'  - DAC: {loco_stats["dac_decoupling_time"]:.1f} min ({loco_stats["dac_decoupling_count"]} ops)')

    with col2:
        st.write('🚦 **Train Preparation:**')
        st.write(
            f'  - Shunting Prep: {loco_stats["shunting_prep_time"]:.1f} min ({loco_stats["shunting_prep_count"]} ops)'
        )
        st.write(f'  - Brake Tests: {loco_stats["brake_test_time"]:.1f} min ({loco_stats["brake_test_count"]} ops)')
        st.write(f'  - Inspections: {loco_stats["inspection_time"]:.1f} min ({loco_stats["inspection_count"]} ops)')
        st.write('')
        st.write('🚆 **Movement:**')
        st.write(f'  - Total Moving Time: {loco_stats["total_moving_time"]:.1f} min')


def render_overview_tab(data: dict[str, Any]) -> None:
    """Render overview tab with simulation results."""
    st.header('📊 Simulation Overview')

    metrics = data.get('metrics')

    if not metrics:
        st.warning('⚠️ No simulation metrics available')
        return

    # KPI Cards
    _render_kpi_cards(metrics)

    st.markdown('---')

    # Workshop Statistics
    st.subheader('🏭 Workshop Performance')

    workshop_stats = metrics.get('workshop_statistics', {})
    if workshop_stats:
        _render_workshop_stats(workshop_stats)

    # Locomotive Statistics
    st.subheader('🚂 Locomotive Operations Summary')

    loco_journey = data.get('locomotive_journey')
    if loco_journey is not None and not loco_journey.empty:
        # Calculate locomotive statistics from journey data
        loco_stats = _calculate_loco_stats(loco_journey)

        # Display summary metrics
        _render_loco_summary_metrics(loco_stats)

        # Detailed breakdown
        st.markdown('---')
        st.markdown('**Time Breakdown by Activity:**')

        _render_loco_time_breakdown(loco_stats)
    else:
        loco_stats = metrics.get('locomotive_statistics', {})
        if loco_stats:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric('Allocations', loco_stats.get('allocations', 0))

            with col2:
                st.metric('Movements', loco_stats.get('movements', 0))

            with col3:
                st.metric('Total Operations', loco_stats.get('total_operations', 0))


def _update_coupling_stats(stats: dict, duration: float, coupler_type: str) -> None:
    """Update coupling statistics."""
    stats['coupling_count'] += 1
    stats['total_coupling_time'] += duration
    if coupler_type == 'SCREW':
        stats['screw_coupling_time'] += duration
        stats['screw_coupling_count'] += 1
    elif coupler_type == 'DAC':
        stats['dac_coupling_time'] += duration
        stats['dac_coupling_count'] += 1


def _update_decoupling_stats(stats: dict, duration: float, coupler_type: str) -> None:
    """Update decoupling statistics."""
    stats['decoupling_count'] += 1
    stats['total_decoupling_time'] += duration
    if coupler_type == 'SCREW':
        stats['screw_decoupling_time'] += duration
        stats['screw_decoupling_count'] += 1
    elif coupler_type == 'DAC':
        stats['dac_decoupling_time'] += duration
        stats['dac_decoupling_count'] += 1


def _calculate_loco_stats(loco_journey: Any) -> dict[str, Any]:
    """Calculate locomotive statistics from journey data."""
    stats = {
        'total_operations': len(loco_journey),
        'movement_count': 0,
        'coupling_count': 0,
        'decoupling_count': 0,
        'brake_test_count': 0,
        'inspection_count': 0,
        'shunting_prep_count': 0,
        'total_coupling_time': 0.0,
        'total_decoupling_time': 0.0,
        'screw_coupling_time': 0.0,
        'screw_coupling_count': 0,
        'dac_coupling_time': 0.0,
        'dac_coupling_count': 0,
        'screw_decoupling_time': 0.0,
        'screw_decoupling_count': 0,
        'dac_decoupling_time': 0.0,
        'dac_decoupling_count': 0,
        'brake_test_time': 0.0,
        'inspection_time': 0.0,
        'shunting_prep_time': 0.0,
        'total_moving_time': 0.0,
    }

    for _, row in loco_journey.iterrows():
        event_type = row.get('event_type', '')
        duration = row.get('duration_min', 0.0) or 0.0
        coupler_type = row.get('coupler_type', '')

        if event_type == 'MOVING':
            stats['movement_count'] += 1
            stats['total_moving_time'] += duration
        elif event_type == 'COUPLING_STARTED':
            _update_coupling_stats(stats, duration, coupler_type)
        elif event_type == 'DECOUPLING_STARTED':
            _update_decoupling_stats(stats, duration, coupler_type)
        elif event_type == 'BRAKE_TEST':
            stats['brake_test_count'] += 1
            stats['brake_test_time'] += duration
        elif event_type == 'INSPECTION':
            stats['inspection_count'] += 1
            stats['inspection_time'] += duration
        elif event_type == 'SHUNTING_PREP':
            stats['shunting_prep_count'] += 1
            stats['shunting_prep_time'] += duration

    return stats
