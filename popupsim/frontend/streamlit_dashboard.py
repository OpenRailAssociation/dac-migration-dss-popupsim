"""PopUpSim Streamlit Dashboard - Comprehensive post-simulation analysis."""

import contextlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title='PopUpSim Dashboard', layout='wide', page_icon='🚂')


def load_dashboard_data(output_dir: Path) -> dict[str, Any]:
    """Load all dashboard data files."""
    data: dict[str, Any] = {}

    # Load summary metrics JSON
    metrics_file = output_dir / 'summary_metrics.json'
    if metrics_file.exists():
        with open(metrics_file, encoding='utf-8') as f:
            data['metrics'] = json.load(f)

    # Load events CSV
    events_file = output_dir / 'events.csv'
    if events_file.exists():
        data['events'] = pd.read_csv(events_file)

    # Load process log
    process_log_file = output_dir / 'process.log'
    if process_log_file.exists():
        with contextlib.suppress(pd.errors.ParserError, pd.errors.EmptyDataError):
            data['process_log'] = pd.read_csv(process_log_file)

    # Load locomotive utilization
    loco_file = output_dir / 'locomotive_utilization.csv'
    if loco_file.exists():
        data['locomotive_util'] = pd.read_csv(loco_file)

    # Load workshop metrics
    workshop_file = output_dir / 'workshop_metrics.csv'
    if workshop_file.exists():
        data['workshop_metrics'] = pd.read_csv(workshop_file)

    # Load track capacity
    track_file = output_dir / 'track_capacity.csv'
    if track_file.exists():
        data['track_capacity'] = pd.read_csv(track_file)

    # Load rejected wagons
    rejected_file = output_dir / 'rejected_wagons.csv'
    if rejected_file.exists():
        data['rejected_wagons'] = pd.read_csv(rejected_file)

    # Load wagon locations
    locations_file = output_dir / 'wagon_locations.csv'
    if locations_file.exists():
        data['wagon_locations'] = pd.read_csv(locations_file)

    # Load wagon journey
    journey_file = output_dir / 'wagon_journey.csv'
    if journey_file.exists():
        data['wagon_journey'] = pd.read_csv(journey_file)

    return data


def render_header(data: dict[str, Any]) -> None:
    """Render dashboard header with simulation summary."""
    st.title('🚂 PopUpSim - Simulation Dashboard')

    if 'metrics' in data:
        metrics = data['metrics']
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_wagons = metrics.get('wagons_arrived', 0)
            st.metric('Wagons in train schedule', total_wagons)

        with col2:
            completed = metrics.get('retrofits_completed', 0)
            st.metric('Retrofitted', completed)

        with col3:
            completion_rate = (completed / total_wagons * 100) if total_wagons > 0 else 0
            st.metric('Completion Rate', f'{completion_rate:.1f}%')

        with col4:
            duration = metrics.get('simulation_duration_minutes', 0)
            st.metric('Workshops open for', f'{duration:.1f} min')

    st.markdown('---')


