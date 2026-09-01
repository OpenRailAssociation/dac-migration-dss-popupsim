"""Animation tab - animated playback of a simulation run.

Renders a schematic yard (metric track lanes + a connecting throat) and plays
back wagon / locomotive movements over time using Plotly's native frame
animation (client-side play / pause / scrub). Resources are drawn as flat,
non-overlapping, train-like rectangles sized by their real length.

All heavy data preparation lives in
:mod:`dashboard_components.animation_data` (pure, unit-tested); this module
only handles Streamlit controls and Plotly figure assembly.
"""

from string import Template
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components

from dashboard_components import animation_data as ad
from dashboard_components import routes_graph as rg

# Rectangle height in lane units (nominal: the y-axis is a lane index, not
# metric, so true 3 m would render as an invisible hairline against a yard that
# is hundreds of metres tall). Length, by contrast, is true-to-metre.
_RECT_HEIGHT = 0.5
_LANE_HALF_HEIGHT = 0.36
_TRACK_LINE_WIDTH = 5
_LABEL_OFFSET_M = 14.0
_MIN_FRAME_MS = 20

# Selectable animation resolutions on a roughly quadratic scale: fine steps at
# the low end, coarse jumps toward the (very large) high end.
_RESOLUTION_OPTIONS = [200, 300, 500, 900, 1500, 2200, 3100, 4200, 5400, 6800, 8300, 10000]
# Above this many frames the embedded figure JSON gets large and the browser
# may become sluggish, so we surface a heads-up.
_HEAVY_FRAME_COUNT = 2000

# The animated figure is embedded as raw HTML (not via ``st.plotly_chart``) so
# that custom previous/next buttons can drive ``Plotly.animate`` entirely in the
# browser, staying in sync with the native play/pause and slider.
_PLOT_DIV_ID = 'yard-animation'
# ``string.Template`` ($-substitution) avoids escaping every brace in the JS.
_CONTROLS_TEMPLATE = Template(
    """
<div class="yard-controls">
  <button type="button" id="${div}-prev" class="yard-btn">⏮ Previous frame</button>
  <button type="button" id="${div}-next" class="yard-btn">⏭ Next frame</button>
  <span class="yard-frame" id="${div}-label"></span>
</div>
<style>
  .yard-controls { display:flex; align-items:center; gap:8px; margin:2px 0 0 6px;
                   font-family:"Source Sans Pro",sans-serif; }
  .yard-btn { padding:4px 12px; border:1px solid #ccc; border-radius:6px;
              background:#f6f6f6; cursor:pointer; font-size:14px; }
  .yard-btn:hover { background:#e9e9e9; }
  .yard-frame { color:#555; font-size:13px; }
</style>
<script>
(function() {
  var divId = "$div";
  var N = $n;
  var cur = 0;
  function gd() { return document.getElementById(divId); }
  function clamp(i) { return Math.max(0, Math.min(N - 1, i)); }
  function refresh() {
    var label = document.getElementById(divId + "-label");
    if (label) { label.textContent = "Frame " + (cur + 1) + " / " + N; }
  }
  function go(i) {
    cur = clamp(i);
    Plotly.animate(gd(), [String(cur)],
      {mode: "immediate", frame: {duration: 0, redraw: true}, transition: {duration: 0}});
    refresh();
  }
  function wire() {
    document.getElementById(divId + "-prev").addEventListener("click", function() { go(cur - 1); });
    document.getElementById(divId + "-next").addEventListener("click", function() { go(cur + 1); });
    // The native play button and slider both animate by frame name, so this one
    // handler keeps "cur" in sync with every kind of navigation.
    gd().on("plotly_animatingframe", function(e) {
      if (e && e.name !== undefined && e.name !== null) {
        var idx = parseInt(e.name, 10);
        if (!isNaN(idx)) { cur = idx; refresh(); }
      }
    });
    refresh();
  }
  function ready() {
    var g = gd();
    if (window.Plotly && g && g._fullLayout) { wire(); }
    else { setTimeout(ready, 60); }
  }
  ready();
})();
</script>
"""
)


