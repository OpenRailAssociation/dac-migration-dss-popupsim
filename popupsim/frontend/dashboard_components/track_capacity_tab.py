"""Track capacity tab - visualizes track utilization and capacity."""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_track_capacity_tab(data: dict[str, Any]) -> None:
    """Render track capacity analysis tab."""
    st.header('🛤️ Track Capacity')

    track_capacity = data.get('track_capacity')

    if track_capacity is None or track_capacity.empty:
        st.warning('⚠️ No track capacity data available')
        return

    # Get latest capacity state for each track
    latest_capacity = track_capacity.groupby('track_id').last().reset_index()
    latest_capacity['utilization_percent'] = (latest_capacity['used_after'] / latest_capacity['capacity'] * 100).fillna(
        0
    )

    # Section 1: Track Utilization Overview
    st.subheader('Track Utilization Overview')
    _render_utilization_overview(latest_capacity)

    st.markdown('---')

    # Section 2: Track Capacity Over Time
    st.subheader('Track Capacity Over Time')
    _render_capacity_over_time(track_capacity)

    st.markdown('---')

    # Section 3: Capacity Heatmap
    st.subheader('Capacity Heatmap Over Time')
    _render_capacity_heatmap(track_capacity)

    st.markdown('---')

    # Section 4: Peak Utilization Analysis
    st.subheader('Peak Utilization Analysis')
    _render_peak_utilization(track_capacity)


def _render_utilization_overview(latest_capacity: pd.DataFrame) -> None:
    """Render utilization overview with metrics and charts."""
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    avg_util = latest_capacity['utilization_percent'].mean()
    max_util = latest_capacity['utilization_percent'].max()
    high_util = len(latest_capacity[latest_capacity['utilization_percent'] >= 85])
    medium_util = len(
        latest_capacity[(latest_capacity['utilization_percent'] >= 70) & (latest_capacity['utilization_percent'] < 85)]
    )

    with col1:
        st.metric('Avg Utilization', f'{avg_util:.1f}%')
    with col2:
        st.metric('Max Utilization', f'{max_util:.1f}%')
    with col3:
        st.metric('🔴 High (≥85%)', high_util)
    with col4:
        st.metric('🟡 Medium (70-85%)', medium_util)

    # Utilization bar chart with color coding
    col1, col2 = st.columns([2, 1])

    with col1:
        # Create color-coded bar chart
        colors = latest_capacity['utilization_percent'].apply(
            lambda x: '#DC3545' if x >= 85 else '#FFC107' if x >= 70 else '#28A745'
        )

        fig = go.Figure(
            go.Bar(
                x=latest_capacity['track_id'],
                y=latest_capacity['utilization_percent'],
                marker_color=colors,
                text=latest_capacity['utilization_percent'].round(1),
                texttemplate='%{text}%',
                textposition='outside',
                hovertemplate=(
                    '<b>%{x}</b><br>Utilization: %{y:.1f}%<br>'
                    'Used: %{customdata[0]:.1f}<br>'
                    'Capacity: %{customdata[1]:.1f}<extra></extra>'
                ),
                customdata=latest_capacity[['used_after', 'capacity']].values,
            )
        )

        fig.update_layout(
            title='Track Utilization',
            xaxis_title='Track ID',
            yaxis_title='Utilization (%)',
            yaxis_range=[0, 105],
            height=400,
        )

        # Add threshold lines
        fig.add_hline(y=85, line_dash='dash', line_color='red', annotation_text='High (85%)')
        fig.add_hline(y=70, line_dash='dash', line_color='orange', annotation_text='Medium (70%)')

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Detailed table
        display_df = latest_capacity[['track_id', 'capacity', 'used_after', 'utilization_percent']].copy()
        display_df.columns = ['Track', 'Capacity', 'Used', 'Util %']
        display_df['Util %'] = display_df['Util %'].round(1)
        display_df['Capacity'] = display_df['Capacity'].round(1)
        display_df['Used'] = display_df['Used'].round(1)
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)


