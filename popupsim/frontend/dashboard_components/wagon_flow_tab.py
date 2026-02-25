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

    # Section 1: Wagon Status Distribution
    st.subheader('Wagon Status Distribution (Final State)')
    _render_status_distribution(data)

    st.markdown('---')

    # Section 2: Location Changes
    st.subheader('Location Changes')
    _render_location_changes(data)

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

    # Get all wagon IDs from resource_states (includes rejected wagons)
    resource_states = data.get('resource_states')
    if resource_states is not None and not resource_states.empty:
        all_wagon_ids_from_states = sorted(
            resource_states[resource_states['resource_type'] == 'wagon']['resource_id'].unique(),
            key=lambda x: int(x[1:]) if x[1:].isdigit() else 0,
        )
    else:
        all_wagon_ids_from_states = sorted(
            wagon_journey['wagon_id'].unique(), key=lambda x: int(x[1:]) if x[1:].isdigit() else 0
        )

    # Add "All Wagons" option
    wagon_options = ['All Wagons', *all_wagon_ids_from_states]

    selected_wagons = st.multiselect(
        'Select wagons:', options=wagon_options, default=[], placeholder='Choose wagon IDs to track...'
    )

    if selected_wagons:
        # If "All Wagons" is selected, use all wagon IDs
        wagons_to_display = all_wagon_ids_from_states if 'All Wagons' in selected_wagons else selected_wagons

        _render_wagon_gantt_dual_stream(data, wagons_to_display, key='track_specific')


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