@st.cache_data(show_spinner=False)
def _compute_animation(  # noqa: PLR0913  # pylint: disable=too-many-arguments,too-many-positional-arguments
    resource_locations: pd.DataFrame | None,
    resource_states: pd.DataFrame | None,
    layout_config: dict[str, Any],
    num_frames: int,
    rejected_wagons: pd.DataFrame | None = None,
    track_capacity: pd.DataFrame | None = None,
) -> tuple[ad.YardLayout, list[ad.FrameData]]:
    """Build (and cache) the yard layout and per-frame rectangle arrays.

    Cached on the raw inputs + resolution so scrubbing/replaying is instant.
    ``layout_config`` bundles the ``tracks`` / ``topology`` / ``workshops`` /
    ``routes`` config plus the ``wagon_lengths`` map. ``rejected_wagons`` feeds
    the cumulative rejected-wagon counter.
    """
    route_graph = rg.parse_routes(layout_config.get('routes'))
    active = ad.active_track_ids(resource_locations, route_graph)
    layout = ad.build_layout(
        layout_config.get('tracks', []),
        layout_config.get('topology', {}),
        layout_config.get('workshops', []),
        route_graph,
        active,
    )
    timelines = ad.extract_timelines(resource_locations, resource_states, layout_config.get('wagon_lengths', {}))
    cap_tl = ad.parse_capacity_timeline(track_capacity)
    frames = ad.build_frames(
        layout, timelines, num_frames, rejected_at=ad.rejected_times(rejected_wagons), capacity_timeline=cap_tl
    )
    return layout, frames


def _rect_polygons(
    xs: list[float], ys: list[float], lengths: list[float]
) -> tuple[list[float | None], list[float | None]]:
    """Build None-separated polygon corner arrays for a set of rectangles."""
    poly_x: list[float | None] = []
    poly_y: list[float | None] = []
    half_h = _RECT_HEIGHT / 2.0
    for xc, yc, length in zip(xs, ys, lengths, strict=False):
        half_l = length / 2.0
        poly_x.extend([xc - half_l, xc + half_l, xc + half_l, xc - half_l, xc - half_l, None])
        poly_y.extend([yc - half_h, yc - half_h, yc + half_h, yc + half_h, yc - half_h, None])
    return poly_x, poly_y


def _rect_trace(xs: list[float], ys: list[float], lengths: list[float], color: str, line_color: str) -> go.Scatter:
    """Build a single filled-rectangle Scatter trace (one colour group)."""
    poly_x, poly_y = _rect_polygons(xs, ys, lengths)
    return go.Scatter(
        x=poly_x,
        y=poly_y,
        mode='lines',
        fill='toself',
        fillcolor=color,
        line={'color': line_color, 'width': 1.1},
        hoverinfo='skip',
        showlegend=False,
    )


_WAGON_BORDER_PENDING = '#013a63'
_WAGON_BORDER_DONE = '#04503a'
_LOCO_BORDER = '#f1c40f'
_STATS_FONT = {'size': 17, 'color': '#2c3e50'}
_UTIL_FONT_SIZE = 16
_UTIL_OFFSET_M = 30.0  # gap past a track's throat end for its utilization label (toward middle)


def _wagon_groups(frame: ad.FrameData) -> dict[tuple[str, int], dict[str, list[float]]]:
    """Group a frame's wagons by (status, shade) so each renders in its own shade."""
    groups: dict[tuple[str, int], dict[str, list[float]]] = {
        (status, shade): {'x': [], 'y': [], 'len': []} for status in ('pending', 'done') for shade in (0, 1)
    }
    rows = zip(frame.wagon_x, frame.wagon_y, frame.wagon_len, frame.wagon_color, frame.wagon_shade, strict=False)
    for x, y, length, color, shade in rows:
        status = 'done' if color == ad.WAGON_COLOR_DONE else 'pending'
        group = groups[(status, shade)]
        group['x'].append(x)
        group['y'].append(y)
        group['len'].append(length)
    return groups


def _label_trace(frame: ad.FrameData, show_labels: bool) -> go.Scatter:
    """Build the hover/label trace carrying every resource id."""
    return go.Scatter(
        x=frame.wagon_x + frame.loco_x,
        y=frame.wagon_y + frame.loco_y,
        mode='markers+text' if show_labels else 'markers',
        marker={'size': 12, 'color': 'rgba(0,0,0,0)'},
        text=frame.wagon_ids + frame.loco_ids,
        textposition='middle center',
        textfont={'size': 6, 'color': '#ffffff'},
        hovertemplate='%{text}<extra></extra>',
        showlegend=False,
    )


