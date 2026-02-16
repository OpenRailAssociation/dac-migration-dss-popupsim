"""PopUpSim Dashboard V2 - Clean architecture with scenario configuration visualization."""

from pathlib import Path

from dashboard_v2_components.bottleneck_tab import render_bottleneck_tab
from dashboard_v2_components.data_loader import DataLoader
from dashboard_v2_components.locomotive_tab import render_locomotive_tab
from dashboard_v2_components.overview_tab import render_overview_tab
from dashboard_v2_components.scenario_tab import render_scenario_tab
from dashboard_v2_components.track_capacity_tab import render_track_capacity_tab
from dashboard_v2_components.wagon_flow_tab import render_wagon_flow_tab
from dashboard_v2_components.workshop_tab import render_workshop_tab
import pandas as pd
import streamlit as st

st.set_page_config(page_title='PopUpSim Dashboard V2', layout='wide', page_icon='🚂')


def render_header(data: dict) -> None:
    """Render dashboard header."""
    st.title('🚂 PopUpSim - Simulation Dashboard V2')

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

    # Dropdown to select scenario
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
    st.sidebar.info(
        '**PopUpSim Dashboard**'
        '\n📂 Load output directory to view results.'
    )


if __name__ == '__main__':
    main()