def _render_wagon_gantt_dual_stream(  # noqa: C901, PLR0912, PLR0915  # pylint: disable=too-many-locals,too-many-branches,too-many-statements,too-many-nested-blocks
    data: dict[str, Any], wagon_ids: list[str], key: str = 'default'
) -> None:
    """Render Gantt chart using dual-stream data (states and processes)."""
    resource_states = data.get('resource_states')
    resource_processes = data.get('resource_processes')
    resource_locations = data.get('resource_locations')

    if resource_states is None or resource_states.empty:
        st.info('No state data available')
        return

    # Filter for selected wagons
    wagon_states = resource_states[
        (resource_states['resource_type'] == 'wagon') & (resource_states['resource_id'].isin(wagon_ids))
    ].copy()

    # Merge with locations to get track information
    if resource_locations is not None and not resource_locations.empty:
        wagon_locations = resource_locations[
            (resource_locations['resource_type'] == 'wagon') & (resource_locations['resource_id'].isin(wagon_ids))
        ].copy()
        # Merge states with locations on timestamp and resource_id
        wagon_states = wagon_states.merge(
            wagon_locations[['timestamp', 'resource_id', 'location', 'route_path']],
            on=['timestamp', 'resource_id'],
            how='left',
        )
        # Fill missing locations with 'Unknown'
        wagon_states['location'] = wagon_states['location'].fillna('Unknown')
        wagon_states['route_path'] = wagon_states['route_path'].fillna('')

    wagon_processes = pd.DataFrame()
    if resource_processes is not None and not resource_processes.empty:
        wagon_processes = resource_processes[
            (resource_processes['resource_type'] == 'wagon') & (resource_processes['resource_id'].isin(wagon_ids))
        ].copy()

    # Activity colors
    activity_colors = {
        'waiting': '#FFA500',  # Orange
        'moving': '#9467BD',  # Purple
        'coupling': '#2CA02C',  # Green
        'decoupling': '#D62728',  # Red
        'retrofitting': '#1F77B4',  # Blue
        'parked': '#7F7F7F',  # Gray
        'rejected': '#FF0000',  # Bright Red
    }

    # Build segments for each wagon
    segments = []

    for wagon_id in wagon_ids:
        wagon_state_data = wagon_states[wagon_states['resource_id'] == wagon_id].sort_values('timestamp')
        wagon_process_data = (
            wagon_processes[wagon_processes['resource_id'] == wagon_id].sort_values('timestamp')
            if not wagon_processes.empty
            else pd.DataFrame()
        )

        if wagon_state_data.empty:
            continue

        # Check if wagon is rejected - if so, show only rejected state
        is_rejected = (wagon_state_data['state'] == 'rejected').any()
        if is_rejected:
            # Find rejection event
            rejection_row = wagon_state_data[wagon_state_data['state'] == 'rejected'].iloc[0]
            rejection_time = rejection_row['timestamp']
            rejection_reason = rejection_row.get('rejection_reason', 'Unknown')
            location = rejection_row.get('location', 'Unknown')

            # Show rejected for entire simulation
            sim_end = wagon_states['timestamp'].max()
            duration = max(10, sim_end - rejection_time)  # Minimum 10 minutes for visibility
            segments.append(
                {
                    'wagon_id': wagon_id,
                    'activity': 'rejected',
                    'start': rejection_time,
                    'duration': duration,
                    'location': location,
                    'label': f'❌ Rejected: {rejection_reason}',
                }
            )
            continue

        # Process state changes to create segments
        for i in range(len(wagon_state_data) - 1):
            row = wagon_state_data.iloc[i]
            next_row = wagon_state_data.iloc[i + 1]

            start_time = row['timestamp']
            end_time = next_row['timestamp']
            duration = end_time - start_time

            if duration <= 0:
                continue

            state = row['state']
            location = row.get('location', 'Unknown')

            # Map state to activity
            if state == 'moving':
                activity = 'moving'
                route_path = row.get('route_path', '')
                if route_path and '|' in route_path:
                    waypoints = route_path.split('|')
                    label = f'Moving {waypoints[0]}→{waypoints[-1]}'
                else:
                    label = f'Moving from {location}'
            elif state == 'parked':
                activity = 'parked'
                label = f'Parked @ {location}'
            elif state == 'rejected':
                activity = 'rejected'
                rejection_reason = row.get('rejection_reason', 'Unknown')
                label = f'❌ Rejected: {rejection_reason}'
            elif state in ('in_workshop', 'retrofitted'):
                activity = 'retrofitting'
                label = f'Retrofitting @ {location}'
            else:
                activity = 'waiting'
                label = f'Waiting @ {location}'

            segments.append(
                {
                    'wagon_id': wagon_id,
                    'activity': activity,
                    'start': start_time,
                    'duration': duration,
                    'location': location,
                    'label': label,
                }
            )

        # Add final segment (parked or last state until simulation end)
        if len(wagon_state_data) > 0:
            last_row = wagon_state_data.iloc[-1]
            last_state = last_row['state']
            last_location = last_row.get('location', 'Unknown')
            last_time = last_row['timestamp']

            # Find simulation end time from all wagon data
            sim_end = wagon_states['timestamp'].max()
            final_duration = max(10, sim_end - last_time)  # Minimum 10 minutes for visibility

            if final_duration > 0:
                if last_state == 'parked':
                    activity = 'parked'
                    label = f'Parked @ {last_location}'
                elif last_state == 'rejected':
                    activity = 'rejected'
                    rejection_reason = last_row.get('rejection_reason', 'Unknown')
                    label = f'❌ Rejected: {rejection_reason}'
                else:
                    activity = 'waiting'
                    label = f'Waiting @ {last_location}'

                segments.append(
                    {
                        'wagon_id': wagon_id,
                        'activity': activity,
                        'start': last_time,
                        'duration': final_duration,
                        'location': last_location,
                        'label': label,
                    }
                )

        # Add process events (coupling/decoupling) from resource_processes
        if not wagon_process_data.empty:
            # Group started/completed pairs to calculate real durations
            process_events = {}
            for _, proc_row in wagon_process_data.iterrows():
                process_state = str(proc_row['process_state']).lower()
                timestamp = proc_row['timestamp']
                location = proc_row.get('location', 'Unknown')

                # Determine activity type
                if 'decoupling' in process_state:
                    activity = 'decoupling'
                elif 'coupling' in process_state:
                    activity = 'coupling'
                else:
                    continue

                # Track started events
                if 'started' in process_state:
                    key = f'{activity}_{location}_{timestamp}'  # Use timestamp to make key unique
                    process_events[key] = {'activity': activity, 'start': timestamp, 'location': location}
                # Match with completed events
                elif 'completed' in process_state:
                    # Find matching started event (same activity and location, most recent)
                    matching_keys = [k for k in process_events if k.startswith(f'{activity}_{location}_')]
                    if matching_keys:
                        # Use the most recent started event
                        key = max(matching_keys, key=lambda k: float(k.split('_')[-1]))
                        start_event = process_events[key]
                        duration = timestamp - start_event['start']
                        # Show coupling/decoupling with actual duration (no minimum)
                        if duration > 0:  # Only show if duration is positive
                            label = f'{activity.capitalize()} @ {location}'
                            segments.append(
                                {
                                    'wagon_id': wagon_id,
                                    'activity': activity,
                                    'start': start_event['start'],
                                    'duration': duration,
                                    'location': location,
                                    'label': label,
                                }
                            )
                        del process_events[key]

    if not segments:
        st.info('No activity data to display')
        return

    df_segments = pd.DataFrame(segments)

    # Create Gantt chart
    fig = go.Figure()

    for activity, color in activity_colors.items():
        activity_data = df_segments[df_segments['activity'] == activity]
        if not activity_data.empty:
            fig.add_trace(
                go.Bar(
                    y=activity_data['wagon_id'],
                    x=activity_data['duration'],
                    base=activity_data['start'],
                    orientation='h',
                    name=activity.capitalize(),
                    marker_color=color,
                    hovertemplate=(
                        '<b>%{y}</b><br>'
                        'Activity: %{customdata[0]}<br>'
                        'Location: %{customdata[1]}<br>'
                        'Start: %{base:.1f} min<br>'
                        'Duration: %{x:.1f} min<extra></extra>'
                    ),
                    customdata=activity_data[['label', 'location']].values,
                )
            )

    fig.update_layout(
        title='Wagon Activities Over Time',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Wagon ID',
        yaxis={'autorange': 'reversed', 'categoryorder': 'array', 'categoryarray': wagon_ids},
        barmode='overlay',  # Changed from 'stack' to 'overlay' so coupling/decoupling shows on top
        height=max(200, len(wagon_ids) * 30),  # Minimum 200px height, 30px per wagon
        showlegend=True,
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'left', 'x': 0},
        margin={'t': 100, 'b': 50},
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f'wagon_gantt_{key}',
        config={
            'displayModeBar': True,
            'toImageButtonOptions': {'format': 'png', 'filename': 'wagon_activities', 'height': 800, 'width': 1400},
        },
    )
    st.caption(
        f'Showing {len(wagon_ids)} wagons. Colors indicate activity type: '
        'waiting, moving, coupling, decoupling, retrofitting, parked, rejected.'
    )