def _counters_trace(frame: ad.FrameData, layout: ad.YardLayout) -> go.Scatter:
    """Build the live counters text block, placed above the layout."""
    s = frame.stats
    text = (
        f'<b>To retrofit: {s.to_retrofit}<br>'
        f'Retrofitted: {s.cumulative_retrofitted}<br>'
        f'Rejected: {s.cumulative_rejected}</b>'
    )
    if layout.mode == 'zones':
        x = (layout.left_throat_x + layout.right_throat_x) / 2.0
        y = layout.y_max + 0.7
    else:
        x = layout.x_max * 0.5
        y = layout.y_max + 0.5
    return go.Scatter(
        x=[x],
        y=[y],
        mode='text',
        text=[text],
        textposition='middle center',
        textfont=_STATS_FONT,
        hoverinfo='skip',
        showlegend=False,
    )


def _utilization_trace(frame: ad.FrameData, layout: ad.YardLayout) -> go.Scatter:
    """Build the per-track capacity-usage labels (one '%' per non-mainline lane)."""
    xs: list[float] = []
    ys: list[float] = []
    texts: list[str] = []
    colors: list[str] = []
    for track_id, usage in frame.stats.utilization.items():
        tl = layout.tracks.get(track_id)
        if tl is None:
            continue
        # Place the label on the throat (inner) side: right of throat for the
        # left panel, left of throat for the right panel.
        if abs(tl.throat_x - tl.x_end) < 1e-9:
            xs.append(tl.x_end + _UTIL_OFFSET_M)
        else:
            xs.append(tl.x_start - _UTIL_OFFSET_M)
        ys.append(tl.lane_y)
        texts.append(f'{usage * 100:.0f}%')
        colors.append('#c0392b' if usage > 1.0 else '#34495e')
    return go.Scatter(
        x=xs,
        y=ys,
        mode='text',
        text=texts,
        textposition='middle center',
        textfont={'size': _UTIL_FONT_SIZE, 'color': colors or '#34495e'},
        hoverinfo='skip',
        showlegend=False,
    )


def _dynamic_traces(frame: ad.FrameData, layout: ad.YardLayout, show_labels: bool) -> list[go.Scatter]:
    """Build the per-frame traces (4 wagon shade groups, locos, labels, stats)."""
    groups = _wagon_groups(frame)
    return [
        _rect_trace(*_unpack(groups[('pending', 0)]), ad.WAGON_SHADES_PENDING[0], _WAGON_BORDER_PENDING),
        _rect_trace(*_unpack(groups[('pending', 1)]), ad.WAGON_SHADES_PENDING[1], _WAGON_BORDER_PENDING),
        _rect_trace(*_unpack(groups[('done', 0)]), ad.WAGON_SHADES_DONE[0], _WAGON_BORDER_DONE),
        _rect_trace(*_unpack(groups[('done', 1)]), ad.WAGON_SHADES_DONE[1], _WAGON_BORDER_DONE),
        _rect_trace(frame.loco_x, frame.loco_y, frame.loco_len, ad.LOCO_COLOR, _LOCO_BORDER),
        _label_trace(frame, show_labels),
        _counters_trace(frame, layout),
        _utilization_trace(frame, layout),
    ]


_DYNAMIC_TRACE_COUNT = 8


def _unpack(group: dict[str, list[float]]) -> tuple[list[float], list[float], list[float]]:
    """Return the (x, y, len) arrays of a wagon group."""
    return group['x'], group['y'], group['len']


def _legend_traces() -> list[go.Scatter]:
    """Legend-only marker traces (no data points)."""
    entries = [
        ('Wagon · to retrofit', ad.WAGON_COLOR_PENDING, 'square'),
        ('Wagon · retrofitted', ad.WAGON_COLOR_DONE, 'square'),
        ('Locomotive', ad.LOCO_COLOR, 'square'),
        ('Workshop', ad.TRACK_TYPE_COLORS['workshop'], 'square'),
    ]
    return [
        go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            name=name,
            marker={'color': color, 'symbol': symbol, 'size': 12, 'line': {'color': '#222', 'width': 1}},
            showlegend=True,
            hoverinfo='skip',
        )
        for name, color, symbol in entries
    ]


def _add_static_geometry(fig: go.Figure, layout: ad.YardLayout) -> None:
    """Draw the static yard skeleton, dispatching on the layout mode."""
    if layout.mode == 'zones':
        _add_zone_geometry(fig, layout)
    else:
        _add_single_geometry(fig, layout)


