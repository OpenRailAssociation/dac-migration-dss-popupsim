"""Locomotive details tab - detailed locomotive operations analysis."""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_locomotive_tab(data: dict[str, Any]) -> None:
    """Render locomotive details tab."""
    st.header('🚂 Locomotive Operations Details')

    loco_journey = data.get('locomotive_journey')

    if loco_journey is None or loco_journey.empty:
        st.warning('⚠️ No locomotive journey data available')
        return

    locos = sorted(loco_journey['locomotive_id'].unique())

    if len(locos) > 1:
        view_mode = st.radio('View Mode', ['Single Locomotive', 'Compare Locomotives'], horizontal=True)

        if view_mode == 'Compare Locomotives':
            _render_comparison_view(loco_journey, locos)
            return
        selected_loco = st.selectbox('Select Locomotive', locos)
        loco_data = loco_journey[loco_journey['locomotive_id'] == selected_loco]
    else:
        selected_loco = locos[0]
        loco_data = loco_journey
        st.info(f'📍 Showing data for: **{selected_loco}**')

    _render_utilization_kpi(loco_data)
    st.markdown('---')
    st.subheader('📊 Activity Timeline')
    _render_timeline_chart(loco_data)
    st.markdown('---')

    col1, col2 = st.columns(2)
    with col1:
        st.subheader('📈 Activity Frequency')
        _render_activity_frequency(loco_data)
    with col2:
        st.subheader('📍 Location Analysis')
        _render_location_heatmap(loco_data)

    st.markdown('---')
    st.subheader('⏸️ Idle Time Analysis')
    _render_idle_time_analysis(loco_data)
    st.markdown('---')
    st.subheader('📋 Detailed Event Log')
    _render_event_log(loco_data)


