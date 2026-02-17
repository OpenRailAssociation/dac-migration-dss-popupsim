"""Workshop tab - visualizes workshop performance and utilization."""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_workshop_tab(data: dict[str, Any]) -> None:
    """Render workshop analysis tab."""
    st.header('🏭 Workshop Performance Analysis')

    workshop_metrics = data.get('workshop_metrics')
    workshop_util = data.get('workshop_utilization')
    wagon_journey = data.get('wagon_journey')

    if workshop_metrics is None or workshop_metrics.empty:
        st.warning('⚠️ No workshop metrics data available')
        return

    # Section 1: Performance Overview
    st.subheader('Workshop Performance Overview')
    _render_performance_overview(workshop_metrics)

    st.markdown('---')

    # Section 2: Utilization Over Time
    if workshop_util is not None and not workshop_util.empty:
        st.subheader('Utilization Over Time')
        _render_utilization_timeline(workshop_util)

        st.markdown('---')

        # Section 3: Bay Occupancy Timeline
        st.subheader('Bay Occupancy Timeline')
        _render_bay_occupancy(workshop_util, wagon_journey)

        st.markdown('---')

    # Section 4: Workshop Comparison
    st.subheader('Workshop Comparison')
    _render_workshop_comparison(workshop_metrics)

    st.markdown('---')

    # Section 5: Efficiency Analysis
    st.subheader('Efficiency Analysis')
    _render_efficiency_analysis(workshop_metrics)

    if workshop_util is not None and not workshop_util.empty:
        st.markdown('---')

        # Section 6: Capacity Heatmap
        st.subheader('Capacity Heatmap')
        _render_capacity_heatmap(workshop_util)


def _render_performance_overview(metrics_df: pd.DataFrame) -> None:
    """Render workshop performance overview with key metrics."""
    workshops = sorted(metrics_df['workshop_id'].unique())
    cols = st.columns(len(workshops))

    for idx, ws_id in enumerate(workshops):
        ws_data = metrics_df[metrics_df['workshop_id'] == ws_id].iloc[0]

        with cols[idx]:
            st.markdown(f'### {ws_id}')

            # Utilization with color coding
            util = ws_data['utilization_percent']
            if util >= 85:
                util_color = '🔴'
            elif util >= 70:
                util_color = '🟡'
            else:
                util_color = '🟢'

            st.metric('Completed Retrofits', int(ws_data['completed_retrofits']))
            st.metric('Throughput/Hour', f'{ws_data["throughput_per_hour"]:.2f}')
            st.metric(f'{util_color} Utilization', f'{util:.1f}%')
            st.metric('Retrofit Time', f'{ws_data["total_retrofit_time"]:.0f} min')
            st.metric('Waiting Time', f'{ws_data["total_waiting_time"]:.0f} min')


