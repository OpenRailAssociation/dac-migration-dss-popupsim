"""Scenario configuration tab - visualizes input scenario configuration."""

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from dashboard_v2_components.scenario_analyzer import ScenarioAnalyzer


def render_scenario_tab(data: dict[str, Any]) -> None:  # pylint: disable=too-many-locals
    """Render scenario configuration tab.

    Note: Multiple local variables needed for comprehensive scenario analysis.
    """
    scenario_config = data.get('scenario_config', {})

    if not scenario_config:
        st.warning('⚠️ No scenario configuration found. Make sure scenario files are in output/scenario/')
        return

    analyzer = ScenarioAnalyzer(scenario_config)

    st.header('⚙️ Scenario Configuration')

    # Section 1: Overview
    _render_overview_section(analyzer)

    st.markdown('---')

    # Section 2: Infrastructure Layout
    _render_infrastructure_section(analyzer)

    st.markdown('---')

    # Section 3: Resource Capacity
    _render_capacity_section(analyzer)

    st.markdown('---')

    # Section 4: Train Schedule
    _render_schedule_section(analyzer)

    st.markdown('---')


def _render_overview_section(analyzer: ScenarioAnalyzer) -> None:
    """Render scenario overview cards."""
    st.subheader('📋 Scenario Overview')

    metrics = analyzer.get_overview_metrics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric('Scenario ID', metrics['scenario_id'])
        st.caption(f'Version: {metrics["version"]}')

    with col2:
        st.metric('Total Trains', metrics['total_trains'])
        st.metric('Total Wagons', metrics['total_wagons'])

    with col3:
        st.metric('Needs Retrofit', metrics['needs_retrofit'])
        st.metric('Loaded Wagons', metrics['loaded_wagons'])

    with col4:
        st.metric('Workflow Mode', metrics['workflow_mode'])

    # Strategy configuration
    with st.expander('🎯 Strategy Configuration'):
        strategies = analyzer.get_strategy_config()
        strategy_df = pd.DataFrame(list(strategies.items()), columns=['Strategy', 'Value'])
        st.dataframe(strategy_df, use_container_width=True, hide_index=True)


def _render_infrastructure_section(analyzer: ScenarioAnalyzer) -> None:  # pylint: disable=too-many-locals
    """Render infrastructure layout schematic.

    Note: Multiple local variables needed for infrastructure visualization.
    """
    st.subheader('🛤️ Infrastructure Layout')

    track_summary = analyzer.get_track_summary()

    # Track type colors
    colors = {
        'collection': '#e74c3c',
        'retrofit': '#f39c12',
        'workshop': '#27ae60',
        'retrofitted': '#9b59b6',
        'parking': '#34495e',
        'mainline': '#95a5a6',
        'rescource_parking': '#7f8c8d',
    }

    # Calculate total tracks and figure height
    total_tracks = sum(info['count'] for info in track_summary.values())
    fig_height = max(8, total_tracks * 0.4 + 2)

    # Create schematic diagram
    fig, ax = plt.subplots(figsize=(14, fig_height))
    ax.set_xlim(0, 10)
    ax.axis('off')

    # Track type order (top to bottom)
    track_order = ['mainline', 'collection', 'retrofit', 'workshop', 'retrofitted', 'parking', 'rescource_parking']

    # Draw tracks with proper spacing
    current_y = total_tracks * 0.5
    track_height = 0.3
    track_spacing = 0.1

    for track_type in track_order:
        if track_type not in track_summary:
            continue

        info = track_summary[track_type]
        color = colors.get(track_type, '#7f7f7f')
        tracks = info['tracks']

        # Draw type label
        type_label_y = current_y - (len(tracks) - 1) * (track_height + track_spacing) / 2
        ax.text(0.5, type_label_y, track_type.upper(), va='center', ha='right', fontweight='bold', fontsize=10)

        # Draw each track
        for track in tracks:
            track_id = track['id']
            length_m = track['length_m']

            # Track bar (scale width based on length)
            width = min(7, max(1, length_m / 100))
            ax.barh(
                current_y, width, height=track_height, left=1.5, color=color, alpha=0.8, edgecolor='black', linewidth=1
            )

            # Track label
            label = f'{track_id}: {length_m:.0f}m'
            ax.text(1.5 + width + 0.1, current_y, label, va='center', fontsize=8)

            current_y -= track_height + track_spacing

        # Add spacing between track types
        current_y -= 0.3

    # Set y-limits
    ax.set_ylim(-1, total_tracks * 0.5 + 1)

    ax.set_title('Yard Infrastructure Schematic', fontsize=14, fontweight='bold', pad=20)

    st.pyplot(fig)
    plt.close()

    # Interactive track details
    with st.expander('📊 Track Details'):
        for track_type, info in track_summary.items():
            st.markdown(f'**{track_type.upper()}**')
            st.write(
                f'Count: {info["count"]} | '
                f'Total Length: {info["total_length_m"]:.0f}m | '
                f'Total Capacity: {info["total_capacity_wagons"]} wagons'
            )

            track_df = pd.DataFrame(info['tracks'])
            if not track_df.empty:
                st.dataframe(track_df, use_container_width=True, hide_index=True)


def _render_capacity_section(analyzer: ScenarioAnalyzer) -> None:
    """Render resource capacity summary."""
    st.subheader('📦 Resource Capacity')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('**🏭 Workshops**')
        workshop_summary = analyzer.get_workshop_summary()

        st.metric('Total Workshops', workshop_summary['total_workshops'])
        st.metric('Total Retrofit Bays', workshop_summary['total_bays'])

        workshop_df = pd.DataFrame(workshop_summary['workshops'])
        if not workshop_df.empty:
            st.dataframe(workshop_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown('**🚂 Locomotives**')
        loco_summary = analyzer.get_locomotive_summary()

        st.metric('Total Locomotives', loco_summary['total_locomotives'])

        loco_df = pd.DataFrame(loco_summary['locomotives'])
        if not loco_df.empty:
            st.dataframe(loco_df, use_container_width=True, hide_index=True)

    # Process times
    with st.expander('⏱️ Process Times Configuration'):
        process_times = analyzer.get_process_times()
        if process_times:
            times_df = pd.DataFrame(list(process_times.items()), columns=['Operation', 'Duration (minutes)'])
            st.dataframe(times_df, use_container_width=True, hide_index=True)


def _render_schedule_section(analyzer: ScenarioAnalyzer) -> None:
    """Render train schedule timeline."""
    st.subheader('🚆 Train Schedule')

    train_arrivals = analyzer.get_train_arrival_timeline()

    if train_arrivals is None or train_arrivals.empty:
        st.info('No train schedule data available')
        return

    # Arrival histogram
    fig, ax = plt.subplots(figsize=(12, 4))

    # Create hourly bins
    train_arrivals['hour'] = train_arrivals['arrival_time'].dt.floor('H')
    hourly_wagons = train_arrivals.groupby('hour')['wagon_count'].sum()

    ax.bar(hourly_wagons.index, hourly_wagons.values, width=0.03, color='#3498db', alpha=0.7, edgecolor='black')
    ax.set_xlabel('Time', fontsize=11)
    ax.set_ylabel('Wagons Arriving', fontsize=11)
    ax.set_title('Wagon Arrival Rate Over Time', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)
    plt.close()

    # Train details table
    with st.expander('📋 Train Arrival Details'):
        display_df = train_arrivals.copy()
        display_df['arrival_time'] = display_df['arrival_time'].dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(display_df, use_container_width=True, hide_index=True)
