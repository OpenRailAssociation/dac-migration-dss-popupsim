"""Wagon flow tab - visualizes wagon journeys through the system."""

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


def render_wagon_flow_tab(data: dict[str, Any]) -> None:
    """Render wagon flow analysis tab."""
    st.header('🚃 Wagon Flow Analysis')

    wagon_journey = data.get('wagon_journey')
    metrics = data.get('metrics', {})

    if wagon_journey is None or wagon_journey.empty:
        st.warning('⚠️ No wagon journey data available')
        return

    # Section 1: Wagon Journeys Over Time
    st.subheader('Wagon Journeys Over Time')
    all_wagon_ids = sorted(wagon_journey['wagon_id'].unique())
    _render_wagon_gantt(wagon_journey, all_wagon_ids)

    st.markdown('---')

    # Section 2: Wagon Status Distribution
    st.subheader('Wagon Status Distribution (Final State)')
    _render_status_distribution(data)

    st.markdown('---')

    # Section 3: Journey Statistics
    st.subheader('Journey Statistics')
    _render_journey_statistics(wagon_journey)

    st.markdown('---')

    # Section 4: Wagon Journey History
    st.subheader('Wagon Journey History')
    _render_wagon_journey_history(wagon_journey)

    st.markdown('---')

    # Section 5: Track Specific Wagons
    st.subheader('Track Specific Wagons')
    st.write('Select specific wagons to analyze their journey in detail:')

    selected_wagons = st.multiselect(
        'Select wagons:', options=all_wagon_ids, default=[], placeholder='Choose wagon IDs to track...'
    )

    if selected_wagons:
        filtered_journey = wagon_journey[wagon_journey['wagon_id'].isin(selected_wagons)]
        _render_wagon_gantt(filtered_journey, sorted(selected_wagons))