def _track_line(fig: go.Figure, tl: ad.TrackLayout) -> None:
    """Draw a single track as a workshop box or a plain horizontal line."""
    if tl.is_workshop:
        _draw_workshop(fig, tl)
    else:
        fig.add_shape(
            type='line',
            x0=tl.x_start,
            y0=tl.lane_y,
            x1=tl.x_end,
            y1=tl.lane_y,
            line={'color': tl.color, 'width': _TRACK_LINE_WIDTH},
            opacity=0.5,
            layer='below',
        )


def _add_single_geometry(fig: go.Figure, layout: ad.YardLayout) -> None:
    """Single-column layout: one vertical throat with stacked lanes."""
    y_lo, y_hi = layout.y_min - 0.6, layout.y_max + 0.6
    fig.add_shape(
        type='line',
        x0=layout.throat_x,
        y0=y_lo,
        x1=layout.throat_x,
        y1=y_hi,
        line={'color': '#bdc3c7', 'width': 3, 'dash': 'dot'},
        layer='below',
    )
    for tl in layout.tracks.values():
        if tl.track_type == 'mainline':
            fig.add_shape(
                type='line',
                x0=layout.throat_x,
                y0=tl.lane_y,
                x1=layout.x_max,
                y1=tl.lane_y,
                line={'color': tl.color, 'width': 9},
                opacity=0.85,
                layer='below',
            )
        else:
            _track_line(fig, tl)
        fig.add_annotation(
            x=layout.throat_x - _LABEL_OFFSET_M,
            y=tl.lane_y,
            text=tl.track_id,
            showarrow=False,
            xanchor='right',
            font={'size': 9, 'color': '#555'},
        )


def _add_zone_geometry(fig: go.Figure, layout: ad.YardLayout) -> None:
    """Three-zone layout: local yard | Mainline corridor | remote storage."""
    y_lo, y_hi = layout.y_min - 0.6, layout.y_max + 0.6
    fig.add_shape(
        type='rect',
        x0=0,
        y0=y_lo,
        x1=layout.left_throat_x,
        y1=y_hi,
        fillcolor='#2980b9',
        opacity=0.04,
        line={'width': 0},
        layer='below',
    )
    fig.add_shape(
        type='rect',
        x0=layout.right_throat_x,
        y0=y_lo,
        x1=layout.x_max,
        y1=y_hi,
        fillcolor='#8e44ad',
        opacity=0.04,
        line={'width': 0},
        layer='below',
    )
    for ladder_x in (layout.left_throat_x, layout.right_throat_x):
        fig.add_shape(
            type='line',
            x0=ladder_x,
            y0=y_lo,
            x1=ladder_x,
            y1=y_hi,
            line={'color': '#bdc3c7', 'width': 3, 'dash': 'dot'},
            layer='below',
        )
    main_color = ad.TRACK_TYPE_COLORS['mainline']
    fig.add_shape(
        type='line',
        x0=layout.left_throat_x,
        y0=layout.corridor_y,
        x1=layout.right_throat_x,
        y1=layout.corridor_y,
        line={'color': main_color, 'width': 9},
        opacity=0.85,
        layer='below',
    )
    for tl in layout.tracks.values():
        if tl.track_type == 'mainline':
            continue
        _track_line(fig, tl)
        if tl.zone == 'right':
            label_x, anchor = tl.x_end + _LABEL_OFFSET_M, 'left'
        else:
            label_x, anchor = tl.x_start - _LABEL_OFFSET_M, 'right'
        fig.add_annotation(
            x=label_x, y=tl.lane_y, text=tl.track_id, showarrow=False, xanchor=anchor, font={'size': 9, 'color': '#555'}
        )
    _add_zone_titles(fig, layout)


def _add_zone_titles(fig: go.Figure, layout: ad.YardLayout) -> None:
    """Add the three zone headings below the layout."""
    y = layout.corridor_y - 0.7
    titles = [
        (layout.left_throat_x / 2.0, 'Local retrofit yard', '#2471a3'),
        ((layout.left_throat_x + layout.right_throat_x) / 2.0, '🚆 Main line', '#566573'),
        ((layout.right_throat_x + layout.x_max) / 2.0, 'Arrival / remote storage', '#6c3483'),
    ]
    for x, text, color in titles:
        fig.add_annotation(x=x, y=y, text=text, showarrow=False, font={'size': 11, 'color': color})


