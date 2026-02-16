"""Bottleneck analysis tab - visualizes timeline data for bottleneck identification."""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_bottleneck_tab(data: dict[str, Any]) -> None:  # pylint: disable=too-many-locals
    """Render bottleneck analysis tab.

    Note: Multiple local variables needed for comprehensive bottleneck analysis.
    """
    st.header('🚧 Bottleneck Analysis')

    timeline = data.get('timeline')
    wagon_journey = data.get('wagon_journey')

    if timeline is None or timeline.empty:
        st.warning('⚠️ No timeline data available')
        return

    # Section 1: Process Flow Heatmap
    if wagon_journey is not None and not wagon_journey.empty:
        st.subheader('Process Flow Heatmap')
        st.write('Shows wagon count in each process stage over time - darker colors indicate bottlenecks')
        _render_process_flow_heatmap(wagon_journey)
        st.markdown('---')

    # Section 2: Resource Utilization Overview
    st.subheader('Resource Utilization Overview')
    _render_resource_overview(timeline)

    st.markdown('---')

    # Section 3: Track Queue Analysis
    st.subheader('Track Queue Analysis')
    _render_track_queues(timeline)

    st.markdown('---')

    # Section 4: Workshop Utilization
    st.subheader('Workshop Utilization')
    _render_workshop_utilization(timeline)


def _render_process_flow_heatmap(wagon_journey: pd.DataFrame) -> None:  # pylint: disable=too-many-locals
    """Render process flow heatmap showing wagon count in each stage over time.

    Note: Multiple local variables needed for heatmap visualization.
    """
    # Define meaningful process stages (exclude transient ARRIVED state)
    process_stages = ['WAITING', 'PROCESSING', 'COMPLETED', 'PARKED', 'REJECTED']

    # Create time bins
    max_time = wagon_journey['timestamp'].max()
    bin_size = max(60, max_time / 40)  # 40 time bins
    time_bins = list(range(0, int(max_time) + int(bin_size), int(bin_size)))

    # Count wagons in each stage for each time bin
    heatmap_data = []
    for stage in process_stages:
        stage_counts = []
        for i in range(len(time_bins) - 1):
            bin_start, bin_end = time_bins[i], time_bins[i + 1]

            # Count unique wagons in this stage during this time bin
            bin_data = wagon_journey[
                (wagon_journey['timestamp'] >= bin_start)
                & (wagon_journey['timestamp'] < bin_end)
                & (wagon_journey['status'] == stage)
            ]
            wagon_count = len(bin_data['wagon_id'].unique())
            stage_counts.append(wagon_count)

        heatmap_data.append(stage_counts)

    # Create heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data,
            x=[f'{time_bins[i]:.0f}' for i in range(len(time_bins) - 1)],
            y=process_stages,
            colorscale='YlOrRd',  # Yellow to Orange to Red
            colorbar={'title': 'Wagon Count'},
            hovertemplate='Stage: %{y}<br>Time: %{x} min<br>Wagons: %{z}<extra></extra>',
        )
    )

    fig.update_layout(
        title='Wagon Count by Process Stage Over Time',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Process Stage',
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption('🟡 Light: Few wagons (smooth flow) | 🟠 Medium: Moderate load | 🔴 Dark: Many wagons (bottleneck)')

    # Add insights
    col1, col2, col3 = st.columns(3)

    with col1:
        # Find stage with highest average count
        avg_counts = [sum(counts) / len(counts) for counts in heatmap_data]
        max_stage_idx = avg_counts.index(max(avg_counts))
        st.metric('Most Congested Stage', process_stages[max_stage_idx], f'{avg_counts[max_stage_idx]:.1f} avg wagons')

    with col2:
        # Find peak time
        total_by_time = [sum(heatmap_data[j][i] for j in range(len(process_stages))) for i in range(len(time_bins) - 1)]
        peak_time_idx = total_by_time.index(max(total_by_time))
        st.metric(
            'Peak Congestion Time',
            f'{time_bins[peak_time_idx]:.0f} min',
            f'{total_by_time[peak_time_idx]} total wagons',
        )

    with col3:
        # Calculate flow efficiency (ratio of processing to waiting)
        processing_total = sum(heatmap_data[process_stages.index('PROCESSING')])
        waiting_total = sum(heatmap_data[process_stages.index('WAITING')])
        efficiency = (
            (processing_total / (processing_total + waiting_total) * 100)
            if (processing_total + waiting_total) > 0
            else 0
        )
        st.metric('Processing Efficiency', f'{efficiency:.1f}%', 'Processing vs Waiting')


def _render_resource_overview(timeline: pd.DataFrame) -> None:
    """Render resource utilization overview."""
    # Identify resource columns
    track_cols = [col for col in timeline.columns if col.startswith('track_')]
    workshop_cols = [col for col in timeline.columns if col.startswith('workshop_')]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            'Track Queues',
            len(track_cols),
            f'Max: {max(timeline[col].max() for col in track_cols) if track_cols else 0:.0f} wagons',
        )

    with col2:
        st.metric(
            'Workshop Bays',
            len(workshop_cols),
            f'Max: {max(timeline[col].max() for col in workshop_cols) if workshop_cols else 0:.0f} busy',
        )

    with col3:
        if 'wagons_in_process' in timeline.columns:
            st.metric('Peak Wagons in Process', f'{timeline["wagons_in_process"].max():.0f}')