def render_overview_tab(data: dict[str, Any]) -> None:  # noqa: PLR0915
    """Render overview dashboard with KPI cards and charts."""
    st.header('📊 Overview Dashboard')

    if 'metrics' not in data:
        st.warning('⚠️ No metrics data available')
        return

    metrics = data['metrics']

    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        trains = metrics.get('trains_arrived', 0)
        wagons = metrics.get('wagons_arrived', 0)
        st.metric('Arrived trains / Overall wagons', f'{trains} / {wagons}')

    with col2:
        retrofitted = metrics.get('retrofits_completed', 0)
        rate = (retrofitted / wagons * 100) if wagons > 0 else 0
        st.metric('Retrofitted', f'{retrofitted} ({rate:.1f}%)')

    with col3:
        rejected = (
            len(data.get('rejected_wagons', []))
            if 'rejected_wagons' in data and not data['rejected_wagons'].empty
            else 0
        )
        st.metric('Rejected', rejected)

    with col4:
        workshop_util = metrics.get('workshop_utilization', 0)
        st.metric('Workshop Util.', f'{workshop_util:.1f}%')

    with col5:
        duration = metrics.get('simulation_duration_minutes', 0)
        st.metric('Workshops open for', f'{duration:.0f} min')

    st.markdown('---')
    st.subheader('Operational Dashboard')

    # Create three columns for the operational dashboard
    col1, col2, col3 = st.columns(3)

    with col1:
        # Wagon Flow Chart - include rejected count from rejected_wagons.csv
        rejected_count = (
            len(data.get('rejected_wagons', []))
            if 'rejected_wagons' in data and not data['rejected_wagons'].empty
            else metrics.get('wagons_rejected', 0)
        )
        wagon_flow_data = pd.DataFrame(
            {
                'Category': ['Arrived', 'Retrofitted', 'Rejected'],
                'Count': [
                    metrics.get('wagons_arrived', 0),
                    metrics.get('retrofits_completed', 0),
                    rejected_count,
                ],
            }
        )
        st.markdown('**Wagon Flow**')
        st.bar_chart(wagon_flow_data.set_index('Category'), height=300)

    with col2:
        # Locomotive Activity Breakdown
        if 'locomotive_util' in data and not data['locomotive_util'].empty:
            loco_df = data['locomotive_util'][
                ['locomotive_id', 'moving_percent', 'parking_percent', 'coupling_percent', 'decoupling_percent']
            ]
            loco_df = loco_df.set_index('locomotive_id')
            st.markdown('**Locomotive Activity Breakdown**')
            st.bar_chart(loco_df, height=300)
        else:
            st.markdown('**Locomotive Activity Breakdown**')
            st.info('No locomotive data available')

    with col3:
        # Workshop Bay Utilization (overall + per workshop + per bay)
        if 'workshop_metrics' in data and not data['workshop_metrics'].empty:
            workshop_df = data['workshop_metrics']
            st.markdown('**Workshop Bay Utilization**')

            # Create figure
            fig, ax = plt.subplots(figsize=(6, 4))

            # Define colors for workshops
            colors = {
                'WS_01': '#1f77b4',
                'WS_02': '#ff7f0e',
                'WS_03': '#2ca02c',
                'WS_04': '#d62728',
                'Overall': '#9467bd',
            }

            # Prepare data
            labels = []
            values = []
            bar_colors = []

            # Get overall utilization from metrics (workshop_utilization field)
            overall_util = metrics.get('workshop_utilization', workshop_df['utilization_percent'].mean())
            labels.append('Overall')
            values.append(overall_util)
            bar_colors.append(colors['Overall'])

            for _, row in workshop_df.iterrows():
                workshop_id = row['workshop_id']
                util = row['utilization_percent']
                color = colors.get(workshop_id, '#7f7f7f')

                # Overall workshop
                labels.append(f'{workshop_id}')
                values.append(util)
                bar_colors.append(color)

                # Individual bays (assuming 2 bays)
                labels.append(f'{workshop_id}_bay_1')
                values.append(util)
                bar_colors.append(color)

                labels.append(f'{workshop_id}_bay_2')
                values.append(util)
                bar_colors.append(color)

            # Create horizontal bar chart
            ax.barh(labels, values, color=bar_colors, alpha=0.85, linewidth=0.8, edgecolor='black')
            ax.set_xlim(0, 100)
            ax.set_xlabel('Utilization (%)', fontsize=10)
            ax.set_ylabel('Resource', fontsize=10)
            ax.tick_params(labelsize=9)
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            plt.tight_layout()

            st.pyplot(fig)
            plt.close()
        else:
            st.markdown('**Workshop Bay Utilization**')
            st.info('No workshop data available')