def _render_utilization_timeline(util_df: pd.DataFrame) -> None:
    """Render utilization timeline chart."""
    fig = go.Figure()

    workshops = sorted(util_df['workshop_id'].unique())
    colors = px.colors.qualitative.Set2

    for idx, ws_id in enumerate(workshops):
        ws_data = util_df[util_df['workshop_id'] == ws_id].sort_values('timestamp')

        fig.add_trace(
            go.Scatter(
                x=ws_data['timestamp'],
                y=ws_data['utilization_after_percent'],
                mode='lines',
                name=ws_id,
                line={'width': 2, 'color': colors[idx % len(colors)]},
                hovertemplate='<b>%{fullData.name}</b><br>Time: %{x:.1f} min<br>Utilization: %{y:.1f}%<extra></extra>',
            )
        )

    # Add threshold lines
    fig.add_hline(
        y=85,
        line_dash='dash',
        line_color='red',
        opacity=0.5,
        annotation_text='85% High Load',
        annotation_position='right',
    )
    fig.add_hline(
        y=70,
        line_dash='dash',
        line_color='orange',
        opacity=0.5,
        annotation_text='70% Optimal',
        annotation_position='right',
    )

    fig.update_layout(
        title='Workshop Utilization Over Time',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Utilization (%)',
        yaxis={'range': [0, 105]},
        height=400,
        hovermode='x unified',
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption('🟢 <70% = Underutilized | 🟡 70-85% = Optimal | 🔴 ≥85% = High Load')


def _classify_bay_status(util: float) -> tuple[str, str]:
    """Classify bay status based on utilization."""
    if util >= 85:
        return 'High Load', '#d62728'
    if util >= 50:
        return 'Active', '#ff7f0e'
    if util > 0:
        return 'Low Load', '#2ca02c'
    return 'Idle', '#7f7f7f'


def _get_wagons_in_workshop(
    wagon_journey: pd.DataFrame | None, ws_id: str, start_time: float, end_time: float
) -> list[str]:
    """Get list of wagons in workshop during time period."""
    if wagon_journey is None or wagon_journey.empty:
        return []

    ws_wagons = wagon_journey[
        (wagon_journey['track_id'] == ws_id)
        & (wagon_journey['timestamp'] >= start_time)
        & (wagon_journey['timestamp'] < end_time)
        & (wagon_journey['status'] == 'PROCESSING')
    ]['wagon_id'].unique()
    return sorted(ws_wagons, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)


def _render_bay_occupancy(  # pylint: disable=too-many-locals
    util_df: pd.DataFrame, wagon_journey: pd.DataFrame | None = None
) -> None:
    """Render bay occupancy Gantt chart with wagon IDs.

    Note: Multiple local variables needed for bay occupancy visualization.
    """
    workshops = sorted(util_df['workshop_id'].unique())

    segments = []
    for ws_id in workshops:
        ws_data = util_df[util_df['workshop_id'] == ws_id].sort_values('timestamp')

        for i in range(len(ws_data) - 1):
            row = ws_data.iloc[i]
            next_row = ws_data.iloc[i + 1]

            start_time = row['timestamp']
            end_time = next_row['timestamp']
            duration = end_time - start_time

            if duration <= 0:
                continue

            util = row['utilization_after_percent']
            status, color = _classify_bay_status(util)
            wagons_in_workshop = _get_wagons_in_workshop(wagon_journey, ws_id, start_time, end_time)

            segments.append(
                {
                    'Workshop': ws_id,
                    'Start': start_time,
                    'Duration': duration,
                    'Status': status,
                    'Color': color,
                    'Busy': row['busy_after'],
                    'Total': row['total_bays'],
                    'Utilization': util,
                    'Wagons': ', '.join(wagons_in_workshop[:5]) + ('...' if len(wagons_in_workshop) > 5 else ''),
                }
            )

    if not segments:
        st.info('No occupancy data to display')
        return

    df_segments = pd.DataFrame(segments)
    fig = go.Figure()

    for status in ['Idle', 'Low Load', 'Active', 'High Load']:
        status_data = df_segments[df_segments['Status'] == status]
        if not status_data.empty:
            hover_text = []
            for _, row in status_data.iterrows():
                text = (
                    f'<b>{row["Workshop"]}</b><br>{status}<br>'
                    f'Time: {row["Start"]:.1f} min<br>'
                    f'Duration: {row["Duration"]:.1f} min<br>'
                    f'Utilization: {row["Utilization"]:.1f}%'
                )
                if row['Wagons']:
                    text += f'<br>Wagons: {row["Wagons"]}'
                hover_text.append(text)

            fig.add_trace(
                go.Bar(
                    y=status_data['Workshop'],
                    x=status_data['Duration'],
                    base=status_data['Start'],
                    orientation='h',
                    name=status,
                    marker_color=status_data['Color'].iloc[0],
                    text=status_data['Wagons'],
                    textposition='inside',
                    textfont={'size': 8, 'color': 'white'},
                    hovertemplate='%{customdata}<extra></extra>',
                    customdata=hover_text,
                )
            )

    fig.update_layout(
        title='Bay Occupancy Timeline',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Workshop',
        barmode='stack',
        height=max(300, len(workshops) * 80),
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        'Wagon IDs shown inside bars (max 5 per segment). '
        'Hover for full details including all wagons in that time period.'
    )


def _render_workshop_comparison(metrics_df: pd.DataFrame) -> None:
    """Render side-by-side workshop comparison."""
    col1, col2 = st.columns(2)

    with col1:
        # Completed Retrofits
        fig = go.Figure(
            data=[
                go.Bar(
                    x=metrics_df['workshop_id'],
                    y=metrics_df['completed_retrofits'],
                    marker_color='#3498db',
                    text=metrics_df['completed_retrofits'],
                    textposition='auto',
                )
            ]
        )
        fig.update_layout(
            title='Completed Retrofits', xaxis_title='Workshop', yaxis_title='Count', height=300, showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Throughput
        fig = go.Figure(
            data=[
                go.Bar(
                    x=metrics_df['workshop_id'],
                    y=metrics_df['throughput_per_hour'],
                    marker_color='#2ecc71',
                    text=metrics_df['throughput_per_hour'].round(2),
                    textposition='auto',
                )
            ]
        )
        fig.update_layout(
            title='Throughput (wagons/hour)',
            xaxis_title='Workshop',
            yaxis_title='Wagons/Hour',
            height=300,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Utilization with color coding
        colors = [
            '#2ecc71' if u < 70 else '#f39c12' if u < 85 else '#e74c3c' for u in metrics_df['utilization_percent']
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=metrics_df['workshop_id'],
                    y=metrics_df['utilization_percent'],
                    marker_color=colors,
                    text=metrics_df['utilization_percent'].round(1),
                    textposition='auto',
                )
            ]
        )
        fig.add_hline(y=85, line_dash='dash', line_color='red', opacity=0.5)
        fig.add_hline(y=70, line_dash='dash', line_color='orange', opacity=0.5)
        fig.update_layout(
            title='Utilization (%)', xaxis_title='Workshop', yaxis_title='Utilization (%)', height=300, showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Processing vs Waiting Time
        fig = go.Figure(
            data=[
                go.Bar(
                    name='Retrofit Time',
                    x=metrics_df['workshop_id'],
                    y=metrics_df['total_retrofit_time'],
                    marker_color='#3498db',
                ),
                go.Bar(
                    name='Waiting Time',
                    x=metrics_df['workshop_id'],
                    y=metrics_df['total_waiting_time'],
                    marker_color='#f39c12',
                ),
            ]
        )
        fig.update_layout(
            title='Processing vs Waiting Time',
            xaxis_title='Workshop',
            yaxis_title='Time (minutes)',
            height=300,
            barmode='group',
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_efficiency_analysis(metrics_df: pd.DataFrame) -> None:
    """Render efficiency analysis with time breakdown."""
    workshops = sorted(metrics_df['workshop_id'].unique())
    cols = st.columns(len(workshops))

    for idx, ws_id in enumerate(workshops):
        ws_data = metrics_df[metrics_df['workshop_id'] == ws_id].iloc[0]

        with cols[idx]:
            st.markdown(f'**{ws_id} Time Breakdown**')

            retrofit_time = ws_data['total_retrofit_time']
            waiting_time = ws_data['total_waiting_time']
            total_time = retrofit_time + waiting_time

            # Donut chart
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=['Retrofit Time', 'Waiting Time'],
                        values=[retrofit_time, waiting_time],
                        hole=0.4,
                        marker_colors=['#3498db', '#f39c12'],
                        textinfo='label+percent',
                        hovertemplate='<b>%{label}</b><br>%{value:.0f} min<br>%{percent}<extra></extra>',
                    )
                ]
            )
            fig.update_layout(height=300, showlegend=True, margin={'t': 20, 'b': 20, 'l': 20, 'r': 20})
            st.plotly_chart(fig, use_container_width=True)

            # Metrics
            efficiency = (retrofit_time / total_time * 100) if total_time > 0 else 0
            avg_cycle = (total_time / ws_data['completed_retrofits']) if ws_data['completed_retrofits'] > 0 else 0

            st.metric('Efficiency', f'{efficiency:.1f}%')
            st.metric('Avg Cycle Time', f'{avg_cycle:.1f} min')


