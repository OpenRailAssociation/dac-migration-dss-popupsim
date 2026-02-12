"""Track capacity tab - visualizes track utilization and capacity."""

from typing import Any

import streamlit as st


def render_track_capacity_tab(data: dict[str, Any]) -> None:
    """Render track capacity analysis tab."""
    st.header('🛤️ Track Capacity')

    track_capacity = data.get('track_capacity')

    if track_capacity is None or track_capacity.empty:
        st.warning('⚠️ No track capacity data available')
        return

    # Get latest capacity state for each track
    latest_capacity = track_capacity.groupby('track_id').last().reset_index()

    # Calculate utilization percentage
    latest_capacity['utilization_percent'] = (latest_capacity['used_after'] / latest_capacity['capacity'] * 100).fillna(
        0
    )

    # Section 1: Track Utilization Overview
    st.subheader('Track Utilization Overview')

    col1, col2 = st.columns([2, 1])

    with col1:
        # Utilization bar chart
        st.bar_chart(latest_capacity.set_index('track_id')['utilization_percent'])

    with col2:
        # Summary metrics
        avg_util = latest_capacity['utilization_percent'].mean()
        max_util = latest_capacity['utilization_percent'].max()

        st.metric('Average Utilization', f'{avg_util:.1f}%')
        st.metric('Max Utilization', f'{max_util:.1f}%')

        # Count tracks by utilization level
        high_util = len(latest_capacity[latest_capacity['utilization_percent'] >= 85])
        medium_util = len(
            latest_capacity[
                (latest_capacity['utilization_percent'] >= 70) & (latest_capacity['utilization_percent'] < 85)
            ]
        )
        low_util = len(latest_capacity[latest_capacity['utilization_percent'] < 70])

        st.write(f'🔴 High (≥85%): {high_util}')
        st.write(f'🟡 Medium (70-85%): {medium_util}')
        st.write(f'🟢 Low (<70%): {low_util}')

    st.markdown('---')

    # Section 2: Detailed Track Capacity Table
    st.subheader('Track Capacity Details')

    # Color-code by utilization
    def color_utilization(val: float) -> str:
        if val >= 85:
            return 'background-color: #DC3545; color: white'  # Red
        elif val >= 70:
            return 'background-color: #FFC107; color: black'  # Yellow
        else:
            return 'background-color: #28A745; color: white'  # Green

    display_df = latest_capacity[['track_id', 'capacity', 'used_after', 'utilization_percent']].copy()
    display_df.columns = ['Track ID', 'Capacity (wagons)', 'Used', 'Utilization (%)']

    # Apply styling only to numeric columns
    styled_df = display_df.style.apply(
        lambda x: [
            color_utilization(v) if isinstance(v, (int, float)) and x.name == 'Utilization (%)' else '' for v in x
        ],
        axis=0,
    ).format({'Utilization (%)': '{:.1f}', 'Capacity (wagons)': '{:.0f}', 'Used': '{:.0f}'})

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    st.markdown('---')

    # Section 3: Track Capacity Over Time
    st.subheader('Track Capacity Over Time')

    # Select tracks to visualize
    all_tracks = sorted(track_capacity['track_id'].unique())
    selected_tracks = st.multiselect(
        'Select tracks to visualize:', options=all_tracks, default=all_tracks[:5] if len(all_tracks) > 5 else all_tracks
    )

    if selected_tracks:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 6))

        for track_id in selected_tracks:
            track_data = track_capacity[track_capacity['track_id'] == track_id].sort_values('timestamp')
            if not track_data.empty:
                ax.plot(
                    track_data['timestamp'],
                    track_data['used_after'],
                    label=track_id,
                    linewidth=2,
                    marker='o',
                    markersize=3,
                )

        ax.set_xlabel('Simulation Time (minutes)', fontsize=11)
        ax.set_ylabel('Wagons on Track', fontsize=11)
        ax.set_title('Track Occupancy Over Time', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(alpha=0.3)
        plt.tight_layout()

        st.pyplot(fig)
        plt.close()
    else:
        st.info('Select tracks to visualize capacity over time')