def render_wagon_flow_tab(data: dict[str, Any]) -> None:  # noqa: PLR0915, C901, PLR0912
    """Render wagon flow analysis."""
    st.header('🚃 Wagon Flow Analysis')

    if 'metrics' not in data:
        st.warning('⚠️ No metrics data available')
        return

    metrics = data['metrics']

    # Temporal wagon flow
    st.subheader('Wagon Flow Over Time')
    if 'wagon_journey' in data and not data['wagon_journey'].empty:
        col1, col2 = st.columns([3, 1])
        with col1:
            view_type = st.radio(
                'View by:', ['By Wagon (see individual journeys)', 'By Track (see track utilization)'], horizontal=True
            )
        if 'Track' in view_type:
            _render_track_gantt(data['wagon_journey'])
        else:
            _render_wagon_gantt(data['wagon_journey'])
    else:
        st.info('No wagon journey data available')

    # Wagon status distribution (use wagon_locations if available, otherwise events)
    st.subheader('Wagon Status Distribution (Final State)')

    if 'wagon_locations' in data and not data['wagon_locations'].empty:
        # Use actual wagon locations
        locations_df = data['wagon_locations']
        status_counts = locations_df['status'].value_counts().to_dict()

        # Add parked wagons
        parked = metrics.get('wagons_parked', 0)
        if parked > 0:
            status_counts['PARKED'] = parked

        # Add rejected wagons
        if 'rejected_wagons' in data and not data['rejected_wagons'].empty:
            rejected_df = data['rejected_wagons']
            rejection_type_counts = rejected_df['rejection_type'].value_counts()
            for rtype, count in rejection_type_counts.items():
                status_counts[f'REJECTED: {rtype}'] = int(count)

        # Calculate unaccounted
        total_arrived = metrics.get('wagons_arrived', 0)
        total_accounted = sum(status_counts.values())
        unaccounted = total_arrived - total_accounted
        if unaccounted > 0:
            status_counts['UNACCOUNTED'] = unaccounted

        col1, col2 = st.columns([2, 1])

        with col1:
            df_status = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
            df_status = df_status.sort_values('Count', ascending=False)
            st.bar_chart(df_status.set_index('Status'))

        with col2:
            total_row = pd.DataFrame([['TOTAL', sum(status_counts.values())]], columns=['Status', 'Count'])
            df_display = pd.concat([df_status, total_row], ignore_index=True)
            st.dataframe(df_display, use_container_width=True)
            st.caption(f'Total arrived: {total_arrived}')
    elif 'events' in data and not data['events'].empty:
        # Fallback to events
        final_status = _get_final_wagon_status(data['events'], data.get('rejected_wagons'))
        total_arrived = metrics.get('wagons_arrived', 0)
        total_accounted = sum(final_status.values())
        unaccounted = total_arrived - total_accounted
        if unaccounted > 0:
            final_status['UNACCOUNTED'] = unaccounted

        col1, col2 = st.columns([2, 1])
        with col1:
            df_status = pd.DataFrame(list(final_status.items()), columns=['Status', 'Count'])
            df_status = df_status.sort_values('Count', ascending=False)
            st.bar_chart(df_status.set_index('Status'))
        with col2:
            total_row = pd.DataFrame([['TOTAL', sum(final_status.values())]], columns=['Status', 'Count'])
            df_display = pd.concat([df_status, total_row], ignore_index=True)
            st.dataframe(df_display, use_container_width=True)
            st.caption(f'Total arrived: {total_arrived}')
    else:
        st.info('No data available')

    # Wagon locations by track
    st.subheader('Wagon Locations by Track (final state)')

    if 'wagon_locations' in data and not data['wagon_locations'].empty:
        locations_df = data['wagon_locations']
        track_counts = locations_df['current_track'].value_counts()

        col1, col2 = st.columns([2, 1])
        with col1:
            df_tracks = pd.DataFrame(list(track_counts.items()), columns=['Track', 'Count'])
            st.bar_chart(df_tracks.set_index('Track'))
        with col2:
            st.dataframe(df_tracks, use_container_width=True)

    # Detailed breakdown
    st.subheader('Detailed Breakdown')
    col1, col2 = st.columns([2, 1])

    with col1:
        # Get rejection breakdown if available
        rejection_counts = {'Loaded': 0, 'No Retrofit Needed': 0, 'Collection Track Full': 0}
        if 'rejected_wagons' in data and not data['rejected_wagons'].empty:
            rejection_type_counts = data['rejected_wagons']['rejection_type'].value_counts()
            for rtype, count in rejection_type_counts.items():
                if rtype in rejection_counts:
                    rejection_counts[rtype] = int(count)

        # Calculate wagon states from events and locations
        total_arrived = metrics.get('wagons_arrived', 0)
        retrofitted = metrics.get('retrofits_completed', 0)
        parked = metrics.get('wagons_parked', 0)
        ready_for_retrofit = metrics.get('event_counts', {}).get('WagonReadyForRetrofitEvent', 0)

        # Get wagon locations breakdown by track and status
        track_breakdown = {}
        if 'wagon_locations' in data and not data['wagon_locations'].empty:
            locations_df = data['wagon_locations']

            # Count by status
            retrofitting = len(locations_df[locations_df['status'] == 'RETROFITTING'])
            on_retrofit_track = len(
                locations_df[(locations_df['current_track'] == 'retrofit') & (locations_df['status'] != 'RETROFITTING')]
            )
            on_collection = len(
                locations_df[locations_df['current_track'].str.contains('collection', case=False, na=False)]
            )
            on_workshops = len(
                locations_df[
                    locations_df['current_track'].str.startswith('WS', na=False)
                    & (locations_df['status'] != 'RETROFITTING')
                ]
            )

            if retrofitting > 0:
                track_breakdown['In Retrofit (processing)'] = retrofitting
            if on_retrofit_track > 0:
                track_breakdown['On Retrofit Track (waiting)'] = on_retrofit_track
            if on_collection > 0:
                track_breakdown['On Collection Track'] = on_collection
            if on_workshops > 0:
                track_breakdown['At Workshop (waiting)'] = on_workshops

        # Wagons in different states
        if not track_breakdown:
            waiting_or_in_retrofit = ready_for_retrofit - retrofitted

        states = {
            'Completed & Parked': parked,
            **track_breakdown,
        }

        if not track_breakdown:
            states['Waiting/In Retrofit'] = waiting_or_in_retrofit

        states.update(
            {
                'Rejected: Loaded': rejection_counts['Loaded'],
                'Rejected: No Retrofit Needed': rejection_counts['No Retrofit Needed'],
                'Rejected: Collection Track Full': rejection_counts['Collection Track Full'],
            }
        )

        # Filter out zero values for cleaner chart
        states = {k: v for k, v in states.items() if v > 0}

        if states:
            df_states = pd.DataFrame(list(states.items()), columns=['State', 'Count'])
            st.bar_chart(df_states.set_index('State'))
        else:
            st.info('No wagon data available')

    with col2:
        if states:
            df_states = pd.DataFrame(list(states.items()), columns=['State', 'Count'])
            # Add total row
            total_row = pd.DataFrame([['TOTAL', sum(states.values())]], columns=['State', 'Count'])
            df_display = pd.concat([df_states, total_row], ignore_index=True)
            st.dataframe(df_display, use_container_width=True)
            st.caption(f'Total arrived: {total_arrived}')

    # Show detailed wagon data
    if 'wagon_locations' in data and not data['wagon_locations'].empty:
        locations_df = data['wagon_locations']

        # Create pivot table: tracks as rows, statuses as columns
        track_status_pivot = locations_df.groupby(['current_track', 'status']).size().unstack(fill_value=0)
        track_status_pivot['TOTAL'] = track_status_pivot.sum(axis=1)
        track_status_pivot = track_status_pivot.sort_values('TOTAL', ascending=False)

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown('**Wagons by Track & Status**')
            st.dataframe(track_status_pivot, use_container_width=True)
        with col2:
            st.markdown('**Individual Wagons (Final State)**')
            st.dataframe(locations_df.head(50), use_container_width=True)
            st.caption(f'Showing first 50 of {len(locations_df)} wagons')

    # Show wagon journey history
    if 'wagon_journey' in data and not data['wagon_journey'].empty:
        st.subheader('Wagon Journey History')
        journey_df = data['wagon_journey']

        # Wagon selector
        wagon_ids = sorted(journey_df['wagon_id'].unique())
        selected_wagon = st.selectbox('Select wagon to view journey:', wagon_ids, index=0)

        if selected_wagon:
            wagon_history = journey_df[journey_df['wagon_id'] == selected_wagon]

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown(f'**Journey for {selected_wagon}**')
                st.dataframe(wagon_history[['timestamp', 'event', 'location', 'status']], use_container_width=True)

            with col2:
                st.markdown('**Journey Timeline**')
                # Create Gantt-style chart showing status over time
                import matplotlib.pyplot as plt

                fig, ax = plt.subplots(figsize=(8, 4))

                # Create horizontal bars for each status period
                status_colors = {
                    'ARRIVED': '#8c564b',  # Brown
                    'WAITING_RETROFIT': '#ff7f0e',  # Orange
                    'RETROFITTING': '#2ca02c',  # Green
                    'COMPLETED': '#1f77b4',  # Blue
                    'RETROFITTED': '#17becf',  # Cyan
                    'DISTRIBUTED': '#bcbd22',  # Yellow-green
                    'PARKED': '#9467bd',  # Purple
                    'REJECTED': '#d62728',  # Red
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
                    ax.barh(
                        y_pos,
                        duration,
                        left=start_time,
                        height=0.8,
                        color=color,
                        alpha=0.8,
                        edgecolor='black',
                        linewidth=0.5,
                    )

                    # Add label if duration is significant
                    if duration > 50:
                        ax.text(
                            start_time + duration / 2,
                            y_pos,
                            status,
                            ha='center',
                            va='center',
                            fontsize=8,
                            fontweight='bold',
                        )

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
                    last_row['timestamp'] + 50,
                    y_pos,
                    last_row['status'],
                    ha='center',
                    va='center',
                    fontsize=8,
                    fontweight='bold',
                )

                ax.set_xlabel('Simulation Time (minutes)', fontsize=10)
                ax.set_yticks([])
                ax.set_title(f'Status Timeline for {selected_wagon}', fontsize=11, fontweight='bold')
                ax.grid(axis='x', alpha=0.3, linestyle='--')

                # Add legend
                from matplotlib.patches import Patch

                legend_elements = [
                    Patch(facecolor=color, edgecolor='black', label=status, alpha=0.8)
                    for status, color in status_colors.items()
                ]
                ax.legend(handles=legend_elements, loc='upper right', fontsize=8, ncol=2)

                plt.tight_layout()

                st.pyplot(fig)
                plt.close()

    # Summary statistics
    if 'wagon_journey' in data and not data['wagon_journey'].empty:
        st.subheader('Journey Statistics')
        journey_df = data['wagon_journey']

        col1, col2, col3 = st.columns(3)

        with col1:
            # Count wagons by final status
            final_status = journey_df.groupby('wagon_id').last()['status'].value_counts()
            st.markdown('**Final Status**')
            st.dataframe(final_status.reset_index(name='count'), use_container_width=True)

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

    # Event timeline
    if 'events' in data and not data['events'].empty:
        st.subheader('Event Timeline')
        events_df = data['events']

        # Filter controls
        event_types = events_df['event_type'].unique().tolist()
        selected_types = st.multiselect('Filter by event type', event_types, default=event_types[:5])

        filtered_events = events_df[events_df['event_type'].isin(selected_types)]
        st.dataframe(filtered_events.head(100), use_container_width=True)


