"""PopUpSim Streamlit Dashboard - Comprehensive post-simulation analysis."""

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

st.set_page_config(page_title="PopUpSim Dashboard", layout="wide", page_icon="🚂")


def load_dashboard_data(output_dir: Path) -> dict[str, Any]:
    """Load all dashboard data files."""
    data: dict[str, Any] = {}
    
    # Load comprehensive metrics JSON
    metrics_file = output_dir / "comprehensive_metrics.json"
    if metrics_file.exists():
        with open(metrics_file, encoding="utf-8") as f:
            data["metrics"] = json.load(f)
    
    # Load events CSV
    events_file = output_dir / "events.csv"
    if events_file.exists():
        data["events"] = pd.read_csv(events_file)
    
    # Load process log
    process_log_file = output_dir / "process.log"
    if process_log_file.exists():
        data["process_log"] = pd.read_csv(process_log_file)
    
    # Load locomotive utilization
    loco_file = output_dir / "locomotive_utilization.csv"
    if loco_file.exists():
        data["locomotive_util"] = pd.read_csv(loco_file)
    
    # Load workshop metrics
    workshop_file = output_dir / "workshop_metrics.csv"
    if workshop_file.exists():
        data["workshop_metrics"] = pd.read_csv(workshop_file)
    
    # Load bottlenecks
    bottlenecks_file = output_dir / "bottlenecks.csv"
    if bottlenecks_file.exists():
        data["bottlenecks"] = pd.read_csv(bottlenecks_file)
    
    # Load track capacity
    track_file = output_dir / "track_capacity.csv"
    if track_file.exists():
        data["track_capacity"] = pd.read_csv(track_file)
    
    return data


def render_header(data: dict[str, Any]) -> None:
    """Render dashboard header with simulation summary."""
    st.title("🚂 PopUpSim - Simulation Dashboard")
    
    if "metrics" in data:
        metrics = data["metrics"]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_wagons = metrics.get("wagons_arrived", 0)
            st.metric("Total Wagons", total_wagons)
        
        with col2:
            completed = metrics.get("retrofits_completed", 0)
            st.metric("Retrofitted", completed)
        
        with col3:
            completion_rate = (completed / total_wagons * 100) if total_wagons > 0 else 0
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        with col4:
            duration = metrics.get("simulation_duration_minutes", 0)
            st.metric("Duration", f"{duration:.1f} min")
    
    st.markdown("---")


