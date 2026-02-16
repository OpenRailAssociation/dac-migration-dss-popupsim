"""Wagon flow tab - visualizes wagon journeys through the system."""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_wagon_flow_tab(data: dict[str, Any]) -> None:
    """Render wagon flow analysis tab."""
    st.header('🚃 Wagon Flow Analysis')

    wagon_journey = data.get('wagon_journey')

    if wagon_journey is None or wagon_journey.empty:
        st.warning('⚠️ No wagon journey data available')
        return

    # CSV Export
    if st.button('📥 Export Wagon Journey CSV'):
        csv = wagon_journey.to_csv(index=False)
        st.download_button('Download wagon_journey.csv', csv, 'wagon_journey.csv', 'text/csv')

    # Section 1: Wagon Journeys Over Time
    st.subheader('Wagon Journeys Over Time')
    all_wagon_ids = sorted(wagon_journey['wagon_id'].unique(), key=lambda x: (int(x[1:]) if x[1:].isdigit() else 0))
    _render_wagon_gantt(wagon_journey, all_wagon_ids)

    st.markdown('---')

    # Section 2: Wagon Status Distribution
    st.subheader('Wagon Status Distribution (Final State)')
    _render_status_distribution(data)

    st.markdown('---')

    # Section 3: Processing Time Analysis
    st.subheader('Processing Time Analysis')
    _render_processing_time_analysis(wagon_journey)

    st.markdown('---')

    # Section 4: Throughput Over Time
    st.subheader('Throughput Over Time')
    _render_throughput_over_time(wagon_journey)

    st.markdown('---')

    # Section 5: Train Arrival Analysis
    st.subheader('Train Arrival Analysis')
    _render_train_analysis(wagon_journey, data)

    st.markdown('---')

    # Section 6: Wagon Journey History
    st.subheader('Wagon Journey History')
    _render_wagon_journey_history(wagon_journey)

    st.markdown('---')

    # Section 7: Track Specific Wagons
    st.subheader('Track Specific Wagons')
    st.write('Select specific wagons to analyze their journey in detail:')

    all_wagon_ids = sorted(wagon_journey['wagon_id'].unique(), key=lambda x: (int(x[1:]) if x[1:].isdigit() else 0))
    selected_wagons = st.multiselect(
        'Select wagons:', options=all_wagon_ids, default=[], placeholder='Choose wagon IDs to track...'
    )

    if selected_wagons:
        filtered_journey = wagon_journey[wagon_journey['wagon_id'].isin(selected_wagons)]
        selected_sorted = sorted(selected_wagons, key=lambda x: (int(x[1:]) if x[1:].isdigit() else 0))
        _render_wagon_gantt(filtered_journey, selected_sorted)


def _classify_wagon_segment(row: pd.Series, next_row: pd.Series) -> dict | None:
    """Classify a wagon segment and return its properties."""
    event = row['event']
    track = row['track_id']
    status = row['status']
    duration = next_row['timestamp'] - row['timestamp']

    if duration <= 0:
        return None

    # Determine classification based on event and status
    if 'COUPLING' in event:
        color_key, label, text = 'BATCH_COUPLING', f'Batch Coupling @ {track}', ''
    elif 'DECOUPLING' in event:
        color_key, label, text = 'BATCH_DECOUPLING', f'Batch Decoupling @ {track}', ''
    elif 'RETROFIT' in event and 'STARTED' in event:
        color_key, label = 'RETROFITTING', f'⚙️ RETROFITTING @ {track}'
        text = '⚙️' if duration > 20 else ''
    elif status == 'COMPLETED':
        color_key, label, text = 'COMPLETED', f'Completed @ {track}', ''
    elif status == 'PARKED':
        color_key, label, text = 'PARKED', f'Parked @ {track}', ''
    elif status == 'REJECTED':
        rejection_reason = row.get('rejection_reason', 'Unknown')
        rejection_desc = row.get('rejection_description', '')
        label = (
            f'REJECTED: {rejection_reason} - {rejection_desc}' if rejection_desc else f'REJECTED: {rejection_reason}'
        )
        color_key, text = 'REJECTED', '❌ REJECTED' if duration > 50 else '❌'
    elif status == 'WAITING':
        color_key, label, text = 'WAITING', f'Waiting @ {track}', ''
    else:
        color_key, label, text = 'ARRIVED', f'{status} @ {track}', ''

    return {'color_key': color_key, 'label': label, 'text': text}


