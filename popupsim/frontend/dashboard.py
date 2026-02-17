"""PopUpSim Dashboard V2 - Clean architecture with scenario configuration visualization."""

from pathlib import Path

from dashboard_components.bottleneck_tab import render_bottleneck_tab
from dashboard_components.data_loader import DataLoader
from dashboard_components.locomotive_tab import render_locomotive_tab
from dashboard_components.overview_tab import render_overview_tab
from dashboard_components.scenario_tab import render_scenario_tab
from dashboard_components.track_capacity_tab import render_track_capacity_tab
from dashboard_components.wagon_flow_tab import render_wagon_flow_tab
from dashboard_components.workshop_tab import render_workshop_tab
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='PopUpSim Dashboard', layout='wide', page_icon='🚂')


def render_header(data: dict) -> None:
    """Render dashboard header."""
    st.title('🚂 PopUpSim - Simulation Dashboard')

    scenario_config = data.get('scenario_config', {})
    scenario_info = scenario_config.get('scenario', {})
    scenario_id = scenario_info.get('id', 'N/A')

    start_date = pd.to_datetime(scenario_info.get('start_date')) if scenario_info.get('start_date') else None
    end_date = pd.to_datetime(scenario_info.get('end_date')) if scenario_info.get('end_date') else None

    duration = (end_date - start_date).days if start_date and end_date else None

    st.subheader(f'Scenario: {scenario_id}')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Start Date', start_date.strftime('%Y-%m-%d %H:%M') if start_date else 'N/A')
    with col2:
        st.metric('End Date', end_date.strftime('%Y-%m-%d %H:%M') if end_date else 'N/A')
    with col3:
        st.metric('Duration', f'{duration} days' if duration else 'N/A')

    st.markdown('---')


def main() -> None:
    """Run main dashboard application."""
    # Sidebar
    st.sidebar.header('📁 Load Simulation Results')

    # Base output directory
    base_dir = st.sidebar.text_input(
        'Base Output Directory', value='output', help='Base directory containing scenario folders'
    )
    base_path = Path(base_dir)

    if not base_path.exists():
        st.error(f'❌ Base directory not found: {base_dir}')
        st.stop()

    # Scan for scenario folders (folders containing a 'scenario' subdirectory)
    scenario_folders = []
    for folder in sorted(base_path.iterdir()):
        if folder.is_dir() and (folder / 'scenario').exists():
            scenario_folders.append(folder.name)

    if not scenario_folders:
        st.warning(f'⚠️ No scenario folders found in {base_dir}. Looking for folders with a "scenario" subdirectory.')
        st.stop()

    # Scenario comparison mode
    comparison_mode = st.sidebar.checkbox(
        '🔄 Compare Scenarios', help='Compare metrics from multiple scenarios side-by-side'
    )

    if comparison_mode:
        selected_scenarios = st.sidebar.multiselect(
            'Select Scenarios to Compare',
            scenario_folders,
            default=scenario_folders[:2] if len(scenario_folders) >= 2 else scenario_folders,
        )
        if len(selected_scenarios) < 2:
            st.info('🔄 Select at least 2 scenarios to compare')
            st.stop()
        _render_comparison_view(base_path, selected_scenarios)
        return

    # Single scenario mode
    selected_scenario = st.sidebar.selectbox('Select Scenario', scenario_folders, help='Choose a scenario to visualize')
    output_path = base_path / selected_scenario

    # Load data
    with st.spinner('Loading simulation data...'):
        loader = DataLoader(output_path)
        data = loader.load_all()

    if not data:
        st.error('❌ No data files found in output directory')
        st.stop()

    # Render header
    render_header(data)

    # Main tabs
    tabs = st.tabs(
        [
            '📊 Overview',
            '⚙️ Scenario Config',
            '🚃 Wagons',
            '🚂 Locomotives',
            '🏭 Workshops',
            '🛤️ Track Capacity',
            '🚧 Bottleneck Analysis',
        ]
    )
    with tabs[0]:
        render_overview_tab(data)

    with tabs[1]:
        render_scenario_tab(data)

    with tabs[2]:
        render_wagon_flow_tab(data)

    with tabs[3]:
        render_locomotive_tab(data)

    with tabs[4]:
        render_workshop_tab(data)

    with tabs[5]:
        render_track_capacity_tab(data)

    with tabs[6]:
        render_bottleneck_tab(data)

    # Footer
    st.sidebar.markdown('---')
    st.sidebar.info('**PopUpSim Dashboard**\n📂 Load output directory to view results.')