def _draw_workshop(fig: go.Figure, tl: ad.TrackLayout) -> None:
    """Draw a workshop as a labeled building box with one divider per bay."""
    fig.add_shape(
        type='rect',
        x0=tl.x_start,
        y0=tl.lane_y - _LANE_HALF_HEIGHT,
        x1=tl.x_end,
        y1=tl.lane_y + _LANE_HALF_HEIGHT,
        line={'color': tl.color, 'width': 2},
        fillcolor=tl.color,
        opacity=0.18,
        layer='below',
    )
    bays = tl.bays or 1
    for i in range(1, bays):
        x = tl.x_start + (tl.x_end - tl.x_start) * i / bays
        fig.add_shape(
            type='line',
            x0=x,
            y0=tl.lane_y - _LANE_HALF_HEIGHT,
            x1=x,
            y1=tl.lane_y + _LANE_HALF_HEIGHT,
            line={'color': tl.color, 'width': 1, 'dash': 'dot'},
            layer='below',
        )
    bay_label = f' · {tl.bays} bays' if tl.bays else ''
    fig.add_annotation(
        x=(tl.x_start + tl.x_end) / 2,
        y=tl.lane_y + _LANE_HALF_HEIGHT,
        text=f'🏭 {tl.track_id}{bay_label}',
        showarrow=False,
        yanchor='bottom',
        font={'size': 9, 'color': '#1e5631'},
    )