def render_workshop_tab(data: dict[str, Any]) -> None:
    """Render workshop performance analysis."""
    st.header('🏭 Workshop Performance')

    if 'workshop_metrics' not in data or data['workshop_metrics'].empty:
        st.warning('⚠️ No workshop metrics available')
        return

    workshop_df = data['workshop_metrics']

    # Workshop comparison table
    st.subheader('Workshop Comparison')
    st.dataframe(workshop_df, use_container_width=True)

    # Utilization chart
    st.subheader('Workshop Utilization')
    st.bar_chart(workshop_df.set_index('workshop_id')['utilization_percent'])

    # Throughput chart
    st.subheader('Throughput (wagons/hour)')
    st.bar_chart(workshop_df.set_index('workshop_id')['throughput_per_hour'])


def render_locomotive_tab(data: dict[str, Any]) -> None:
    """Render locomotive operations analysis."""
    st.header('🚂 Locomotive Operations')

    if 'locomotive_util' not in data or data['locomotive_util'].empty:
        st.warning('⚠️ No locomotive utilization data available')
        return

    loco_df = data['locomotive_util']

    # Check if coupling/decoupling data exists
    has_coupling = loco_df['coupling_percent'].sum() > 0 or loco_df['decoupling_percent'].sum() > 0

    # Utilization table
    st.subheader('Locomotive Utilization Breakdown')

    if has_coupling:
        display_df = loco_df[
            ['locomotive_id', 'parking_percent', 'moving_percent', 'coupling_percent', 'decoupling_percent']
        ]
        chart_cols = ['parking_percent', 'moving_percent', 'coupling_percent', 'decoupling_percent']
    else:
        display_df = loco_df[['locomotive_id', 'parking_percent', 'moving_percent']]
        chart_cols = ['parking_percent', 'moving_percent']
        st.info('i Coupling/decoupling operations not tracked in this simulation')

    st.dataframe(display_df, use_container_width=True)

    # Stacked bar chart
    st.subheader('Activity Distribution')
    chart_data = loco_df.set_index('locomotive_id')[chart_cols]
    st.bar_chart(chart_data)


