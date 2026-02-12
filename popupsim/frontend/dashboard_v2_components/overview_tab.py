"""Overview tab - simulation results summary."""

from typing import Any

import streamlit as st


def render_overview_tab(data: dict[str, Any]) -> None:
    """Render overview tab with simulation results."""
    st.header('📊 Simulation Overview')

    metrics = data.get('metrics')

    if not metrics:
        st.warning('⚠️ No simulation metrics available')
        return

    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        trains = metrics.get('trains_arrived', 0)
        wagons = metrics.get('wagons_arrived', 0)
        st.metric('Trains / Wagons', f'{trains} / {wagons}')

    with col2:
        retrofitted = metrics.get('retrofits_completed', 0)
        rate = (retrofitted / wagons * 100) if wagons > 0 else 0
        st.metric('Retrofitted', f'{retrofitted} ({rate:.1f}%)')

    with col3:
        rejected = metrics.get('wagons_rejected', 0)
        st.metric('Rejected', rejected)

    with col4:
        workshop_util = metrics.get('workshop_utilization', 0)
        st.metric('Workshop Util.', f'{workshop_util:.1f}%')

    with col5:
        duration = metrics.get('simulation_duration_minutes', 0)
        st.metric('Duration', f'{duration:.0f} min')

    st.markdown('---')

    # Workshop Statistics
    st.subheader('🏭 Workshop Performance')

    workshop_stats = metrics.get('workshop_statistics', {})
    if workshop_stats:
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

    # Locomotive Statistics
    st.subheader('🚂 Locomotive Operations')

    loco_stats = metrics.get('locomotive_statistics', {})
    if loco_stats:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric('Allocations', loco_stats.get('allocations', 0))

        with col2:
            st.metric('Movements', loco_stats.get('movements', 0))

        with col3:
            st.metric('Total Operations', loco_stats.get('total_operations', 0))