def _classify_final_segment(last_row: pd.Series, duration: float) -> dict:
    """Classify the final segment of a wagon journey."""
    status = last_row['status']
    track = last_row['track_id']
    event = last_row['event']

    if status == 'PARKED':
        return {'color_key': 'PARKED', 'label': f'Parked @ {track}', 'text': ''}
    if status == 'COMPLETED':
        return {'color_key': 'COMPLETED', 'label': f'Completed @ {track}', 'text': ''}
    if status == 'REJECTED' or event == 'REJECTED':
        rejection_reason = last_row.get('rejection_reason', 'Unknown')
        rejection_desc = last_row.get('rejection_description', '')
        label = (
            f'REJECTED: {rejection_reason} - {rejection_desc}' if rejection_desc else f'REJECTED: {rejection_reason}'
        )
        return {'color_key': 'REJECTED', 'label': label, 'text': '❌ REJECTED' if duration > 50 else '❌'}
    return {'color_key': 'ARRIVED', 'label': f'{status} @ {track}', 'text': ''}


def _process_wagon_segments(wagon_data: pd.DataFrame, wagon_id: str, journey_df: pd.DataFrame) -> list[dict]:
    """Process all segments for a single wagon."""
    segments = []

    for i in range(len(wagon_data) - 1):
        row = wagon_data.iloc[i]
        next_row = wagon_data.iloc[i + 1]

        classification = _classify_wagon_segment(row, next_row)
        if classification is None:
            continue

        segments.append(
            {
                'Wagon': wagon_id,
                'State': classification['color_key'],
                'Start': row['timestamp'],
                'Duration': next_row['timestamp'] - row['timestamp'],
                'Label': classification['label'],
                'Track': row['track_id'],
                'Text': classification['text'],
            }
        )

    # Add final segment
    if len(wagon_data) > 0:
        last_row = wagon_data.iloc[-1]
        max_time = journey_df['timestamp'].max()
        duration = max(10, max_time - last_row['timestamp'])

        classification = _classify_final_segment(last_row, duration)
        segments.append(
            {
                'Wagon': wagon_id,
                'State': classification['color_key'],
                'Start': last_row['timestamp'],
                'Duration': duration,
                'Label': classification['label'],
                'Track': last_row['track_id'],
                'Text': classification['text'],
            }
        )

    return segments


def _render_wagon_gantt(journey_df, wagon_ids: list[str]) -> None:
    """Render interactive Gantt chart showing wagon journeys with Plotly."""
    with st.spinner('Generating wagon journey Gantt chart...'):
        event_colors = {
            'WAITING': '#f39c12',
            'BATCH_COUPLING': '#2ecc71',
            'BATCH_DECOUPLING': '#e67e22',
            'RETROFITTING': '#3498db',
            'COMPLETED': '#9b59b6',
            'PARKED': '#34495e',
            'REJECTED': '#d62728',
            'ARRIVED': '#95a5a6',
        }

    # Build segments
    segments = []
    for wagon_id in wagon_ids:
        wagon_data = journey_df[journey_df['wagon_id'] == wagon_id].sort_values('timestamp')
        if wagon_data.empty:
            continue

        # Check if wagon is rejected - if so, skip ARRIVED events
        is_rejected = (wagon_data['status'] == 'REJECTED').any()
        if is_rejected:
            wagon_data = wagon_data[wagon_data['event'] != 'ARRIVED']

        wagon_segments = _process_wagon_segments(wagon_data, wagon_id, journey_df)
        segments.extend(wagon_segments)

    if not segments:
        st.info('No wagon journey data to display')
        return

    df_segments = pd.DataFrame(segments)
    fig = go.Figure()

    for state, color in event_colors.items():
        state_data = df_segments[df_segments['State'] == state]
        if not state_data.empty:
            fig.add_trace(
                go.Bar(
                    y=state_data['Wagon'],
                    x=state_data['Duration'],
                    base=state_data['Start'],
                    orientation='h',
                    name=state.replace('_', ' ').title(),
                    marker_color=color,
                    text=state_data['Text'],
                    textposition='inside',
                    textfont={'color': 'white', 'size': 10},
                    hovertemplate=(
                        '<b>%{y}</b><br>%{customdata}<br>'
                        'Start: %{base:.1f} min<br>'
                        'Duration: %{x:.1f} min<extra></extra>'
                    ),
                    customdata=state_data['Label'],
                )
            )

    fig.update_layout(
        title='Wagon Journeys Over Time',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Wagon ID',
        yaxis={'autorange': 'reversed', 'categoryorder': 'array', 'categoryarray': wagon_ids},
        barmode='stack',
        height=max(400, len(wagon_ids) * 25),
        showlegend=True,
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            'displayModeBar': True,
            'toImageButtonOptions': {'format': 'png', 'filename': 'wagon_journeys', 'height': 800, 'width': 1400},
        },
    )
    st.caption(
        f'Showing {len(wagon_ids)} wagons. ⚙️ = Retrofitting. ❌ = Rejected. Coupling/Decoupling = Batch rake formation.'
    )