def _render_timeline_chart(loco_data: pd.DataFrame) -> None:
    """Render single-row timeline showing locomotive state over time."""
    loco_data = loco_data.sort_values('timestamp')

    activity_colors = {
        'MOVING': '#3498db',
        'COUPLING': '#2ecc71',
        'DECOUPLING': '#e74c3c',
        'BRAKE_TEST': '#f39c12',
        'INSPECTION': '#9b59b6',
        'SHUNTING_PREP': '#f1c40f',
        'PARKING': '#95a5a6',
        'ALLOCATED': '#34495e',
    }

    segments = []
    for _, row in loco_data.iterrows():
        event_type = row.get('event_type', '')
        timestamp = row.get('timestamp', 0)
        duration = row.get('duration_min', 0) or 0

        if duration <= 0:
            continue

        if event_type == 'MOVING':
            state = 'MOVING'
            label = f'{row.get("from_location", "")}→{row.get("to_location", "")}'
        elif 'COUPLING' in event_type:
            state = 'COUPLING'
            coupler = row.get('coupler_type', '')
            label = f'COUPLING ({coupler})' if coupler else 'COUPLING'
        elif 'DECOUPLING' in event_type:
            state = 'DECOUPLING'
            coupler = row.get('coupler_type', '')
            label = f'DECOUPLING ({coupler})' if coupler else 'DECOUPLING'
        elif event_type in ['BRAKE_TEST', 'INSPECTION', 'SHUNTING_PREP', 'PARKING', 'ALLOCATED']:
            state = event_type
            label = event_type.replace('_', ' ')
        else:
            continue

        segments.append({'State': state, 'Start': timestamp, 'Duration': duration, 'Label': label})

    if not segments:
        st.info('No timeline data to display')
        return

    df_segments = pd.DataFrame(segments)

    fig = go.Figure()

    for state, color in activity_colors.items():
        state_data = df_segments[df_segments['State'] == state]
        if not state_data.empty:
            fig.add_trace(
                go.Bar(
                    y=['Locomotive'] * len(state_data),
                    x=state_data['Duration'],
                    base=state_data['Start'],
                    orientation='h',
                    name=state,
                    marker_color=color,
                    hovertemplate=(
                        '<b>%{fullData.name}</b><br>Start: %{base:.1f} min<br>Duration: %{x:.1f} min<extra></extra>'
                    ),
                )
            )

    fig.update_layout(
        title='Locomotive Activity Timeline',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='',
        barmode='stack',
        height=250,
        showlegend=True,
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(f'Timeline shows {len(segments)} activity segments')


def _render_location_heatmap(loco_data: pd.DataFrame) -> None:
    """Render bar chart showing time at each location."""
    time_by_location: dict[str, float] = {}

    for _, row in loco_data.iterrows():
        event_type = row.get('event_type', '')
        duration = row.get('duration_min', 0) or 0

        # Get location based on event type
        if event_type == 'MOVING':
            location = str(row.get('to_location', 'unknown'))
        elif event_type == 'PARKING':
            location = 'loco_parking'
        else:
            location = str(row.get('location', 'unknown'))

        if location and location != 'unknown' and duration > 0:
            time_by_location[location] = time_by_location.get(location, 0) + duration

    if not time_by_location:
        st.info('No location data available')
        return

    df = pd.DataFrame(list(time_by_location.items()), columns=['Location', 'Time'])
    df = df.sort_values('Time', ascending=True)

    fig = px.bar(
        df,
        x='Time',
        y='Location',
        orientation='h',
        title='Time Spent at Each Location',
        labels={'Time': 'Time (minutes)'},
    )
    fig.update_traces(marker_color='lightblue', text=df['Time'].round(1), textposition='outside')
    st.plotly_chart(fig, use_container_width=True)


def _render_event_log(loco_data: pd.DataFrame) -> None:
    """Render detailed event log table."""
    event_types = ['All', *sorted(loco_data['event_type'].unique().tolist())]
    selected_event = st.selectbox('Filter by Event Type', event_types)

    filtered_data = loco_data[loco_data['event_type'] == selected_event] if selected_event != 'All' else loco_data

    display_cols = [
        'timestamp',
        'datetime',
        'event_type',
        'location',
        'from_location',
        'to_location',
        'coupler_type',
        'wagon_count',
        'duration_min',
    ]

    available_cols = [col for col in display_cols if col in filtered_data.columns]

    st.dataframe(filtered_data[available_cols], use_container_width=True, height=400)

    csv = filtered_data.to_csv(index=False)
    st.download_button(
        label='📥 Download Event Log as CSV', data=csv, file_name='locomotive_event_log.csv', mime='text/csv'
    )


def _render_utilization_kpi(loco_data: pd.DataFrame) -> None:
    """Render utilization KPI metrics."""
    # Calculate active vs idle time
    active_time = 0.0
    idle_time = 0.0

    for _, row in loco_data.iterrows():
        event_type = row.get('event_type', '')
        duration_val = row.get('duration_min', 0) or 0

        if event_type in [
            'MOVING',
            'COUPLING_STARTED',
            'DECOUPLING_STARTED',
            'BRAKE_TEST',
            'INSPECTION',
            'SHUNTING_PREP',
        ]:
            active_time += duration_val
        elif event_type in ['PARKING', 'ALLOCATED']:
            idle_time += duration_val

    total_time = active_time + idle_time
    utilization = (active_time / total_time * 100) if total_time > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric('🟢 Utilization', f'{utilization:.1f}%')
    with col2:
        st.metric('⏱️ Active Time', f'{active_time:.1f} min')
    with col3:
        st.metric('⏸️ Idle Time', f'{idle_time:.1f} min')
    with col4:
        st.metric('🕒 Total Time', f'{total_time:.1f} min')


def _render_activity_frequency(loco_data: pd.DataFrame) -> None:
    """Render activity frequency bar chart."""
    activity_counts = {
        'Moving': 0,
        'Coupling': 0,
        'Decoupling': 0,
        'Brake Test': 0,
        'Inspection': 0,
        'Shunting Prep': 0,
    }

    for _, row in loco_data.iterrows():
        event_type = row.get('event_type', '')

        if event_type == 'MOVING':
            activity_counts['Moving'] += 1
        elif 'COUPLING' in event_type:
            activity_counts['Coupling'] += 1
        elif 'DECOUPLING' in event_type:
            activity_counts['Decoupling'] += 1
        elif event_type == 'BRAKE_TEST':
            activity_counts['Brake Test'] += 1
        elif event_type == 'INSPECTION':
            activity_counts['Inspection'] += 1
        elif event_type == 'SHUNTING_PREP':
            activity_counts['Shunting Prep'] += 1

    activity_counts = {k: v for k, v in activity_counts.items() if v > 0}

    if not activity_counts:
        st.info('No activity data available')
        return

    df = pd.DataFrame(list(activity_counts.items()), columns=['Activity', 'Count'])
    colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#f1c40f']

    fig = px.bar(
        df, x='Activity', y='Count', title='Activity Frequency', color='Activity', color_discrete_sequence=colors
    )
    fig.update_traces(text=df['Count'], textposition='outside')
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def _render_idle_time_analysis(loco_data: pd.DataFrame) -> None:
    """Render idle time analysis."""
    loco_data = loco_data.sort_values('timestamp')

    # Find idle periods
    idle_periods = []
    for _, row in loco_data.iterrows():
        event_type = row.get('event_type', '')
        if event_type in ['PARKING', 'ALLOCATED']:
            duration = row.get('duration_min', 0) or 0
            if duration > 0:
                idle_periods.append({'start': row.get('timestamp', 0), 'duration': duration, 'type': event_type})

    if not idle_periods:
        st.info('✅ No significant idle periods detected')
        return

    col1, col2 = st.columns(2)

    with col1:
        # Metrics
        total_idle = sum(p['duration'] for p in idle_periods)
        avg_idle = total_idle / len(idle_periods) if idle_periods else 0
        max_idle = max(p['duration'] for p in idle_periods) if idle_periods else 0

        st.metric('Total Idle Periods', len(idle_periods))
        st.metric('Total Idle Time', f'{total_idle:.1f} min')
        st.metric('Average Idle Duration', f'{avg_idle:.1f} min')
        st.metric('Longest Idle Period', f'{max_idle:.1f} min')

    with col2:
        # Top 5 longest idle periods
        st.markdown('**Top 5 Longest Idle Periods:**')
        sorted_periods = sorted(idle_periods, key=lambda x: x['duration'], reverse=True)[:5]
        for i, period in enumerate(sorted_periods, 1):
            st.write(f'{i}. {period["duration"]:.1f} min at t={period["start"]:.0f} ({period["type"]})')


def _render_comparison_view(loco_journey: pd.DataFrame, locos: list[str]) -> None:  # pylint: disable=too-many-locals
    """Render comparison view for multiple locomotives.

    Note: Multiple local variables needed for locomotive comparison analysis.
    """
    st.subheader('🔀 Locomotive Comparison')

    selected_locos = st.multiselect('Select locomotives to compare:', locos, default=locos[: min(3, len(locos))])

    if len(selected_locos) < 2:
        st.warning('⚠️ Please select at least 2 locomotives to compare')
        return

    # Multi-locomotive timeline
    st.subheader('📊 Combined Timeline')
    filtered_data = loco_journey[loco_journey['locomotive_id'].isin(selected_locos)]
    _render_multi_loco_timeline(filtered_data)

    st.markdown('---')

    # Comparison metrics
    comparison_data = []
    for loco_id in selected_locos:
        loco_data = loco_journey[loco_journey['locomotive_id'] == loco_id]
        active_time = idle_time = moving_count = coupling_count = decoupling_count = 0

        for _, row in loco_data.iterrows():
            event_type = row.get('event_type', '')
            duration = row.get('duration_min', 0) or 0

            if event_type in [
                'MOVING',
                'COUPLING_STARTED',
                'DECOUPLING_STARTED',
                'BRAKE_TEST',
                'INSPECTION',
                'SHUNTING_PREP',
            ]:
                active_time += duration
            elif event_type in ['PARKING', 'ALLOCATED']:
                idle_time += duration

            if event_type == 'MOVING':
                moving_count += 1
            elif 'COUPLING' in event_type and 'STARTED' in event_type:
                coupling_count += 1
            elif 'DECOUPLING' in event_type and 'STARTED' in event_type:
                decoupling_count += 1

        total_time = active_time + idle_time
        utilization = (active_time / total_time * 100) if total_time > 0 else 0

        comparison_data.append(
            {
                'Locomotive': loco_id,
                'Utilization (%)': f'{utilization:.1f}',
                'Active Time (min)': f'{active_time:.1f}',
                'Idle Time (min)': f'{idle_time:.1f}',
                'Movements': moving_count,
                'Couplings': coupling_count,
                'Decouplings': decoupling_count,
                'Total Operations': moving_count + coupling_count + decoupling_count,
                '_util_num': utilization,
                '_ops_num': moving_count + coupling_count + decoupling_count,
            }
        )

    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison.drop(columns=['_util_num', '_ops_num']), use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            df_comparison,
            x='Locomotive',
            y='_util_num',
            title='Utilization Comparison',
            labels={'_util_num': 'Utilization (%)'},
            color_discrete_sequence=['#3498db'],
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(
            df_comparison,
            x='Locomotive',
            y='_ops_num',
            title='Operations Comparison',
            labels={'_ops_num': 'Total Operations'},
            color_discrete_sequence=['#2ecc71'],
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_multi_loco_timeline(loco_journey: pd.DataFrame) -> None:
    """Render timeline for multiple locomotives."""
    activity_colors = {
        'MOVING': '#3498db',
        'COUPLING': '#2ecc71',
        'DECOUPLING': '#e74c3c',
        'BRAKE_TEST': '#f39c12',
        'INSPECTION': '#9b59b6',
        'SHUNTING_PREP': '#f1c40f',
        'PARKING': '#95a5a6',
        'ALLOCATED': '#34495e',
    }

    segments = []
    for _, row in loco_journey.iterrows():
        loco_id = row.get('locomotive_id', '')
        event_type = row.get('event_type', '')
        timestamp = row.get('timestamp', 0)
        duration = row.get('duration_min', 0) or 0

        if duration <= 0:
            continue

        if event_type == 'MOVING':
            state = 'MOVING'
        elif 'COUPLING' in event_type:
            state = 'COUPLING'
        elif 'DECOUPLING' in event_type:
            state = 'DECOUPLING'
        elif event_type in ['BRAKE_TEST', 'INSPECTION', 'SHUNTING_PREP', 'PARKING', 'ALLOCATED']:
            state = event_type
        else:
            continue

        segments.append({'Locomotive': loco_id, 'State': state, 'Start': timestamp, 'Duration': duration})

    if not segments:
        st.info('No timeline data to display')
        return

    df_segments = pd.DataFrame(segments)
    fig = go.Figure()

    for state, color in activity_colors.items():
        state_data = df_segments[df_segments['State'] == state]
        if not state_data.empty:
            fig.add_trace(
                go.Bar(
                    y=state_data['Locomotive'],
                    x=state_data['Duration'],
                    base=state_data['Start'],
                    orientation='h',
                    name=state,
                    marker_color=color,
                    hovertemplate=(
                        '<b>%{fullData.name}</b><br>Start: %{base:.1f} min<br>Duration: %{x:.1f} min<extra></extra>'
                    ),
                )
            )

    fig.update_layout(
        title='Multi-Locomotive Activity Timeline',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Locomotive',
        barmode='stack',
        height=max(250, len(df_segments['Locomotive'].unique()) * 60),
        showlegend=True,
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f'Timeline shows {len(segments)} activity segments across {len(df_segments["Locomotive"].unique())} locomotives'
    )