def _render_location_changes(  # noqa: C901, PLR0912  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    data: dict[str, Any],
) -> None:
    """Render location changes plot with route waypoints and coupler type toggle."""
    resource_locations = data.get('resource_locations')

    if resource_locations is None or resource_locations.empty:
        st.info('No location data available')
        return

    # Filter for wagons only
    wagon_locations = resource_locations[resource_locations['resource_type'] == 'wagon'].copy()

    if wagon_locations.empty:
        st.info('No wagon location data available')
        return

    # Coupler type toggle
    show_coupler = st.radio('Show coupler type on locations:', ['No', 'Yes'], horizontal=True) == 'Yes'

    # Select wagon
    wagon_ids = sorted(wagon_locations['resource_id'].unique())
    selected_wagon = st.selectbox('Select wagon:', wagon_ids, key='location_wagon_select')

    if not selected_wagon:
        return

    wagon_data = wagon_locations[wagon_locations['resource_id'] == selected_wagon].sort_values('timestamp')

    if wagon_data.empty:
        st.info(f'No location data for {selected_wagon}')
        return

    # Determine coupler type changes from resource_states
    if show_coupler:
        resource_states = data.get('resource_states')
        if resource_states is not None:
            retrofit_events = resource_states[
                (resource_states['resource_id'] == selected_wagon) & (resource_states['state'] == 'retrofitted')
            ]
            retrofit_time = retrofit_events['timestamp'].min() if not retrofit_events.empty else float('inf')

    # Build location plot data with waypoints
    plot_data = []

    for _idx, row in wagon_data.iterrows():
        timestamp = row['timestamp']
        location = row['location']
        route_path = row.get('route_path', '')

        # Determine coupler type
        coupler_text = (' (DAC)' if timestamp >= retrofit_time else ' (SCREW)') if show_coupler else ''

        # If route_path exists, add waypoints
        if route_path and isinstance(route_path, str) and '|' in route_path:
            waypoints = route_path.split('|')
            # Find next location to calculate duration
            next_rows = wagon_data[wagon_data['timestamp'] > timestamp]
            if not next_rows.empty:
                next_timestamp = next_rows.iloc[0]['timestamp']
                duration = next_timestamp - timestamp

                # Add all waypoints with distributed times
                for i, waypoint in enumerate(waypoints):
                    waypoint_time = (
                        timestamp + (i * duration / (len(waypoints) - 1)) if len(waypoints) > 1 else timestamp
                    )
                    plot_data.append(
                        {
                            'timestamp': waypoint_time,
                            'location': waypoint,
                            'is_waypoint': i not in (0, len(waypoints) - 1),
                            'coupler_text': coupler_text if i in (0, len(waypoints) - 1) else '',
                        }
                    )
            else:
                # Last location, just add it
                plot_data.append(
                    {'timestamp': timestamp, 'location': location, 'is_waypoint': False, 'coupler_text': coupler_text}
                )
        else:
            # No route path, just add location
            plot_data.append(
                {'timestamp': timestamp, 'location': location, 'is_waypoint': False, 'coupler_text': coupler_text}
            )

    if not plot_data:
        st.info('No location changes to display')
        return

    plot_df = pd.DataFrame(plot_data)

    # Create scatter plot
    fig = go.Figure()

    # Add line connecting all points
    fig.add_trace(
        go.Scatter(
            x=plot_df['timestamp'],
            y=plot_df['location'],
            mode='lines',
            name='Path',
            line={'color': 'lightblue', 'width': 2},
            showlegend=False,
        )
    )

    # Regular locations (start/end)
    regular = plot_df[~plot_df['is_waypoint']]
    fig.add_trace(
        go.Scatter(
            x=regular['timestamp'],
            y=regular['location'],
            mode='markers+text',
            name='Locations',
            marker={'size': 10, 'color': 'blue'},
            text=regular['coupler_text'],
            textposition='top center',
            textfont={'size': 10, 'color': 'red'},
        )
    )

    # Waypoints
    waypoints = plot_df[plot_df['is_waypoint']]
    if not waypoints.empty:
        fig.add_trace(
            go.Scatter(
                x=waypoints['timestamp'],
                y=waypoints['location'],
                mode='markers',
                name='Waypoints',
                marker={'size': 6, 'color': 'orange', 'symbol': 'diamond'},
            )
        )

    fig.update_layout(
        title=f'Location Changes for {selected_wagon}',
        xaxis_title='Time (minutes)',
        yaxis_title='Location',
        height=400,
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_status_distribution(data: dict[str, Any]) -> None:
    """Render wagon status distribution with improved visualizations."""
    metrics = data.get('metrics', {})
    rejected_wagons = data.get('rejected_wagons')

    total_wagons = metrics.get('total_wagons', 0)
    parked = metrics.get('wagons_parked', 0)
    rejected = metrics.get('wagons_rejected', 0)
    in_process = metrics.get('wagons_in_process', 0)

    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Total Wagons', total_wagons)
    with col2:
        st.metric('✅ Parked', parked, delta=f'{(parked / total_wagons * 100):.1f}%' if total_wagons > 0 else '0%')
    with col3:
        st.metric('🔄 In Process', in_process)
    with col4:
        st.metric(
            '❌ Rejected',
            rejected,
            delta=f'{(rejected / total_wagons * 100):.1f}%' if total_wagons > 0 else '0%',
            delta_color='inverse',
        )

    # Pie chart for status distribution
    col1, col2 = st.columns([1, 1])

    with col1:
        if total_wagons > 0:
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
        wagon_history = journey_df[journey_df['wagon_id'] == selected_wagon].sort_values('timestamp')

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