def _render_status_distribution(data: dict[str, Any]) -> None:
    """Render wagon status distribution with improved visualizations."""
    metrics = data.get('metrics', {})
    rejected_wagons = data.get('rejected_wagons')

    total_arrived = metrics.get('wagons_arrived', 0)
    parked = metrics.get('wagons_parked', 0)
    rejected = metrics.get('wagons_rejected', 0)
    in_process = total_arrived - parked - rejected

    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Total Arrived', total_arrived)
    with col2:
        st.metric('✅ Parked', parked, delta=f'{(parked / total_arrived * 100):.1f}%' if total_arrived > 0 else '0%')
    with col3:
        st.metric('🔄 In Process', in_process)
    with col4:
        st.metric(
            '❌ Rejected',
            rejected,
            delta=f'{(rejected / total_arrived * 100):.1f}%' if total_arrived > 0 else '0%',
            delta_color='inverse',
        )

    # Pie chart for status distribution
    col1, col2 = st.columns([1, 1])

    with col1:
        if total_arrived > 0:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=['Parked', 'In Process', 'Rejected'],
                        values=[parked, in_process, rejected],
                        marker_colors=['#2ecc71', '#3498db', '#e74c3c'],
                        hole=0.4,
                    )
                ]
            )
            fig.update_layout(title='Wagon Status Distribution', height=300)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Rejection breakdown
        if rejected_wagons is not None and not rejected_wagons.empty:
            rejection_counts = rejected_wagons['rejection_type'].value_counts()
            fig = go.Figure(data=[go.Bar(x=rejection_counts.index, y=rejection_counts.values, marker_color='#e74c3c')])
            fig.update_layout(title='Rejection Reasons', xaxis_title='Reason', yaxis_title='Count', height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('No rejections recorded')


def _render_processing_time_analysis(journey_df: pd.DataFrame) -> None:
    """Render processing time analysis."""
    # Calculate time spent in each status per wagon
    time_by_status = []
    for wagon_id in journey_df['wagon_id'].unique():
        wagon_data = journey_df[journey_df['wagon_id'] == wagon_id].sort_values('timestamp')
        for i in range(len(wagon_data) - 1):
            status = wagon_data.iloc[i]['status']
            duration = wagon_data.iloc[i + 1]['timestamp'] - wagon_data.iloc[i]['timestamp']
            time_by_status.append({'status': status, 'duration': duration, 'wagon_id': wagon_id})

    if not time_by_status:
        st.info('No processing time data available')
        return

    time_df = pd.DataFrame(time_by_status)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Average time by status
        avg_time = time_df.groupby('status')['duration'].mean().sort_values(ascending=False)
        fig = go.Figure(go.Bar(x=avg_time.values, y=avg_time.index, orientation='h'))
        fig.update_layout(title='Average Time by Status', xaxis_title='Minutes', yaxis_title='Status', height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Summary statistics
        summary = time_df.groupby('status')['duration'].agg(['mean', 'min', 'max']).round(1)
        summary.columns = ['Avg (min)', 'Min (min)', 'Max (min)']
        st.dataframe(summary, use_container_width=True)


def _render_throughput_over_time(journey_df: pd.DataFrame) -> None:
    """Render throughput over time chart."""
    # Create time bins (e.g., hourly)
    max_time = journey_df['timestamp'].max()
    bin_size = max(60, max_time / 20)  # At least 60 min bins, or 20 bins total

    bins = list(range(0, int(max_time) + int(bin_size), int(bin_size)))

    # Count events by type in each bin
    arrived = []
    completed = []
    parked = []

    for i in range(len(bins) - 1):
        bin_start, bin_end = bins[i], bins[i + 1]
        bin_data = journey_df[(journey_df['timestamp'] >= bin_start) & (journey_df['timestamp'] < bin_end)]

        arrived.append(len(bin_data[bin_data['event'] == 'ARRIVED']['wagon_id'].unique()))
        completed.append(len(bin_data[bin_data['status'] == 'COMPLETED']))
        parked.append(len(bin_data[bin_data['event'] == 'PARKED']))

    bin_labels = [f'{bins[i]:.0f}' for i in range(len(bins) - 1)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bin_labels, y=arrived, name='Arrived', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=bin_labels, y=completed, name='Completed', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=bin_labels, y=parked, name='Parked', mode='lines+markers'))

    fig.update_layout(
        title='Wagon Throughput Over Time',
        xaxis_title='Time (minutes)',
        yaxis_title='Number of Wagons',
        height=400,
        hovermode='x unified',
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_train_analysis(journey_df: pd.DataFrame, data: dict[str, Any]) -> None:
    """Render train arrival analysis."""
    rejected_wagons = data.get('rejected_wagons')

    # Get train statistics
    train_stats = []
    for train_id, train_wagons in journey_df.groupby('train_id'):
        if not train_id:
            continue
        total_wagons = len(train_wagons['wagon_id'].unique())

        # Count rejections
        rejected_count = 0
        if rejected_wagons is not None and not rejected_wagons.empty:
            rejected_count = len(rejected_wagons[rejected_wagons['train_id'] == train_id])

        arrival_time = train_wagons['timestamp'].min()

        train_stats.append(
            {
                'Train ID': train_id,
                'Arrival Time': f'{arrival_time:.0f} min',
                'Total Wagons': total_wagons + rejected_count,
                'Accepted': total_wagons,
                'Rejected': rejected_count,
                'Rejection Rate': f'{(rejected_count / (total_wagons + rejected_count) * 100):.1f}%'
                if (total_wagons + rejected_count) > 0
                else '0%',
            }
        )

    if not train_stats:
        st.info('No train data available')
        return

    train_df = pd.DataFrame(train_stats)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.dataframe(train_df, use_container_width=True, hide_index=True)

    with col2:
        # Summary metrics
        total_trains = len(train_df)
        trains_with_rejections = len(train_df[train_df['Rejected'] > 0])
        st.metric('Total Trains', total_trains)
        st.metric('Trains with Rejections', trains_with_rejections)
        st.metric('Avg Wagons per Train', f'{train_df["Total Wagons"].mean():.1f}')


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
    # Calculate key metrics
    total_time = wagon_history['timestamp'].max() - wagon_history['timestamp'].min()

    # Calculate time in each status
    time_by_status = {}
    for i in range(len(wagon_history) - 1):
        status = wagon_history.iloc[i]['status']
        duration = wagon_history.iloc[i + 1]['timestamp'] - wagon_history.iloc[i]['timestamp']
        time_by_status[status] = time_by_status.get(status, 0) + duration

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Total Time', f'{total_time:.1f} min')
    with col2:
        waiting_time = time_by_status.get('WAITING', 0)
        st.metric('Waiting Time', f'{waiting_time:.1f} min')
    with col3:
        processing_time = time_by_status.get('PROCESSING', 0)
        st.metric('Processing Time', f'{processing_time:.1f} min')

    # Show status breakdown
    if time_by_status:
        status_df = pd.DataFrame(list(time_by_status.items()), columns=['Status', 'Time (min)'])
        status_df['Time (min)'] = status_df['Time (min)'].round(1)
        st.dataframe(status_df, use_container_width=True, hide_index=True)