def _render_wagon_gantt(journey_df, wagon_ids: list[str]) -> None:
    """Render Gantt chart showing individual wagon journeys."""
    # Wagon positions (inverted - first at top)
    wagon_positions = {wagon_id: len(wagon_ids) - 1 - i for i, wagon_id in enumerate(wagon_ids)}

    # Track colors
    track_colors = {
        'collection': '#e74c3c',
        'collection1': '#e74c3c',
        'collection2': '#c0392b',
        'retrofit': '#f39c12',
        'WS_01': '#27ae60',
        'WS_02': '#3498db',
        'retrofitted': '#9b59b6',
        'parking': '#34495e',
        'REJECTED': '#d62728',
    }

    # Add parking track colors
    for i in range(1, 20):
        track_colors[f'parking{i}'] = '#34495e'

    # Create figure
    fig_height = max(8, len(wagon_ids) * 0.15)
    fig, ax = plt.subplots(figsize=(14, fig_height))

    # Plot each wagon's journey
    for wagon_id in wagon_ids:
        wagon_data = journey_df[journey_df['wagon_id'] == wagon_id].sort_values('timestamp')
        if wagon_data.empty:
            continue

        y_pos = wagon_positions[wagon_id]

        for i in range(len(wagon_data) - 1):
            row = wagon_data.iloc[i]
            next_row = wagon_data.iloc[i + 1]

            track = row['track_id']
            status = row['status']
            start_time = row['timestamp']
            end_time = next_row['timestamp']
            duration = end_time - start_time

            color = track_colors.get(track, '#7f7f7f')
            hatch = '///' if status == 'RETROFITTING' else None
            alpha = 1.0 if status == 'RETROFITTING' else 0.8

            ax.barh(
                y_pos,
                duration,
                left=start_time,
                height=0.8,
                color=color,
                alpha=alpha,
                edgecolor='black',
                linewidth=0.3,
                hatch=hatch,
            )

        # Add final position
        last_row = wagon_data.iloc[-1]
        max_time = journey_df['timestamp'].max()
        duration = max_time - last_row['timestamp']
        if duration > 0:
            track = last_row['track_id']
            status = last_row['status']
            color = track_colors.get(track, '#7f7f7f')
            hatch = '///' if status == 'RETROFITTING' else None
            alpha = 1.0 if status == 'RETROFITTING' else 0.8

            ax.barh(
                y_pos,
                duration,
                left=last_row['timestamp'],
                height=0.8,
                color=color,
                alpha=alpha,
                edgecolor='black',
                linewidth=0.3,
                hatch=hatch,
            )

    # Set y-axis (inverted - first wagon at top)
    ax.set_yticks(range(len(wagon_ids)))
    ax.set_yticklabels([wagon_ids[len(wagon_ids) - 1 - i] for i in range(len(wagon_ids))], fontsize=6)
    ax.set_xlabel('Simulation Time (minutes)', fontsize=11)
    ax.set_ylabel('Wagon ID', fontsize=11)
    ax.set_title('Wagon Journeys Over Time', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Add legend
    from matplotlib.patches import Patch

    unique_tracks = sorted(set(journey_df['track_id'].unique()))
    priority_tracks = [
        'collection',
        'collection1',
        'collection2',
        'retrofit',
        'WS_01',
        'WS_02',
        'retrofitted',
        'parking',
        'REJECTED',
    ]
    legend_tracks = [t for t in priority_tracks if t in unique_tracks]
    legend_tracks.extend([t for t in unique_tracks if t not in legend_tracks][:5])

    legend_elements = []
    for track in legend_tracks:
        legend_elements.append(
            Patch(facecolor=track_colors.get(track, '#7f7f7f'), edgecolor='black', label=track, alpha=0.8)
        )
    legend_elements.append(Patch(facecolor='gray', edgecolor='black', hatch='///', label='RETROFITTING', alpha=1.0))

    ax.legend(handles=legend_elements, loc='upper right', fontsize=8, ncol=2)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.caption(f'Showing {len(wagon_ids)} wagons. Each color = track. Hatched (///) = actively retrofitting.')


def _render_status_distribution(data: dict[str, Any]) -> None:
    """Render wagon status distribution charts."""
    metrics = data.get('metrics', {})
    rejected_wagons = data.get('rejected_wagons')

    # Calculate status counts
    total_arrived = metrics.get('wagons_arrived', 0)
    parked = metrics.get('wagons_parked', 0)
    rejected = metrics.get('wagons_rejected', 0)
    in_process = total_arrived - parked - rejected

    col1, col2 = st.columns([2, 1])

    with col1:
        # Status bar chart
        status_data = pd.DataFrame(
            {'Status': ['Parked', 'In Process', 'Rejected'], 'Count': [parked, in_process, rejected]}
        )
        st.bar_chart(status_data.set_index('Status'))

    with col2:
        # Status table
        st.dataframe(status_data, use_container_width=True, hide_index=True)
        st.caption(f'Total arrived: {total_arrived}')

    # Rejection breakdown if available
    if rejected_wagons is not None and not rejected_wagons.empty:
        st.markdown('**Rejection Breakdown:**')
        rejection_counts = rejected_wagons['rejection_type'].value_counts()
        rejection_df = pd.DataFrame({'Rejection Type': rejection_counts.index, 'Count': rejection_counts.values})

        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(rejection_df.set_index('Rejection Type'))
        with col2:
            st.dataframe(rejection_df, use_container_width=True, hide_index=True)


def _render_journey_statistics(journey_df: pd.DataFrame) -> None:
    """Render journey statistics."""
    col1, col2, col3 = st.columns(3)

    with col1:
        # Count wagons by final status
        final_status = journey_df.groupby('wagon_id').last()['status'].value_counts()
        st.markdown('**Final Status**')
        st.dataframe(final_status.reset_index(name='count'), use_container_width=True, hide_index=True)

    with col2:
        # Average journey length
        journey_lengths = journey_df.groupby('wagon_id').size()
        st.metric('Avg Events per Wagon', f'{journey_lengths.mean():.1f}')
        st.metric('Max Events', journey_lengths.max())
        st.metric('Min Events', journey_lengths.min())

    with col3:
        # Most common paths
        wagon_paths = journey_df.groupby('wagon_id')['status'].apply(lambda x: ' → '.join(x)).value_counts().head(5)
        st.markdown('**Top 5 Journey Paths**')
        for path, count in wagon_paths.items():
            st.text(f'{count}x: {path}')


def _render_wagon_journey_history(journey_df: pd.DataFrame) -> None:
    """Render individual wagon journey history viewer."""
    wagon_ids = sorted(journey_df['wagon_id'].unique())
    selected_wagon = st.selectbox('Select wagon to view journey:', wagon_ids, index=0)

    if selected_wagon:
        wagon_history = journey_df[journey_df['wagon_id'] == selected_wagon]

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(f'**Journey for {selected_wagon}**')
            display_cols = ['timestamp', 'event', 'track_id', 'status']
            st.dataframe(wagon_history[display_cols], use_container_width=True, hide_index=True)

        with col2:
            st.markdown('**Journey Timeline**')
            _render_wagon_timeline(wagon_history)


def _render_wagon_timeline(wagon_history: pd.DataFrame) -> None:
    """Render timeline chart for single wagon."""
    fig, ax = plt.subplots(figsize=(8, 4))

    status_colors = {
        'ARRIVED': '#8c564b',
        'WAITING_RETROFIT': '#ff7f0e',
        'RETROFITTING': '#2ca02c',
        'COMPLETED': '#1f77b4',
        'RETROFITTED': '#17becf',
        'DISTRIBUTED': '#bcbd22',
        'PARKED': '#9467bd',
        'REJECTED': '#d62728',
    }

    y_pos = 0
    for i in range(len(wagon_history) - 1):
        row = wagon_history.iloc[i]
        next_row = wagon_history.iloc[i + 1]

        start_time = row['timestamp']
        end_time = next_row['timestamp']
        duration = end_time - start_time
        status = row['status']

        color = status_colors.get(status, '#7f7f7f')
        ax.barh(y_pos, duration, left=start_time, height=0.8, color=color, alpha=0.8, edgecolor='black', linewidth=0.5)

        if duration > 50:
            ax.text(start_time + duration / 2, y_pos, status, ha='center', va='center', fontsize=8, fontweight='bold')

    # Add final status
    last_row = wagon_history.iloc[-1]
    ax.barh(
        y_pos,
        100,
        left=last_row['timestamp'],
        height=0.8,
        color=status_colors.get(last_row['status'], '#7f7f7f'),
        alpha=0.8,
        edgecolor='black',
        linewidth=0.5,
    )
    ax.text(
        last_row['timestamp'] + 50, y_pos, last_row['status'], ha='center', va='center', fontsize=8, fontweight='bold'
    )

    ax.set_xlabel('Simulation Time (minutes)', fontsize=10)
    ax.set_yticks([])
    ax.set_title('Status Timeline', fontsize=11, fontweight='bold')
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Add legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=color, edgecolor='black', label=status, alpha=0.8) for status, color in status_colors.items()
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=7, ncol=2)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
