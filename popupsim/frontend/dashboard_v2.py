"""PopUpSim Dashboard V2 - Clean architecture with scenario configuration visualization."""

from pathlib import Path

from dashboard_v2_components.bottleneck_tab import render_bottleneck_tab
from dashboard_v2_components.data_loader import DataLoader
from dashboard_v2_components.overview_tab import render_overview_tab
from dashboard_v2_components.scenario_tab import render_scenario_tab
from dashboard_v2_components.track_capacity_tab import render_track_capacity_tab
from dashboard_v2_components.wagon_flow_tab import render_wagon_flow_tab
import streamlit as st

st.set_page_config(page_title='PopUpSim Dashboard V2', layout='wide', page_icon='🚂')


def render_header(data: dict) -> None:
    """Render dashboard header."""
    st.title('🚂 PopUpSim Dashboard V2')

    if 'metrics' in data:
        metrics = data['metrics']
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric('Total Wagons', metrics.get('wagons_arrived', 0))
        with col2:
            st.metric('Retrofitted', metrics.get('retrofits_completed', 0))
        with col3:
            completion = metrics.get('completion_rate', 0) * 100
            st.metric('Completion Rate', f'{completion:.1f}%')
        with col4:
            duration = metrics.get('simulation_duration_minutes', 0)
            st.metric('Duration', f'{duration:.0f} min')

    st.markdown('---')


def main() -> None:
    """Main dashboard application."""
    # Sidebar
    st.sidebar.header('📁 Load Simulation Results')

    output_dir = st.sidebar.text_input(
        'Output Directory', value='output/test0', help='Path to simulation output directory'
    )

    output_path = Path(output_dir)

    if not output_path.exists():
        st.error(f'❌ Directory not found: {output_dir}')
        st.stop()

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
            '⚙️ Scenario Config',
            '📊 Overview',
            '🚃 Wagon Flow',
            '🛤️ Track Capacity',
            '🚧 Bottleneck Analysis',
        ]
    )

    with tabs[0]:
        render_scenario_tab(data)

    with tabs[1]:
        render_overview_tab(data)

    with tabs[2]:
        render_wagon_flow_tab(data)

    with tabs[3]:
        render_track_capacity_tab(data)

    with tabs[4]:
        render_bottleneck_tab(data)

    # Footer
    st.sidebar.markdown('---')
    st.sidebar.info(
        '**PopUpSim Dashboard V2**\\n\\n'
        'Enhanced visualization with scenario configuration analysis.\\n\\n'
        '📂 Load output directory to view results.'
    )


if __name__ == '__main__':
    main()
