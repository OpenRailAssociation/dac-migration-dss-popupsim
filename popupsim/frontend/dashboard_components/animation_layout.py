"""Schematic yard geometry for the simulation animation.

Builds the metric track-lane layout used by :mod:`dashboard_components.animation_data`:
three zones when routes span the Mainline (local yard on the left, Mainline
corridor in the middle, remote/arrival storage on the right), or a single
stacked column otherwise. Kept free of Streamlit / Plotly imports so the
geometry stays unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dashboard_components import routes_graph as rg

# --- Visual constants (mirrors scenario_tab for consistency) ----------------

TRACK_TYPE_ORDER: list[str] = [
    'mainline',
    'collection',
    'retrofit',
    'workshop',
    'retrofitted',
    'parking',
    'rescource_parking',
]

TRACK_TYPE_COLORS: dict[str, str] = {
    'collection': '#e74c3c',
    'retrofit': '#f39c12',
    'workshop': '#27ae60',
    'retrofitted': '#9b59b6',
    'parking': '#34495e',
    'mainline': '#95a5a6',
    'rescource_parking': '#7f8c8d',
}

# Geometry. The x-axis is in metres along the track.
THROAT_X: float = 0.0
LANE_SPACING: float = 1.0
MIN_TRACK_LEN_M: float = 40.0  # floor so very short tracks stay visible
MAINLINE_DRAWN_M: float = 300.0  # mainline is transit-only; not drawn to scale


@dataclass(frozen=True)
class TrackLayout:  # pylint: disable=too-many-instance-attributes
    """Geometry for a single track lane in the schematic yard."""

    track_id: str
    track_type: str
    lane_y: float
    x_start: float
    x_end: float
    length_m: float
    color: str
    is_workshop: bool = False
    bays: int | None = None
    cluster: str = 'local'
    throat_x: float = 0.0  # x of the connecting (ladder) end of the track
    zone: str = 'single'  # 'single' | 'left' | 'middle' | 'right'


@dataclass(frozen=True)
class YardLayout:  # pylint: disable=too-many-instance-attributes
    """Full schematic layout: track lanes plus connecting throat(s).

    In ``zones`` mode: left zone = local yard (ladder on its right edge),
    middle = Mainline corridor, right zone = remote/arrival storage (ladder on
    its left edge). In ``single`` mode: one vertical throat at ``throat_x``.
    """

    tracks: dict[str, TrackLayout]
    throat_x: float
    x_max: float
    y_min: float
    y_max: float
    mode: str = 'single'  # 'single' | 'zones'
    left_throat_x: float = 0.0
    right_throat_x: float = 0.0
    corridor_y: float = 0.0


def _natural_key(track_id: str) -> tuple[str, int]:
    """Return a sort key that orders ``parking2`` before ``parking10``."""
    digits = ''.join(ch for ch in track_id if ch.isdigit())
    prefix = ''.join(ch for ch in track_id if not ch.isdigit())
    return (prefix, int(digits) if digits else 0)


def _edge_length(topology: dict[str, Any], edges: list[str]) -> float:
    """Sum the lengths of the given topology edges (0.0 if unknown)."""
    edge_map = topology.get('edges', {}) if topology else {}
    total = 0.0
    for edge in edges:
        info = edge_map.get(edge)
        if isinstance(info, dict) and 'length' in info:
            total += float(info['length'])
    return total


def _resolve_track_meta(
    track_id: str,
    tracks_by_id: dict[str, dict[str, Any]],
    topology: dict[str, Any],
    bays_by_id: dict[str, int],
    default_ws_len: float,
) -> tuple[str, float, int | None]:
    """Resolve (track_type, length_m, bays) for a track id, robust to id drift.

    Handles scenarios where the runtime/route id (e.g. workshop ``WS_01``) does
    not match the ``tracks.json`` id (``WS1``): such ids fall back to the
    workshop config for type/bays and a default workshop length.
    """
    if track_id in tracks_by_id:
        track = tracks_by_id[track_id]
        track_type = str(track.get('type', 'parking'))
        length_m = _edge_length(topology, track.get('edges', [track_id]))
        bays = bays_by_id.get(track_id) if track_type == 'workshop' else None
        return track_type, length_m, bays
    if track_id in bays_by_id:  # a workshop id with no matching track entry
        return 'workshop', default_ws_len, bays_by_id[track_id]
    if track_id == rg.MAINLINE:
        return 'mainline', _edge_length(topology, [track_id]), None
    return 'parking', _edge_length(topology, [track_id]) or MIN_TRACK_LEN_M, None


def build_layout(  # pylint: disable=too-many-locals
    tracks_config: list[dict[str, Any]],
    topology: dict[str, Any],
    workshops_config: list[dict[str, Any]] | None = None,
    route_graph: rg.RouteGraph | None = None,
    active_ids: list[str] | None = None,
) -> YardLayout:
    """Build a schematic yard layout from scenario configuration.

    When a remote cluster exists (routes span the Mainline), the layout uses
    three zones: local yard on the left (tracks extend left from a right-edge
    ladder), Mainline corridor in the middle, and remote storage on the right
    (tracks extend right from a left-edge ladder). Otherwise a single stacked
    column with a shared left-edge throat is used.

    ``active_ids`` (when given) selects which tracks to lay out — typically the
    union of ids referenced by routes and the event logs.
    """
    workshops_config = workshops_config or []
    tracks_by_id = {str(t['id']): t for t in tracks_config}
    bays_by_id = {str(s['id']): int(s.get('retrofit_stations', 0)) for s in workshops_config if s.get('id')}
    ws_lengths = [
        _edge_length(topology, t.get('edges', [t['id']])) for t in tracks_config if t.get('type') == 'workshop'
    ]
    default_ws_len = max((length for length in ws_lengths if length > 0), default=260.0)

    ids = active_ids if active_ids else [str(t['id']) for t in tracks_config]
    cluster_of = route_graph.cluster if route_graph else {}

    enriched: list[dict[str, Any]] = []
    for track_id in dict.fromkeys(ids):  # de-duplicate, preserve order
        track_type, length_m, bays = _resolve_track_meta(track_id, tracks_by_id, topology, bays_by_id, default_ws_len)
        enriched.append(
            {
                'id': track_id,
                'type': track_type,
                'length_m': length_m,
                'bays': bays,
                'cluster': cluster_of.get(track_id, 'local'),
            }
        )

    if route_graph is not None and any(t['cluster'] == 'remote' for t in enriched):
        return _layout_zones(enriched)
    return _layout_single(enriched)


def _order_index(track_type: str) -> int:
    """Return the top-to-bottom rank of a track type."""
    return TRACK_TYPE_ORDER.index(track_type) if track_type in TRACK_TYPE_ORDER else len(TRACK_TYPE_ORDER)


def _drawn_len(track_type: str, length_m: float) -> float:
    """Return the drawn x-extent (metres) of a track (mainline is fixed)."""
    return MAINLINE_DRAWN_M if track_type == 'mainline' else max(MIN_TRACK_LEN_M, length_m)


def _make_track(
    track: dict[str, Any], lane_y: float, x_range: tuple[float, float], throat_x: float, zone: str
) -> TrackLayout:
    """Build a TrackLayout from an enriched track dict and geometry."""
    track_type = track['type']
    return TrackLayout(
        track_id=track['id'],
        track_type=track_type,
        lane_y=lane_y,
        x_start=x_range[0],
        x_end=x_range[1],
        length_m=track['length_m'],
        color=TRACK_TYPE_COLORS.get(track_type, '#7f7f7f'),
        is_workshop=track_type == 'workshop',
        bays=track['bays'],
        cluster=track['cluster'],
        throat_x=throat_x,
        zone=zone,
    )


def _layout_single(enriched: list[dict[str, Any]]) -> YardLayout:
    """Lay out all tracks as a single vertically-stacked column."""
    enriched.sort(key=lambda t: (rg.CLUSTER_RANK.get(t['cluster'], 2), _order_index(t['type']), _natural_key(t['id'])))
    n_lanes = len(enriched)
    tracks: dict[str, TrackLayout] = {}
    for index, track in enumerate(enriched):
        drawn = _drawn_len(track['type'], track['length_m'])
        tracks[track['id']] = _make_track(
            track, (n_lanes - 1 - index) * LANE_SPACING, (THROAT_X, THROAT_X + drawn), THROAT_X, 'single'
        )
    y_values = [t.lane_y for t in tracks.values()] or [0.0]
    x_values = [t.x_end for t in tracks.values()] or [MAINLINE_DRAWN_M]
    return YardLayout(
        tracks=tracks,
        throat_x=THROAT_X,
        x_max=max(x_values),
        y_min=min(y_values),
        y_max=max(y_values),
        mode='single',
        left_throat_x=THROAT_X,
    )


def _layout_zones(enriched: list[dict[str, Any]]) -> YardLayout:  # pylint: disable=too-many-locals
    """Lay out tracks in three columns: local yard | Mainline | remote storage.

    The local yard sits on the left (ladder on its right edge, tracks extend
    left), the Mainline is a fixed-width corridor in the middle, and the remote
    storage sits on the right (ladder on its left edge, tracks extend right).
    """
    left = sorted(
        (t for t in enriched if t['type'] != 'mainline' and t['cluster'] in ('local', 'hub')),
        key=lambda t: (_order_index(t['type']), _natural_key(t['id'])),
    )
    right = sorted(
        (t for t in enriched if t['type'] != 'mainline' and t['cluster'] == 'remote'),
        key=lambda t: (_order_index(t['type']), _natural_key(t['id'])),
    )

    left_w = max((_drawn_len(t['type'], t['length_m']) for t in left), default=MIN_TRACK_LEN_M)
    right_w = max((_drawn_len(t['type'], t['length_m']) for t in right), default=MIN_TRACK_LEN_M)
    middle_w = (left_w + right_w) / 3.0
    left_throat = left_w
    right_throat = left_w + middle_w
    total_w = left_w + middle_w + right_w
    n_lanes = max(len(left), len(right), 1)
    corridor_y = -LANE_SPACING

    tracks: dict[str, TrackLayout] = {}

    def lane_for(group: list[dict[str, Any]], index: int) -> float:
        offset = (n_lanes - len(group)) / 2.0
        return (n_lanes - 1 - index - offset) * LANE_SPACING

    for index, track in enumerate(left):
        drawn = _drawn_len(track['type'], track['length_m'])
        tracks[track['id']] = _make_track(
            track, lane_for(left, index), (left_throat - drawn, left_throat), left_throat, 'left'
        )
    for index, track in enumerate(right):
        drawn = _drawn_len(track['type'], track['length_m'])
        tracks[track['id']] = _make_track(
            track, lane_for(right, index), (right_throat, right_throat + drawn), right_throat, 'right'
        )
    for track in (t for t in enriched if t['type'] == 'mainline'):
        tracks[track['id']] = _make_track(
            track, corridor_y, (left_throat, right_throat), (left_throat + right_throat) / 2.0, 'middle'
        )

    y_values = [t.lane_y for t in tracks.values()] or [0.0]
    return YardLayout(
        tracks=tracks,
        throat_x=left_throat,
        x_max=total_w,
        y_min=min(y_values),
        y_max=max(y_values),
        mode='zones',
        left_throat_x=left_throat,
        right_throat_x=right_throat,
        corridor_y=corridor_y,
    )