def _render_capacity_heatmap(util_df: pd.DataFrame) -> None:
    """Render capacity heatmap showing utilization patterns."""
    workshops = sorted(util_df['workshop_id'].unique())

    # Create time bins (e.g., every 100 minutes)
    max_time = util_df['timestamp'].max()
    time_bins = list(range(0, int(max_time) + 100, 100))

    heatmap_data = []
    for ws_id in workshops:
        ws_data = util_df[util_df['workshop_id'] == ws_id].sort_values('timestamp')

        utilizations = []
        for i in range(len(time_bins) - 1):
            bin_start = time_bins[i]
            bin_end = time_bins[i + 1]

            # Get utilization in this time bin
            bin_data = ws_data[(ws_data['timestamp'] >= bin_start) & (ws_data['timestamp'] < bin_end)]
            if not bin_data.empty:
                avg_util = bin_data['utilization_after_percent'].mean()
            else:
                # Use last known value
                prev_data = ws_data[ws_data['timestamp'] < bin_start]
                avg_util = prev_data['utilization_after_percent'].iloc[-1] if not prev_data.empty else 0

            utilizations.append(avg_util)

        heatmap_data.append(utilizations)

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data,
            x=[f'{t}-{t + 100}' for t in time_bins[:-1]],
            y=workshops,
            colorscale='RdYlGn_r',
            zmid=50,
            zmin=0,
            zmax=100,
            text=[[f'{val:.1f}%' for val in row] for row in heatmap_data],
            texttemplate='%{text}',
            textfont={'size': 10},
            hovertemplate='<b>%{y}</b><br>Time: %{x} min<br>Utilization: %{z:.1f}%<extra></extra>',
            colorbar={'title': 'Utilization (%)'},
        )
    )

    fig.update_layout(
        title='Workshop Utilization Heatmap (100-minute intervals)',
        xaxis_title='Time Period (minutes)',
        yaxis_title='Workshop',
        height=max(300, len(workshops) * 100),
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption('🟢 Green = Low utilization | 🟡 Yellow = Moderate | 🔴 Red = High utilization')
