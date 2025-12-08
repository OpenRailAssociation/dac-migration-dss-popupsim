"""PopUpSim Streamlit Dashboard - Minimal visualization of simulation results."""

import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image

st.set_page_config(page_title="PopUpSim Dashboard", layout="wide", page_icon="🚂")

# Header
st.title("🚂 PopUpSim - Simulation Dashboard")
st.markdown("---")

# Sidebar for file selection
st.sidebar.header("📁 Load Simulation Results")
output_dir = st.sidebar.text_input(
    "Output Directory", 
    value="output",
    help="Path to simulation output directory"
)

output_path = Path(output_dir)

if not output_path.exists():
    st.error(f"❌ Directory not found: {output_dir}")
    st.stop()

# Check for required files
timeline_file = output_path / "timeline.csv"
process_log_file = output_path / "process.log"
events_log_file = output_path / "events.log"

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Charts", "📋 Process Log", "🔍 Event Log"])

# Tab 1: Overview with charts
with tab1:
    st.header("Simulation Overview")
    
    # Display generated charts if available
    col1, col2 = st.columns(2)
    
    with col1:
        kpi_chart = output_path / "kpi_status.png"
        if kpi_chart.exists():
            st.subheader("KPI Status")
            st.image(str(kpi_chart), use_container_width=True)
    
    with col2:
        flow_chart = output_path / "flow_analysis.png"
        if flow_chart.exists():
            st.subheader("Flow Analysis")
            st.image(str(flow_chart), use_container_width=True)
    
    # Operational dashboard (full width)
    dashboard_chart = output_path / "operational_dashboard.png"
    if dashboard_chart.exists():
        st.subheader("Operational Dashboard")
        st.image(str(dashboard_chart), use_container_width=True)

# Tab 2: Timeline data
with tab2:
    st.header("Timeline Metrics")
    
    if timeline_file.exists():
        df = pd.read_csv(timeline_file)
        
        # Show metrics summary
        st.subheader("Metrics Summary")
        st.dataframe(df, use_container_width=True)
        
        # Simple line chart
        if not df.empty and 'timestamp' in df.columns:
            st.subheader("Metrics Over Time")
            st.line_chart(df.set_index('timestamp'))
    else:
        st.warning("⚠️ timeline.csv not found")

# Tab 3: Process log viewer
with tab3:
    st.header("Process Log")
    
    if process_log_file.exists():
        # Read process log
        with open(process_log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        # Filter controls
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Search log", placeholder="Enter search term...")
        with col2:
            show_lines = st.number_input("Show lines", min_value=10, max_value=1000, value=100, step=10)
        
        # Filter log lines
        if search_term:
            filtered_lines = [line for line in log_lines if search_term.upper() in line.upper()]
        else:
            filtered_lines = log_lines
        
        # Display log
        st.text_area(
            "Log Content",
            value="".join(filtered_lines[-show_lines:]),
            height=600,
            disabled=True
        )
        
        st.caption(f"Showing {min(show_lines, len(filtered_lines))} of {len(filtered_lines)} lines")
    else:
        st.warning("⚠️ process.log not found")

# Tab 4: Event log viewer
with tab4:
    st.header("Event Log")
    
    if events_log_file.exists():
        # Read event log
        with open(events_log_file, 'r', encoding='utf-8') as f:
            event_lines = f.readlines()
        
        # Filter controls
        col1, col2 = st.columns([3, 1])
        with col1:
            event_search = st.text_input("🔍 Search events", placeholder="Enter search term...")
        with col2:
            event_lines_count = st.number_input("Show lines", min_value=10, max_value=1000, value=100, step=10, key="event_lines")
        
        # Filter event lines
        if event_search:
            filtered_events = [line for line in event_lines if event_search.upper() in line.upper()]
        else:
            filtered_events = event_lines
        
        # Display event log
        st.text_area(
            "Event Content",
            value="".join(filtered_events[-event_lines_count:]),
            height=600,
            disabled=True
        )
        
        st.caption(f"Showing {min(event_lines_count, len(filtered_events))} of {len(filtered_events)} lines")
    else:
        st.warning("⚠️ events.log not found")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    "**PopUpSim Dashboard**\n\n"
    "Visualize simulation results from PopUpSim.\n\n"
    "📂 Load output directory to view results."
)