def _render_capacity_over_time(track_capacity: pd.DataFrame) -> None:
    """Render track capacity over time with Plotly."""
    all_tracks = sorted(track_capacity['track_id'].unique())

    # Select tracks to visualize
    selected_tracks = st.multiselect(
        'Select tracks to visualize:', options=all_tracks, default=all_tracks[:5] if len(all_tracks) > 5 else all_tracks
    )

    if not selected_tracks:
        st.info('Select tracks to visualize capacity over time')
        return

    fig = go.Figure()

    for track_id in selected_tracks:
        track_data = track_capacity[track_capacity['track_id'] == track_id].sort_values('timestamp')
        if not track_data.empty:
            # Calculate utilization percentage
            util_pct = track_data['used_after'] / track_data['capacity'] * 100

            fig.add_trace(
                go.Scatter(
                    x=track_data['timestamp'],
                    y=util_pct,
                    name=track_id,
                    mode='lines',
                    line={'width': 2},
                    hovertemplate=(
                        '<b>%{fullData.name}</b><br>Time: %{x:.1f} min<br>Utilization: %{y:.1f}%<extra></extra>'
                    ),
                )
            )

    fig.update_layout(
        title='Track Utilization Over Time',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Utilization (%)',
        yaxis_range=[0, 105],
        height=500,
        hovermode='x unified',
    )

    # Add threshold lines
    fig.add_hline(y=85, line_dash='dash', line_color='red', annotation_text='High (85%)', annotation_position='right')
    fig.add_hline(
        y=70, line_dash='dash', line_color='orange', annotation_text='Medium (70%)', annotation_position='right'
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_capacity_heatmap(track_capacity: pd.DataFrame) -> None:  # pylint: disable=too-many-locals
    """Render capacity heatmap showing all tracks over time.

    Note: Multiple local variables needed for heatmap visualization.
    """
    # Create time bins
    max_time = track_capacity['timestamp'].max()
    bin_size = max(60, max_time / 30)  # 30 time bins
    time_bins = list(range(0, int(max_time) + int(bin_size), int(bin_size)))

    # Get all tracks
    all_tracks = sorted(track_capacity['track_id'].unique())

    # Create heatmap data
    heatmap_data = []
    for track_id in all_tracks:
        track_data = track_capacity[track_capacity['track_id'] == track_id].sort_values('timestamp')
        utilization_by_bin = []

        for i in range(len(time_bins) - 1):
            bin_start, bin_end = time_bins[i], time_bins[i + 1]
            bin_data = track_data[(track_data['timestamp'] >= bin_start) & (track_data['timestamp'] < bin_end)]

            if not bin_data.empty:
                # Use average utilization in this bin
                avg_util = (bin_data['used_after'] / bin_data['capacity'] * 100).mean()
                utilization_by_bin.append(avg_util)
            else:
                # Use last known value
                prev_data = track_data[track_data['timestamp'] < bin_start]
                if not prev_data.empty:
                    last_util = prev_data.iloc[-1]['used_after'] / prev_data.iloc[-1]['capacity'] * 100
                    utilization_by_bin.append(last_util)
                else:
                    utilization_by_bin.append(0)

        heatmap_data.append(utilization_by_bin)

    # Create heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data,
            x=[f'{time_bins[i]:.0f}' for i in range(len(time_bins) - 1)],
            y=all_tracks,
            colorscale=[
                [0, '#28A745'],  # Green (0%)
                [0.7, '#FFC107'],  # Yellow (70%)
                [0.85, '#DC3545'],  # Red (85%)
                [1, '#8B0000'],  # Dark red (100%)
            ],
            zmin=0,
            zmax=100,
            colorbar={'title': 'Utilization (%)', 'ticksuffix': '%'},
            hovertemplate='Track: %{y}<br>Time: %{x} min<br>Utilization: %{z:.1f}%<extra></extra>',
        )
    )

    fig.update_layout(
        title='Track Utilization Heatmap',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Track ID',
        height=max(300, len(all_tracks) * 30),
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption('🟢 Green: Low utilization (<70%) | 🟡 Yellow: Medium (70-85%) | 🔴 Red: High (≥85%)')


def _render_peak_utilization(track_capacity: pd.DataFrame) -> None:
    """Render peak utilization analysis."""
    # Find peak utilization for each track
    peak_data = []

    for track_id in track_capacity['track_id'].unique():
        track_data = track_capacity[track_capacity['track_id'] == track_id]
        track_data['utilization_percent'] = track_data['used_after'] / track_data['capacity'] * 100

        peak_row = track_data.loc[track_data['utilization_percent'].idxmax()]

        peak_data.append(
            {
                'Track ID': track_id,
                'Peak Utilization (%)': peak_row['utilization_percent'],
                'Peak Time (min)': peak_row['timestamp'],
                'Capacity': peak_row['capacity'],
                'Used at Peak': peak_row['used_after'],
                'Times Over 85%': len(track_data[track_data['utilization_percent'] >= 85]),
            }
        )

    peak_df = pd.DataFrame(peak_data).sort_values('Peak Utilization (%)', ascending=False)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Peak utilization bar chart
        colors = peak_df['Peak Utilization (%)'].apply(
            lambda x: '#DC3545' if x >= 85 else '#FFC107' if x >= 70 else '#28A745'
        )

        fig = go.Figure(
            go.Bar(
                x=peak_df['Track ID'],
                y=peak_df['Peak Utilization (%)'],
                marker_color=colors,
                text=peak_df['Peak Utilization (%)'].round(1),
                texttemplate='%{text}%',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Peak: %{y:.1f}%<br>At time: %{customdata:.1f} min<extra></extra>',
                customdata=peak_df['Peak Time (min)'],
            )
        )

        fig.update_layout(
            title='Peak Utilization by Track',
            xaxis_title='Track ID',
            yaxis_title='Peak Utilization (%)',
            yaxis_range=[0, 105],
            height=400,
        )

        fig.add_hline(y=85, line_dash='dash', line_color='red')

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Peak utilization table
        display_df = peak_df[['Track ID', 'Peak Utilization (%)', 'Peak Time (min)', 'Times Over 85%']].copy()
        display_df['Peak Utilization (%)'] = display_df['Peak Utilization (%)'].round(1)
        display_df['Peak Time (min)'] = display_df['Peak Time (min)'].round(0)
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