def render_overview_tab(data: dict[str, Any]) -> None:
    """Render overview dashboard with KPI cards and charts."""
    st.header("📊 Overview Dashboard")
    
    if "metrics" not in data:
        st.warning("⚠️ No metrics data available")
        return
    
    metrics = data["metrics"]
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        trains = metrics.get("trains_arrived", 0)
        wagons = metrics.get("wagons_arrived", 0)
        st.metric("Trains / Wagons", f"{trains} / {wagons}")
    
    with col2:
        retrofitted = metrics.get("retrofits_completed", 0)
        rate = (retrofitted / wagons * 100) if wagons > 0 else 0
        st.metric("Retrofitted", f"{retrofitted} ({rate:.1f}%)")
    
    with col3:
        workshop_util = metrics.get("workshop_utilization", 0)
        st.metric("Workshop Utilization", f"{workshop_util:.1f}%")
    
    with col4:
        bottlenecks = len(data.get("bottlenecks", []))
        st.metric("Bottlenecks", bottlenecks)
    
    # Display generated charts
    output_dir = Path(st.session_state.get("output_dir", "output"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        kpi_chart = output_dir / "kpi_status.png"
        if kpi_chart.exists():
            st.subheader("KPI Status")
            st.image(str(kpi_chart), use_container_width=True)
    
    with col2:
        flow_chart = output_dir / "flow_analysis.png"
        if flow_chart.exists():
            st.subheader("Flow Analysis")
            st.image(str(flow_chart), use_container_width=True)
    
    dashboard_chart = output_dir / "operational_dashboard.png"
    if dashboard_chart.exists():
        st.subheader("Operational Dashboard")
        st.image(str(dashboard_chart), use_container_width=True)


def render_wagon_flow_tab(data: dict[str, Any]) -> None:
    """Render wagon flow analysis."""
    st.header("🚃 Wagon Flow Analysis")
    
    if "metrics" not in data:
        st.warning("⚠️ No metrics data available")
        return
    
    metrics = data["metrics"]
    
    # Wagon state distribution
    st.subheader("Wagon State Distribution")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        states = {
            "Retrofitted": metrics.get("retrofits_completed", 0),
            "Rejected": metrics.get("wagons_rejected", 0),
            "In Parking": metrics.get("wagons_parked", 0),
            "On Retrofit Track": metrics.get("wagons_on_retrofit_track", 0),
            "On Retrofitted Track": metrics.get("wagons_on_retrofitted_track", 0),
        }
        
        df_states = pd.DataFrame(list(states.items()), columns=["State", "Count"])
        st.bar_chart(df_states.set_index("State"))
    
    with col2:
        st.dataframe(df_states, use_container_width=True)
    
    # Event timeline
    if "events" in data and not data["events"].empty:
        st.subheader("Event Timeline")
        events_df = data["events"]
        
        # Filter controls
        event_types = events_df["event_type"].unique().tolist()
        selected_types = st.multiselect("Filter by event type", event_types, default=event_types[:5])
        
        filtered_events = events_df[events_df["event_type"].isin(selected_types)]
        st.dataframe(filtered_events.head(100), use_container_width=True)


def render_workshop_tab(data: dict[str, Any]) -> None:
    """Render workshop performance analysis."""
    st.header("🏭 Workshop Performance")
    
    if "workshop_metrics" not in data or data["workshop_metrics"].empty:
        st.warning("⚠️ No workshop metrics available")
        return
    
    workshop_df = data["workshop_metrics"]
    
    # Workshop comparison table
    st.subheader("Workshop Comparison")
    st.dataframe(workshop_df, use_container_width=True)
    
    # Utilization chart
    st.subheader("Workshop Utilization")
    st.bar_chart(workshop_df.set_index("workshop_id")["utilization_percent"])
    
    # Throughput chart
    st.subheader("Throughput (wagons/hour)")
    st.bar_chart(workshop_df.set_index("workshop_id")["throughput_per_hour"])


def render_locomotive_tab(data: dict[str, Any]) -> None:
    """Render locomotive operations analysis."""
    st.header("🚂 Locomotive Operations")
    
    if "locomotive_util" not in data or data["locomotive_util"].empty:
        st.warning("⚠️ No locomotive utilization data available")
        return
    
    loco_df = data["locomotive_util"]
    
    # Check if coupling/decoupling data exists
    has_coupling = (loco_df["coupling_percent"].sum() > 0 or 
                    loco_df["decoupling_percent"].sum() > 0)
    
    # Utilization table
    st.subheader("Locomotive Utilization Breakdown")
    
    if has_coupling:
        display_df = loco_df[["locomotive_id", "parking_percent", "moving_percent", 
                              "coupling_percent", "decoupling_percent"]]
        chart_cols = ["parking_percent", "moving_percent", "coupling_percent", "decoupling_percent"]
    else:
        display_df = loco_df[["locomotive_id", "parking_percent", "moving_percent"]]
        chart_cols = ["parking_percent", "moving_percent"]
        st.info("ℹ️ Coupling/decoupling operations not tracked in this simulation")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Stacked bar chart
    st.subheader("Activity Distribution")
    chart_data = loco_df.set_index("locomotive_id")[chart_cols]
    st.bar_chart(chart_data)


def render_track_capacity_tab(data: dict[str, Any]) -> None:
    """Render track capacity analysis."""
    st.header("🛤️ Track Capacity")
    
    if "track_capacity" not in data or data["track_capacity"].empty:
        st.warning("⚠️ No track capacity data available")
        return
    
    track_df = data["track_capacity"]
    
    # Track utilization grid
    st.subheader("Track Utilization")
    
    # Color-code by utilization
    def color_utilization(val: float) -> str:
        if val >= 85:
            return "background-color: #DC3545"  # Red
        elif val >= 70:
            return "background-color: #FFC107"  # Yellow
        else:
            return "background-color: #28A745"  # Green
    
    styled_df = track_df.style.applymap(
        color_utilization, subset=["utilization_percent"]
    )
    st.dataframe(styled_df, use_container_width=True)
    
    # Utilization chart
    st.subheader("Track Utilization Chart")
    st.bar_chart(track_df.set_index("track_id")["utilization_percent"])


def render_bottleneck_tab(data: dict[str, Any]) -> None:
    """Render bottleneck analysis."""
    st.header("⚠️ Bottleneck Analysis")
    
    if "bottlenecks" not in data or data["bottlenecks"].empty:
        st.success("✅ No bottlenecks detected")
        return
    
    bottleneck_df = data["bottlenecks"]
    
    # Summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        workshop_bottlenecks = len(bottleneck_df[bottleneck_df["resource_type"] == "workshop"])
        st.metric("Workshop Bottlenecks", workshop_bottlenecks)
    
    with col2:
        track_bottlenecks = len(bottleneck_df[bottleneck_df["resource_type"] == "track"])
        st.metric("Track Bottlenecks", track_bottlenecks)
    
    with col3:
        loco_bottlenecks = len(bottleneck_df[bottleneck_df["resource_type"] == "locomotive"])
        st.metric("Locomotive Bottlenecks", loco_bottlenecks)
    
    # Bottleneck details table
    st.subheader("Bottleneck Details")
    st.dataframe(bottleneck_df, use_container_width=True)


def render_event_log_tab(data: dict[str, Any]) -> None:
    """Render event log viewer."""
    st.header("🔍 Event Log Viewer")
    
    if "events" not in data or data["events"].empty:
        st.warning("⚠️ No event data available")
        return
    
    events_df = data["events"]
    
    # Filter controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search events", placeholder="Enter search term...")
    
    with col2:
        show_lines = st.number_input("Show lines", min_value=10, max_value=1000, value=100, step=10)
    
    # Event type filter
    event_types = events_df["event_type"].unique().tolist()
    selected_types = st.multiselect("Filter by event type", event_types, default=event_types)
    
    # Apply filters
    filtered_df = events_df[events_df["event_type"].isin(selected_types)]
    
    if search_term:
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # Display table
    st.dataframe(filtered_df.head(show_lines), use_container_width=True)
    st.caption(f"Showing {min(show_lines, len(filtered_df))} of {len(filtered_df)} events")


def render_process_log_tab(data: dict[str, Any]) -> None:
    """Render process log viewer."""
    st.header("📋 Process Log Viewer")
    
    if "process_log" not in data or data["process_log"].empty:
        st.warning("⚠️ No process log data available")
        return
    
    process_df = data["process_log"]
    
    # Filter controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search process log", placeholder="Enter search term...")
    
    with col2:
        show_lines = st.number_input("Show lines", min_value=10, max_value=1000, value=100, step=10, key="process_lines")
    
    # Process type filter
    if "process" in process_df.columns:
        process_types = process_df["process"].unique().tolist()
        selected_processes = st.multiselect("Filter by process", process_types, default=process_types)
        filtered_df = process_df[process_df["process"].isin(selected_processes)]
    else:
        filtered_df = process_df
    
    if search_term:
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # Display table
    st.dataframe(filtered_df.head(show_lines), use_container_width=True)
    st.caption(f"Showing {min(show_lines, len(filtered_df))} of {len(filtered_df)} process entries")


def main() -> None:
    """Main dashboard application."""
    # Sidebar
    st.sidebar.header("📁 Load Simulation Results")
    
    output_dir = st.sidebar.text_input(
        "Output Directory",
        value="output",
        help="Path to simulation output directory"
    )
    
    st.session_state["output_dir"] = output_dir
    output_path = Path(output_dir)
    
    if not output_path.exists():
        st.error(f"❌ Directory not found: {output_dir}")
        st.stop()
    
    # Load data
    with st.spinner("Loading simulation data..."):
        data = load_dashboard_data(output_path)
    
    if not data:
        st.error("❌ No data files found in output directory")
        st.stop()
    
    # Render header
    render_header(data)
    
    # Main tabs
    tabs = st.tabs([
        "📊 Overview",
        "🚃 Wagon Flow",
        "🏭 Workshop",
        "🚂 Locomotive",
        "🛤️ Track Capacity",
        "⚠️ Bottlenecks",
        "🔍 Event Log",
        "📋 Process Log"
    ])
    
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
        render_bottleneck_tab(data)
    
    with tabs[6]:
        render_event_log_tab(data)
    
    with tabs[7]:
        render_process_log_tab(data)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**PopUpSim Dashboard**\n\n"
        "Post-simulation analysis dashboard.\n\n"
        "📂 Load output directory to view results."
    )


if __name__ == "__main__":
    main()