def render_track_capacity_tab(data: dict[str, Any]) -> None:
    """Render track capacity analysis."""
    st.header('🛤️ Track Capacity')

    if 'track_capacity' not in data or data['track_capacity'].empty:
        st.warning('⚠️ No track capacity data available')
        return

    track_df = data['track_capacity']

    # Track utilization grid
    st.subheader('Track Utilization')

    # Color-code by utilization
    def color_utilization(val: float) -> str:
        if val >= 85:
            return 'background-color: #DC3545'  # Red
        elif val >= 70:
            return 'background-color: #FFC107'  # Yellow
        else:
            return 'background-color: #28A745'  # Green

    styled_df = track_df.style.applymap(color_utilization, subset=['utilization_percent'])
    st.dataframe(styled_df, use_container_width=True)

    # Utilization chart
    st.subheader('Track Utilization Chart')
    st.bar_chart(track_df.set_index('track_id')['utilization_percent'])


def render_rejected_wagons_tab(data: dict[str, Any]) -> None:
    """Render rejected wagons analysis."""
    st.header('❌ Rejected Wagons')

    if 'rejected_wagons' not in data or data['rejected_wagons'].empty:
        st.success('✅ No wagons rejected')
        return

    rejected_df = data['rejected_wagons']

    # st.subheader('Rejection Type Breakdown')
    rejected_df['rejection_type_norm'] = (
        rejected_df['rejection_type']
        .fillna('')
        .astype(str)
        .str.normalize('NFKC')
        .str.replace('_', ' ', regex=False)  # "COLLECTION_TRACK" -> "COLLECTION TRACK"
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
        .str.casefold()
    )

    rejected_df['collection_track_id'] = rejected_df['collection_track_id'].astype(str).str.strip()

    canonical_types = {
        'loaded': 'Loaded',
        'no retrofit needed': 'No Retrofit Needed',
        'collection track full': 'Collection Track Full',
    }

    # not sure what is the target here but take care with what ruff suggests
    rejection_counts = {v: 0 for v in canonical_types.values()}  # noqa: C420
    actual_counts_norm = rejected_df['rejection_type_norm'].value_counts()
    for norm_type, count in actual_counts_norm.items():
        if norm_type in canonical_types:
            readable = canonical_types[norm_type]
            rejection_counts[readable] = int(count)

    counts_df = pd.DataFrame(list(rejection_counts.items()), columns=['Type', 'Count'])

    mask_full = rejected_df['rejection_type_norm'].eq('collection track full')

    counts_by_track = (
        rejected_df.loc[mask_full, 'collection_track_id'].value_counts(dropna=False).sort_values(ascending=False)
    )

    counts_by_track_df = counts_by_track.rename('Count').reset_index()
    counts_by_track_df = counts_by_track_df.rename(columns={'index': 'collection_track_id'})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader('Breakdown of rejection per type')
        st.bar_chart(counts_df.set_index('Type'))
    with col2:
        st.subheader('Counts per type')
        st.dataframe(counts_df, use_container_width=True)

    st.subheader('Breakdown of rejection per collection track')
    st.bar_chart(counts_by_track)  # Direkt als Series mit Track-ID im Index
    st.dataframe(counts_by_track_df, use_container_width=True)
    st.caption(f'Overall wagons still on collection tracks: {int(mask_full.sum())}')

    st.subheader('Rejected Wagons Details')
    st.dataframe(rejected_df, use_container_width=True)
    st.caption(f'Total rejected: {len(rejected_df)} wagons')


def render_event_log_tab(data: dict[str, Any]) -> None:
    """Render event log viewer."""
    st.header('🔍 Event Log Viewer')

    if 'events' not in data or data['events'].empty:
        st.warning('⚠️ No event data available')
        return

    events_df = data['events']

    # Filter controls
    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input('🔍 Search events', placeholder='Enter search term...')

    with col2:
        show_lines = st.number_input('Show lines', min_value=10, max_value=1000, value=100, step=10)

    # Event type filter
    event_types = events_df['event_type'].unique().tolist()
    selected_types = st.multiselect('Filter by event type', event_types, default=event_types)

    # Apply filters
    filtered_df = events_df[events_df['event_type'].isin(selected_types)]

    if search_term:
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        filtered_df = filtered_df[mask]

    # Display table
    st.dataframe(filtered_df.head(show_lines), use_container_width=True)
    st.caption(f'Showing {min(show_lines, len(filtered_df))} of {len(filtered_df)} events')