def _render_track_queues(timeline: pd.DataFrame) -> None:
    """Render track queue analysis with Plotly."""
    track_cols = [col for col in timeline.columns if col.startswith('track_')]

    if not track_cols:
        st.info('No track queue data available')
        return

    # Summary table
    col1, col2 = st.columns([1, 2])

    with col1:
        track_stats = []
        for col in track_cols:
            track_stats.append(
                {
                    'Track': col.replace('track_', ''),
                    'Max Queue': timeline[col].max(),
                    'Avg Queue': timeline[col].mean(),
                    'Peak Time': timeline.loc[timeline[col].idxmax(), 'timestamp'],
                }
            )

        track_df = pd.DataFrame(track_stats).sort_values('Max Queue', ascending=False)
        track_df['Max Queue'] = track_df['Max Queue'].round(1)
        track_df['Avg Queue'] = track_df['Avg Queue'].round(1)
        track_df['Peak Time'] = track_df['Peak Time'].round(0)
        st.dataframe(track_df, use_container_width=True, hide_index=True)

    with col2:
        # Plot track queues over time
        fig = go.Figure()

        for col in track_cols:
            fig.add_trace(
                go.Scatter(
                    x=timeline['timestamp'],
                    y=timeline[col],
                    name=col.replace('track_', ''),
                    mode='lines',
                    line={'width': 2},
                    hovertemplate=(
                        '<b>%{fullData.name}</b><br>Time: %{x:.1f} min<br>Queue: %{y:.1f} wagons<extra></extra>'
                    ),
                )
            )

        fig.update_layout(
            title='Track Queue Lengths Over Time',
            xaxis_title='Simulation Time (minutes)',
            yaxis_title='Wagons in Queue',
            height=400,
            hovermode='x unified',
        )

        st.plotly_chart(fig, use_container_width=True)


def _render_workshop_utilization(timeline: pd.DataFrame) -> None:
    """Render workshop utilization analysis with Plotly."""
    workshop_cols = [col for col in timeline.columns if col.startswith('workshop_')]

    if not workshop_cols:
        st.info('No workshop utilization data available')
        return

    # Summary table
    col1, col2 = st.columns([1, 2])

    with col1:
        workshop_stats = []
        for col in workshop_cols:
            workshop_stats.append(
                {
                    'Workshop': col.replace('workshop_', ''),
                    'Max Busy': timeline[col].max(),
                    'Avg Busy': timeline[col].mean(),
                    'Peak Time': timeline.loc[timeline[col].idxmax(), 'timestamp'],
                }
            )

        workshop_df = pd.DataFrame(workshop_stats).sort_values('Max Busy', ascending=False)
        workshop_df['Max Busy'] = workshop_df['Max Busy'].round(1)
        workshop_df['Avg Busy'] = workshop_df['Avg Busy'].round(1)
        workshop_df['Peak Time'] = workshop_df['Peak Time'].round(0)
        st.dataframe(workshop_df, use_container_width=True, hide_index=True)

    with col2:
        # Plot workshop utilization over time
        fig = go.Figure()

        for col in workshop_cols:
            fig.add_trace(
                go.Scatter(
                    x=timeline['timestamp'],
                    y=timeline[col],
                    name=col.replace('workshop_', ''),
                    mode='lines',
                    line={'width': 2},
                    hovertemplate='<b>%{fullData.name}</b><br>Time: %{x:.1f} min<br>Busy Bays: %{y:.1f}<extra></extra>',
                )
            )

        fig.update_layout(
            title='Workshop Utilization Over Time',
            xaxis_title='Simulation Time (minutes)',
            yaxis_title='Busy Bays',
            height=400,
            hovermode='x unified',
        )

        st.plotly_chart(fig, use_container_width=True)