def _animation_controls(
    frames: list[ad.FrameData], frame_ms: int, active: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build the play/pause buttons (updatemenus) and the time slider."""
    play_args = {'frame': {'duration': frame_ms, 'redraw': True}, 'fromcurrent': True, 'transition': {'duration': 0}}
    pause_args = {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate', 'transition': {'duration': 0}}
    slider_steps = [
        {
            'args': [
                [str(i)],
                {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}},
            ],
            'label': f.datetime_label,
            'method': 'animate',
        }
        for i, f in enumerate(frames)
    ]
    updatemenus = [
        {
            'type': 'buttons',
            'direction': 'left',
            'x': 0,
            'y': -0.04,
            'xanchor': 'left',
            'yanchor': 'top',
            'pad': {'r': 8, 't': 8},
            'buttons': [
                {'label': '▶ Play', 'method': 'animate', 'args': [None, play_args]},
                {'label': '⏸ Pause', 'method': 'animate', 'args': [[None], pause_args]},
            ],
        }
    ]
    sliders = [
        {
            'active': active,
            'x': 0.12,
            'len': 0.88,
            'xanchor': 'left',
            'y': -0.04,
            'yanchor': 'top',
            'currentvalue': {'prefix': 'Time: ', 'font': {'size': 13}},
            'pad': {'t': 8},
            'steps': slider_steps,
        }
    ]
    return updatemenus, sliders


def _build_figure(
    layout: ad.YardLayout, frames: list[ad.FrameData], frame_ms: int, show_labels: bool, active_frame: int = 0
) -> go.Figure:
    """Assemble the full animated Plotly figure, opened at ``active_frame``."""
    active = max(0, min(active_frame, len(frames) - 1))
    first = frames[active]
    fig = go.Figure(data=[*_dynamic_traces(first, layout, show_labels), *_legend_traces()])
    _add_static_geometry(fig, layout)

    fig.frames = [
        go.Frame(name=str(i), data=_dynamic_traces(f, layout, show_labels), traces=list(range(_DYNAMIC_TRACE_COUNT)))
        for i, f in enumerate(frames)
    ]

    updatemenus, sliders = _animation_controls(frames, frame_ms, active)
    fig.update_layout(
        height=max(520, len(layout.tracks) * 28),
        margin={'l': 10, 'r': 40, 't': 30, 'b': 10},
        plot_bgcolor='white',
        xaxis={'visible': False, 'range': [-_LABEL_OFFSET_M * 5, layout.x_max + _LABEL_OFFSET_M * 4]},
        yaxis={'visible': False, 'range': [layout.y_min - 1.8, layout.y_max + 1.9]},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'left', 'x': 0},
        updatemenus=updatemenus,
        sliders=sliders,
    )
    return fig


def _render_controls() -> tuple[int, int, float, bool]:
    """Render the playback control widgets.

    Returns ``(num_frames, length_s, speed, show_labels)``.
    """
    col1, col2, col3 = st.columns(3)
    with col1:
        num_frames = st.selectbox(
            'Resolution (frames)',
            options=_RESOLUTION_OPTIONS,
            index=0,
            help='More frames = smoother motion and finer stepping, but a larger figure. '
            'The scale is quadratic, from 200 up to 10,000 frames.',
        )
    with col2:
        anim_length_s = st.slider(
            'Animation length (s)',
            min_value=5,
            max_value=120,
            value=30,
            step=5,
            help='Wall-clock duration of one full playback.',
        )
    with col3:
        speed = st.select_slider('Playback speed', options=[0.25, 0.5, 1.0, 2.0, 4.0], value=1.0)
    show_labels = st.checkbox('Show wagon / locomotive ids on rectangles', value=False)
    return num_frames, anim_length_s, speed, show_labels


def _render_player(fig: go.Figure, num_frames: int) -> None:
    """Embed the animated figure as HTML with client-side previous/next buttons.

    Rendering through :func:`streamlit.components.v1.html` (instead of
    ``st.plotly_chart``) lets the prev/next buttons call ``Plotly.animate`` in
    the browser, so stepping never triggers a Streamlit rerun and stays in sync
    with the native play/pause and slider.
    """
    plot_html = pio.to_html(
        fig,
        include_plotlyjs='cdn',
        full_html=False,
        auto_play=False,
        div_id=_PLOT_DIV_ID,
        config={
            'responsive': True,
            'displayModeBar': True,
            'toImageButtonOptions': {'format': 'png', 'filename': 'yard_animation'},
        },
    )
    controls = _CONTROLS_TEMPLATE.safe_substitute(div=_PLOT_DIV_ID, n=num_frames)
    height = int(fig.layout.height or 520) + 70
    components.html(f'<div class="yard-player">{plot_html}{controls}</div>', height=height, scrolling=False)


def render_animation_tab(data: dict[str, Any]) -> None:  # pylint: disable=too-many-locals
    """Render the animated simulation playback tab."""
    st.header('🎬 Simulation Animation')
    st.caption(
        'Playback of wagon and locomotive movements through the yard. Resources are flat, '
        'length-accurate rectangles: wagons blue until retrofitted then green, locomotives dark. '
        'Wagons pack flush (no gap) and alternate shade so they stay countable. Live counters and '
        'per-track capacity usage update as the clock advances.'
    )

    resource_locations = data.get('resource_locations')
    resource_states = data.get('resource_states')
    if resource_locations is None or resource_locations.empty:
        st.warning('⚠️ No `resource_locations.csv` found for this scenario — cannot build the animation.')
        return

    scenario_config = data.get('scenario_config', {})
    tracks_config = scenario_config.get('tracks', {}).get('tracks', [])
    topology = scenario_config.get('topology', {})
    workshops_config = scenario_config.get('workshops', {}).get('workshops', [])
    lengths = ad.wagon_lengths(scenario_config.get('train_schedule'))
    if not tracks_config:
        st.warning('⚠️ No track configuration found — cannot build the yard layout.')
        return

    num_frames, anim_length_s, speed, show_labels = _render_controls()

    with st.spinner('Preparing animation...'):
        layout, frames = _compute_animation(
            resource_locations,
            resource_states,
            {
                'tracks': tracks_config,
                'topology': topology,
                'workshops': workshops_config,
                'routes': scenario_config.get('routes'),
                'wagon_lengths': lengths,
            },
            num_frames,
            data.get('rejected_wagons'),
            data.get('track_capacity'),
        )

    if not frames:
        st.info('No movement data available to animate for this scenario.')
        return

    if num_frames >= _HEAVY_FRAME_COUNT:
        st.warning(
            f'⚠️ {num_frames:,} frames produces a large figure — playback and stepping may be sluggish '
            'in the browser. Lower the resolution if it feels slow.'
        )

    frame_ms = max(_MIN_FRAME_MS, int(anim_length_s * 1000 / num_frames / speed))
    fig = _build_figure(layout, frames, frame_ms, show_labels)
    _render_player(fig, len(frames))
    st.caption(
        f'{len(frames)} frames · {len(layout.tracks)} tracks · x-axis in metres along track · '
        f'press ▶ Play, drag the slider or use ⏮ / ⏭ to step a single frame, hover a rectangle for its id. '
        f'(Loads Plotly from a CDN — needs internet on first paint.)'
    )