def render_process_log_tab(data: dict[str, Any]) -> None:
    """Render process log viewer."""
    st.header('📋 Process Log Viewer')

    if 'process_log' not in data or data['process_log'].empty:
        st.warning('⚠️ No process log data available')
        return

    process_df = data['process_log']

    # Filter controls
    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input('🔍 Search process log', placeholder='Enter search term...')

    with col2:
        show_lines = st.number_input(
            'Show lines', min_value=10, max_value=1000, value=100, step=10, key='process_lines'
        )

    # Process type filter
    if 'process' in process_df.columns:
        process_types = process_df['process'].unique().tolist()
        selected_processes = st.multiselect('Filter by process', process_types, default=process_types)
        filtered_df = process_df[process_df['process'].isin(selected_processes)]
    else:
        filtered_df = process_df

    if search_term:
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        filtered_df = filtered_df[mask]

    # Display table
    st.dataframe(filtered_df.head(show_lines), use_container_width=True)
    st.caption(f'Showing {min(show_lines, len(filtered_df))} of {len(filtered_df)} process entries')


def _render_wagon_gantt(journey_df) -> None:  # noqa: PLR0915
    """Render Gantt chart showing individual wagon journeys."""
    import matplotlib.pyplot as plt

    # Filter wagons if needed
    def wagon_has_journey(locations) -> bool:
        unique_locs = locations.unique()
        # Has journey if: more than 1 location OR has rejected track
        return len(unique_locs) > 1 or 'rejected' in unique_locs.tolist()

    wagons_with_journey = journey_df.groupby('wagon_id')['location'].apply(wagon_has_journey)
    wagon_ids = sorted(wagons_with_journey[wagons_with_journey].index)
    journey_df = journey_df[journey_df['wagon_id'].isin(wagon_ids)]

    wagon_positions = {wagon_id: i for i, wagon_id in enumerate(wagon_ids)}

    # Color map for tracks - distinct colors
    # Get unique tracks from data to dynamically assign colors
    unique_tracks = journey_df['location'].unique()

    track_colors = {
        'retrofit': '#f39c12',  # Orange - STAGING TRACK
        'WS_01': '#27ae60',  # Green
        'WS_02': '#3498db',  # Blue
        'retrofitted': '#9b59b6',  # Purple
        'distribution': '#1abc9c',  # Turquoise
        'rejected': '#d62728',  # Red - OUT OF SYSTEM
    }

    # Dynamically assign colors to collection tracks (all red shades)
    collection_colors = ['#5fca3f', '#158d39', '#129733', '#12b483']
    collection_tracks = [t for t in unique_tracks if 'collection' in str(t).lower()]
    for i, track in enumerate(sorted(collection_tracks)):
        track_colors[track] = collection_colors[i % len(collection_colors)]

    # Dynamically assign colors to parking tracks (different shades of gray/blue)
    parking_colors = ['#34495e', '#2c3e50', '#7f8c8d', '#95a5a6', '#bdc3c7']
    parking_tracks = [t for t in unique_tracks if 'parking' in str(t).lower()]
    for i, track in enumerate(sorted(parking_tracks)):
        track_colors[track] = parking_colors[i % len(parking_colors)]

    fig, ax = plt.subplots(figsize=(14, max(10, len(wagon_ids) * 0.15)))

    # Plot each wagon's journey
    for wagon_id in wagon_ids:
        wagon_data = journey_df[journey_df['wagon_id'] == wagon_id].sort_values('timestamp')
        y_pos = wagon_positions[wagon_id]

        for i in range(len(wagon_data) - 1):
            row = wagon_data.iloc[i]
            next_row = wagon_data.iloc[i + 1]

            track = row['location']
            status = row['status']
            start_time = row['timestamp']
            end_time = next_row['timestamp']
            duration = end_time - start_time

            color = track_colors.get(track, '#7f7f7f')

            # Use hatching for RETROFITTING status to show active work
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
        track = last_row['location']
        status = last_row['status']
        max_time = journey_df['timestamp'].max()
        duration = max_time - last_row['timestamp']
        if duration > 0:
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

    ax.set_yticks(range(len(wagon_ids)))
    ax.set_yticklabels(wagon_ids, fontsize=6)
    ax.set_xlabel('Simulation Time (minutes)', fontsize=11)
    ax.set_ylabel('Wagon ID', fontsize=11)
    ax.set_title('Individual Wagon Journeys Over Time (Track-based)', fontsize=12, fontweight='bold')
    ax.yaxis.set_inverted(True)
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Add legend - prioritize important tracks
    from matplotlib.patches import Patch

    unique_tracks = sorted(set(journey_df['location'].unique()))

    # Prioritize key tracks in legend - dynamically detect collection tracks
    collection_tracks_in_data = [t for t in unique_tracks if 'collection' in str(t).lower()]
    priority_tracks = [*collection_tracks_in_data, 'retrofit', 'WS_01', 'WS_02', 'retrofitted', 'rejected']
    # Add parking as generic if any parking tracks exist
    if any('parking' in str(t).lower() for t in unique_tracks):
        priority_tracks.append('parking')

    legend_tracks = [t for t in priority_tracks if t in unique_tracks]
    # Add remaining tracks
    legend_tracks.extend([t for t in unique_tracks if t not in legend_tracks][:5])

    legend_elements = [
        Patch(facecolor=track_colors.get(track, '#7f7f7f'), edgecolor='black', label=track, alpha=0.8)
        for track in legend_tracks
    ]
    # Add hatched element to show retrofitting status
    legend_elements.append(
        Patch(facecolor='gray', edgecolor='black', hatch='///', label='RETROFITTING (active work)', alpha=1.0)
    )

    ax.legend(handles=legend_elements, loc='upper right', fontsize=8, ncol=2)

    plt.tight_layout()

    st.pyplot(fig)
    plt.close()

    st.caption(
        f'Showing {len(wagon_ids)} wagons with journeys '
        '(excludes wagons stuck on collection track). '
        'Each color = track/location. Hatched pattern (///) = '
        'actively retrofitting in workshop.'
    )