def _render_comparison_view(base_path: Path, selected_scenarios: list[str]) -> None:  # noqa: C901, PLR0912, PLR0915  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Render scenario comparison view.

    Note: High complexity acceptable for comprehensive comparison dashboard.
    """
    st.title('🔄 Scenario Comparison')

    # Load all scenarios
    scenarios_data = {}
    for scenario_name in selected_scenarios:
        with st.spinner(f'Loading {scenario_name}...'):
            loader = DataLoader(base_path / scenario_name)
            scenarios_data[scenario_name] = loader.load_all()

    # Compare key metrics
    st.subheader('📊 Key Performance Indicators')

    comparison_data = []
    for scenario_name, data in scenarios_data.items():
        metrics = data.get('metrics', {})
        wagon_journey = data.get('wagon_journey')

        # Calculate cycle time
        avg_cycle_time = 0
        if wagon_journey is not None and not wagon_journey.empty:
            completed = wagon_journey[wagon_journey['status'] == 'COMPLETED']
            if not completed.empty:
                cycle_times = completed.groupby('wagon_id')['timestamp'].agg(['min', 'max'])
                cycle_times['duration'] = cycle_times['max'] - cycle_times['min']
                avg_cycle_time = cycle_times['duration'].mean()

        comparison_data.append(
            {
                'Scenario': scenario_name,
                'Trains': metrics.get('trains_arrived', 0),
                'Wagons': metrics.get('wagons_arrived', 0),
                'Rejected': metrics.get('wagons_rejected', 0),
                'Rejection %': f'{(metrics.get("wagons_rejected", 0) / metrics.get("wagons_arrived", 1) * 100):.1f}',
                'Retrofits': metrics.get('retrofits_completed', 0),
                'Avg Cycle Time (min)': f'{avg_cycle_time:.1f}',
            }
        )

    comparison_df = pd.DataFrame(comparison_data)

    # Add delta indicators
    if len(comparison_df) == 2:
        st.info('💡 Comparing first scenario as baseline vs second scenario')
        baseline = comparison_df.iloc[0]
        compare = comparison_df.iloc[1]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            delta_retrofits = compare['Retrofits'] - baseline['Retrofits']
            delta_pct = (delta_retrofits / baseline['Retrofits'] * 100) if baseline['Retrofits'] > 0 else 0
            st.metric('Retrofits Completed', compare['Retrofits'], f'{delta_retrofits:+.0f} ({delta_pct:+.1f}%)')

        with col2:
            delta_rejected = compare['Rejected'] - baseline['Rejected']
            st.metric('Wagons Rejected', compare['Rejected'], f'{delta_rejected:+.0f}', delta_color='inverse')

        with col3:
            baseline_rej_rate = float(baseline['Rejection %'])
            compare_rej_rate = float(compare['Rejection %'])
            delta_rej_rate = compare_rej_rate - baseline_rej_rate
            st.metric('Rejection Rate', f'{compare_rej_rate:.1f}%', f'{delta_rej_rate:+.1f}%', delta_color='inverse')

        with col4:
            baseline_cycle = float(baseline['Avg Cycle Time (min)'])
            compare_cycle = float(compare['Avg Cycle Time (min)'])
            delta_cycle = compare_cycle - baseline_cycle
            st.metric('Avg Cycle Time', f'{compare_cycle:.1f} min', f'{delta_cycle:+.1f} min', delta_color='inverse')

    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    if st.button('📥 Export KPI Comparison CSV'):
        csv = comparison_df.to_csv(index=False)
        st.download_button('Download kpi_comparison.csv', csv, 'kpi_comparison.csv', 'text/csv')

    st.markdown('---')

    # Visual comparison charts
    st.subheader('📈 Performance Comparison')

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=comparison_df['Scenario'],
                    y=comparison_df['Retrofits'],
                    marker_color='#3498db',
                    text=comparison_df['Retrofits'],
                    textposition='auto',
                )
            ]
        )
        fig.update_layout(title='Retrofits Completed', xaxis_title='Scenario', yaxis_title='Count', height=300)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_retrofits'},
            },
        )

    with col2:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=comparison_df['Scenario'],
                    y=comparison_df['Rejected'],
                    marker_color='#e74c3c',
                    text=comparison_df['Rejected'],
                    textposition='auto',
                )
            ]
        )
        fig.update_layout(title='Wagons Rejected', xaxis_title='Scenario', yaxis_title='Count', height=300)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_rejections'},
            },
        )

    col1, col2 = st.columns(2)

    with col1:
        rejection_rates = [float(x) for x in comparison_df['Rejection %']]
        colors = ['#e74c3c' if x > 10 else '#f39c12' if x > 5 else '#2ecc71' for x in rejection_rates]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=comparison_df['Scenario'],
                    y=rejection_rates,
                    marker_color=colors,
                    text=[f'{x:.1f}%' for x in rejection_rates],
                    textposition='auto',
                )
            ]
        )
        fig.update_layout(title='Rejection Rate %', xaxis_title='Scenario', yaxis_title='Percentage', height=300)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_rejection_rate'},
            },
        )

    with col2:
        cycle_times = [float(x) for x in comparison_df['Avg Cycle Time (min)']]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=comparison_df['Scenario'],
                    y=cycle_times,
                    marker_color='#9b59b6',
                    text=[f'{x:.1f}' for x in cycle_times],
                    textposition='auto',
                )
            ]
        )
        fig.update_layout(title='Average Cycle Time', xaxis_title='Scenario', yaxis_title='Minutes', height=300)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_cycle_time'},
            },
        )

    st.markdown('---')

    # Workshop comparison
    st.subheader('🏭 Workshop Performance Comparison')

    workshop_comparison = []
    for scenario_name, data in scenarios_data.items():
        workshop_metrics = data.get('workshop_metrics')
        if workshop_metrics is not None and not workshop_metrics.empty:
            for _, row in workshop_metrics.iterrows():
                workshop_comparison.append(
                    {
                        'Scenario': scenario_name,
                        'Workshop': row['workshop_id'],
                        'Completed': int(row['completed_retrofits']),
                        'Utilization %': f'{row["utilization_percent"]:.1f}',
                        'Throughput/Hour': f'{row["throughput_per_hour"]:.2f}',
                        'Retrofit Time (min)': f'{row["total_retrofit_time"]:.0f}',
                        'Waiting Time (min)': f'{row["total_waiting_time"]:.0f}',
                    }
                )

    if workshop_comparison:
        workshop_df = pd.DataFrame(workshop_comparison)
        st.dataframe(workshop_df, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)

        with col1:
            # Utilization comparison
            fig = go.Figure()
            for scenario_name in selected_scenarios:
                scenario_data = workshop_df[workshop_df['Scenario'] == scenario_name]
                fig.add_trace(
                    go.Bar(
                        name=scenario_name,
                        x=scenario_data['Workshop'],
                        y=[float(x) for x in scenario_data['Utilization %']],
                        text=[f'{x}%' for x in scenario_data['Utilization %']],
                        textposition='auto',
                    )
                )
            fig.update_layout(
                title='Workshop Utilization Comparison',
                xaxis_title='Workshop',
                yaxis_title='Utilization %',
                barmode='group',
                height=350,
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    'displayModeBar': True,
                    'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_workshop_utilization'},
                },
            )

        with col2:
            # Throughput comparison
            fig = go.Figure()
            for scenario_name in selected_scenarios:
                scenario_data = workshop_df[workshop_df['Scenario'] == scenario_name]
                fig.add_trace(
                    go.Bar(
                        name=scenario_name,
                        x=scenario_data['Workshop'],
                        y=[float(x) for x in scenario_data['Throughput/Hour']],
                        text=[f'{x}' for x in scenario_data['Throughput/Hour']],
                        textposition='auto',
                    )
                )
            fig.update_layout(
                title='Workshop Throughput Comparison',
                xaxis_title='Workshop',
                yaxis_title='Wagons/Hour',
                barmode='group',
                height=350,
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    'displayModeBar': True,
                    'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_workshop_throughput'},
                },
            )

        if st.button('📥 Export Workshop Comparison CSV'):
            csv = workshop_df.to_csv(index=False)
            st.download_button('Download workshop_comparison.csv', csv, 'workshop_comparison.csv', 'text/csv')

    st.markdown('---')

    # Throughput timeline overlay
    st.subheader('📉 Throughput Timeline Comparison')

    fig = go.Figure()
    for scenario_name, data in scenarios_data.items():
        wagon_journey = data.get('wagon_journey')
        if wagon_journey is not None and not wagon_journey.empty:
            # Calculate cumulative retrofits over time
            completed = wagon_journey[wagon_journey['status'] == 'COMPLETED'].copy()
            if not completed.empty:
                completed = completed.sort_values('timestamp')
                completed['cumulative'] = range(1, len(completed) + 1)
                fig.add_trace(
                    go.Scatter(
                        x=completed['timestamp'],
                        y=completed['cumulative'],
                        mode='lines',
                        name=scenario_name,
                        line={'width': 3},
                        hovertemplate='<b>%{fullData.name}</b><br>Time: %{x:.1f} min<br>Completed: %{y}<extra></extra>',
                    )
                )

    fig.update_layout(
        title='Cumulative Retrofits Over Time',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Cumulative Retrofits Completed',
        height=400,
        hovermode='x unified',
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            'displayModeBar': True,
            'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_timeline', 'height': 600, 'width': 1400},
        },
    )

    st.markdown('---')

    # Bottleneck comparison
    st.subheader('🚧 Bottleneck Analysis Comparison')

    bottleneck_data = []
    for scenario_name, data in scenarios_data.items():
        wagon_journey = data.get('wagon_journey')
        if wagon_journey is not None and not wagon_journey.empty:
            # Calculate waiting time
            waiting = wagon_journey[wagon_journey['status'] == 'WAITING']
            waiting_wagons = len(waiting['wagon_id'].unique())

            # Calculate max queue
            max_queue = 0
            if not waiting.empty:
                time_bins = pd.cut(waiting['timestamp'], bins=20)
                max_queue = waiting.groupby(time_bins)['wagon_id'].nunique().max()

            # Calculate processing efficiency
            processing = wagon_journey[wagon_journey['status'] == 'PROCESSING']
            total_time = wagon_journey['timestamp'].max()
            processing_ratio = len(processing) / len(wagon_journey) * 100 if len(wagon_journey) > 0 else 0

            bottleneck_data.append(
                {
                    'Scenario': scenario_name,
                    'Wagons in Waiting': waiting_wagons,
                    'Max Queue Size': int(max_queue),
                    'Processing Ratio %': f'{processing_ratio:.1f}',
                    'Total Duration (min)': f'{total_time:.0f}',
                }
            )

    if bottleneck_data:
        bottleneck_df = pd.DataFrame(bottleneck_data)
        st.dataframe(bottleneck_df, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=bottleneck_df['Scenario'],
                        y=bottleneck_df['Max Queue Size'],
                        marker_color='#e67e22',
                        text=bottleneck_df['Max Queue Size'],
                        textposition='auto',
                    )
                ]
            )
            fig.update_layout(title='Max Queue Size', xaxis_title='Scenario', yaxis_title='Wagons', height=300)
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    'displayModeBar': True,
                    'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_queue'},
                },
            )

        with col2:
            processing_ratios = [float(x) for x in bottleneck_df['Processing Ratio %']]
            colors = ['#2ecc71' if x > 50 else '#f39c12' if x > 30 else '#e74c3c' for x in processing_ratios]
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=bottleneck_df['Scenario'],
                        y=processing_ratios,
                        marker_color=colors,
                        text=[f'{x:.1f}%' for x in processing_ratios],
                        textposition='auto',
                    )
                ]
            )
            fig.update_layout(
                title='Processing Efficiency', xaxis_title='Scenario', yaxis_title='Percentage', height=300
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    'displayModeBar': True,
                    'toImageButtonOptions': {'format': 'png', 'filename': 'comparison_efficiency'},
                },
            )

        if st.button('📥 Export Bottleneck Comparison CSV'):
            csv = bottleneck_df.to_csv(index=False)
            st.download_button('Download bottleneck_comparison.csv', csv, 'bottleneck_comparison.csv', 'text/csv')


if __name__ == '__main__':
    main()
