"""Bottleneck analysis tab - visualizes timeline data for bottleneck identification."""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st


def render_bottleneck_tab(data: dict[str, Any]) -> None:
    """Render bottleneck analysis tab."""
    st.header('🚧 Bottleneck Analysis')

    timeline = data.get('timeline')

    if timeline is None or timeline.empty:
        st.warning('⚠️ No timeline data available')
        return

    st.info('📊 Timeline data shows per-track queue lengths and resource utilization over time')

    # Show timeline columns
    st.subheader('Available Metrics')

    # Separate columns by type
    track_cols = [col for col in timeline.columns if col.startswith('track_')]
    workshop_cols = [col for col in timeline.columns if col.startswith('workshop_')]
    resource_cols = [col for col in timeline.columns if col in ['locomotives_busy', 'wagons_in_process']]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('**Track Queues:**')
        for col in track_cols:
            max_val = timeline[col].max()
            st.write(f'- {col}: max {max_val:.0f} wagons')

    with col2:
        st.markdown('**Workshop Utilization:**')
        for col in workshop_cols:
            max_val = timeline[col].max()
            st.write(f'- {col}: max {max_val:.0f} bays')

    with col3:
        st.markdown('**Resource Usage:**')
        for col in resource_cols:
            max_val = timeline[col].max()
            st.write(f'- {col}: max {max_val:.0f}')

    # Plot track queue lengths over time
    if track_cols:
        st.subheader('Track Queue Lengths Over Time')

        fig, ax = plt.subplots(figsize=(12, 6))

        for col in track_cols:
            ax.plot(timeline['timestamp'], timeline[col], label=col.replace('track_', ''), linewidth=2)

        ax.set_xlabel('Simulation Time (minutes)', fontsize=11)
        ax.set_ylabel('Wagons in Queue', fontsize=11)
        ax.set_title('Track Queue Lengths', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(alpha=0.3)
        plt.tight_layout()

        st.pyplot(fig)
        plt.close()

    # Show raw timeline data
    with st.expander('📋 Raw Timeline Data'):
        st.dataframe(timeline, use_container_width=True)