def _render_track_gantt(journey_df: pd.DataFrame) -> None:
    """Render Gantt chart showing wagons on tracks over time."""
    import matplotlib.pyplot as plt
    import numpy as np

    # Get unique tracks and assign y-positions
    tracks = sorted(journey_df['location'].unique())
    track_positions = {track: i for i, track in enumerate(tracks)}

    # Color map for wagons (cycle through colors)
    wagon_ids = sorted(journey_df['wagon_id'].unique())
    colors = plt.cm.tab20(np.linspace(0, 1, min(len(wagon_ids), 20)))
    wagon_colors = {wagon_id: colors[i % 20] for i, wagon_id in enumerate(wagon_ids)}

    fig, ax = plt.subplots(figsize=(14, max(8, len(tracks) * 0.3)))

    # Plot each wagon's journey
    for wagon_id in wagon_ids:
        wagon_data = journey_df[journey_df['wagon_id'] == wagon_id].sort_values('timestamp')

        for i in range(len(wagon_data) - 1):
            row = wagon_data.iloc[i]
            next_row = wagon_data.iloc[i + 1]

            track = row['location']
            start_time = row['timestamp']
            end_time = next_row['timestamp']
            duration = end_time - start_time

            if track in track_positions:
                y_pos = track_positions[track]
                ax.barh(
                    y_pos,
                    duration,
                    left=start_time,
                    height=0.8,
                    color=wagon_colors[wagon_id],
                    alpha=0.7,
                    edgecolor='black',
                    linewidth=0.3,
                )

        # Add final position
        last_row = wagon_data.iloc[-1]
        track = last_row['location']
        if track in track_positions:
            y_pos = track_positions[track]
            # Show final position as extending to end of simulation
            max_time = journey_df['timestamp'].max()
            duration = max_time - last_row['timestamp']
            if duration > 0:
                ax.barh(
                    y_pos,
                    duration,
                    left=last_row['timestamp'],
                    height=0.8,
                    color=wagon_colors[wagon_id],
                    alpha=0.7,
                    edgecolor='black',
                    linewidth=0.3,
                )

    ax.set_yticks(range(len(tracks)))
    ax.set_yticklabels(tracks, fontsize=9)
    ax.set_xlabel('Simulation Time (minutes)', fontsize=11)
    ax.set_ylabel('Track', fontsize=11)
    ax.set_title('Wagon Locations Over Time', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    plt.tight_layout()

    st.pyplot(fig)
    plt.close()

    st.caption(f'Showing {len(wagon_ids)} wagons across {len(tracks)} tracks. Each color represents a different wagon.')


def _get_wagon_status_timeline(events_df: pd.DataFrame) -> dict[str, list[tuple[float, str]]]:  # noqa: C901
    """Extract wagon status timeline from events."""
    wagon_events = events_df[events_df['resource_type'] == 'wagon'].copy()
    train_events = events_df[events_df['resource_type'] == 'train'].copy()

    wagon_status_timeline = {}

    # Track train arrivals to get initial wagon states
    for _, row in train_events.iterrows():
        if 'Arrived' in row['event_type']:
            # Parse wagon IDs from train arrival (would need actual wagon list)
            pass

    for _, row in wagon_events.iterrows():
        wagon_id = row['resource_id']
        timestamp = row['timestamp']
        event_type = row['event_type']

        # Map event types to statuses
        if 'ReadyForRetrofit' in event_type:
            status = 'ON_RETROFIT_TRACK'
        elif 'RetrofitStarted' in event_type:
            status = 'RETROFITTING'
        elif 'RetrofitCompleted' in event_type:
            status = 'COMPLETED'
        elif 'Parked' in event_type:
            status = 'PARKED'
        elif 'Rejected' in event_type:
            status = 'REJECTED'
        elif 'Classified' in event_type or 'Distributed' in event_type:
            status = 'WAITING_CLASSIFICATION'
        else:
            continue

        if wagon_id not in wagon_status_timeline:
            wagon_status_timeline[wagon_id] = []
        wagon_status_timeline[wagon_id].append((timestamp, status))

    return wagon_status_timeline


def _get_final_wagon_status(events_df: pd.DataFrame, rejected_df: pd.DataFrame | None) -> dict[str, int]:
    """Get final status count for all wagons."""
    wagon_status_timeline = _get_wagon_status_timeline(events_df)

    status_counts = {}

    # Get final status for wagons with events
    for _wagon_id, timeline in wagon_status_timeline.items():
        if timeline:
            final_status = sorted(timeline)[-1][1]
            # Map intermediate states to final states
            if final_status == 'COMPLETED':
                final_status = 'RETROFITTED'
            elif final_status == 'RETROFITTING':
                final_status = 'IN_PROGRESS'
            status_counts[final_status] = status_counts.get(final_status, 0) + 1

    # Add rejected wagon breakdown (these may not have wagon events)
    if rejected_df is not None and not rejected_df.empty:
        rejection_type_counts = rejected_df['rejection_type'].value_counts()
        for rtype, count in rejection_type_counts.items():
            status_counts[f'REJECTED: {rtype}'] = int(count)
        # Remove generic REJECTED if we have breakdown
        status_counts.pop('REJECTED', None)

    # Filter out zero counts
    status_counts = {k: v for k, v in status_counts.items() if v > 0}

    return status_counts


def _render_temporal_flow_old(events_df: pd.DataFrame) -> None:
    """Render temporal wagon flow as stacked area chart."""
    import matplotlib.pyplot as plt

    wagon_status_timeline = _get_wagon_status_timeline(events_df)

    if not wagon_status_timeline:
        st.info('No wagon events available')
        return

    # Get time range
    max_time = events_df['timestamp'].max()
    time_points = list(range(0, int(max_time) + 1, 1))  # 1 minute intervals

    # Count wagons in each status at each time point
    status_counts = {
        status: []
        for status in ['WAITING_CLASSIFICATION', 'ON_RETROFIT_TRACK', 'RETROFITTING', 'COMPLETED', 'PARKED', 'REJECTED']
    }

    for t in time_points:
        counts = dict.fromkeys(status_counts.keys(), 0)

        for _wagon_id, timeline in wagon_status_timeline.items():
            # Find current status at time t
            current_status = None
            for timestamp, status in sorted(timeline):
                if timestamp <= t:
                    current_status = status
                else:
                    break

            if current_status:
                counts[current_status] += 1

        for status in status_counts:
            status_counts[status].append(counts[status])

    # Create stacked area chart
    fig, ax = plt.subplots(figsize=(12, 6))

    # Stack the areas
    ax.stackplot(
        time_points,
        status_counts['WAITING_CLASSIFICATION'],
        status_counts['ON_RETROFIT_TRACK'],
        status_counts['RETROFITTING'],
        status_counts['COMPLETED'],
        status_counts['PARKED'],
        status_counts['REJECTED'],
        labels=['Waiting Classification', 'On Retrofit Track', 'Retrofitting', 'Completed', 'Parked', 'Rejected'],
        alpha=0.8,
        colors=['#8c564b', '#ff7f0e', '#2ca02c', '#1f77b4', '#9467bd', '#d62728'],
    )

    ax.set_xlabel('Simulation Time (minutes)', fontsize=11)
    ax.set_ylabel('Number of Wagons', fontsize=11)
    ax.set_title('Wagon Status Over Time', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    st.pyplot(fig)
    plt.close()


def main() -> None:
    """Run main dashboard application."""
    # Sidebar
    st.sidebar.header('📁 Load Simulation Results')

    output_dir = st.sidebar.text_input(
        'Base output Directory', value='output', help='Path to base simulation output directory'
    )

    st.session_state['base_output_dir'] = Path(output_dir)
    folders = st.session_state['base_output_dir'].glob('**/')

    output_folder = st.sidebar.selectbox(
        'Output scenario folder',
        folders,
    )

    st.session_state['output_dir'] = output_folder
    output_path = Path(output_folder)

    if not output_path.exists():
        st.error(f'❌ Directory not found: {output_dir}')
        st.stop()

    # Load data
    with st.spinner('Loading simulation data...'):
        data = load_dashboard_data(output_path)

    if not data:
        st.error(
            '❌ No data files found in output directory. Maybe you need to set a scenario folder from the dropdown '
            'first.'
        )
        st.stop()

    # Render header
    render_header(data)

    # Main tabs
    tabs = st.tabs(
        [
            '📊 Overview',
            '🚃 Wagon Flow',
            '🏭 Workshop',
            '🚂 Locomotive',
            '🛤️ Track Capacity',
            '❌ Rejected Wagons',
            '🔍 Event Log',
            '📋 Process Log',
        ]
    )

    with tabs[0]:
        render_overview_tab(data)

    with tabs[1]:
        render_wagon_flow_tab(data)

    with tabs[2]:
        render_workshop_tab(data)

    with tabs[3]:
        render_locomotive_tab(data)

    with tabs[4]:
        render_track_capacity_tab(data)

    with tabs[5]:
        render_rejected_wagons_tab(data)

    with tabs[6]:
        render_event_log_tab(data)

    with tabs[7]:
        render_process_log_tab(data)

    # Footer
    st.sidebar.markdown('---')
    st.sidebar.info(
        '**PopUpSim Dashboard**\n\nPost-simulation analysis dashboard.\n\n📂 Load output directory to view results.'
    )


if __name__ == '__main__':
    main()
