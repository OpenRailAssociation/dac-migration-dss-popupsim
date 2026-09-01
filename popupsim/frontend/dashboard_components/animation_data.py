"""Pure data transforms for the simulation animation tab.

This module intentionally avoids any Streamlit or Plotly imports so that the
timeline and motion logic stays fully unit-testable. It turns the raw
``resource_locations`` / ``resource_states`` event logs and the scenario
configuration into per-resource movement timelines and per-frame rectangle
arrays. The yard geometry itself lives in
:mod:`dashboard_components.animation_layout` (re-exported here for convenience).

Parked resources are compacted **per frame** so wagons stay hole-free: the
present occupants of a track are packed flush from the far (right) end as a
LIFO stack (earliest arrival deepest, newest at the throat). Locomotives are
coupled to the wagons they haul and the consist travels as one rigid, spaced
train with the loco on the throat side. Wagons are sized by their real length;
adjacent wagons are told apart by alternating fill shade plus a border.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
import math
from typing import Any

import pandas as pd

from dashboard_components import routes_graph as rg
from dashboard_components.animation_layout import LANE_SPACING
from dashboard_components.animation_layout import MAINLINE_DRAWN_M
from dashboard_components.animation_layout import MIN_TRACK_LEN_M
from dashboard_components.animation_layout import THROAT_X
from dashboard_components.animation_layout import TRACK_TYPE_COLORS
from dashboard_components.animation_layout import TRACK_TYPE_ORDER
from dashboard_components.animation_layout import TrackLayout
from dashboard_components.animation_layout import YardLayout
from dashboard_components.animation_layout import build_layout

__all__ = [
    'LANE_SPACING',
    'MAINLINE_DRAWN_M',
    'MIN_TRACK_LEN_M',
    'THROAT_X',
    'TRACK_TYPE_COLORS',
    'TRACK_TYPE_ORDER',
    'TrackLayout',
    'YardLayout',
    'active_track_ids',
    'build_frames',
    'build_layout',
    'extract_timelines',
    'parse_capacity_timeline',
    'rejected_times',
    'wagon_lengths',
]

WAGON_COLOR_PENDING: str = '#0072B2'  # blue (Okabe-Ito): not yet retrofitted
WAGON_COLOR_DONE: str = '#009E73'  # green (Okabe-Ito): retrofitted
LOCO_COLOR: str = '#2c3e50'  # dark slate, distinct from wagons

# Alternating fill shades so flush (gap-less) neighbours stay individually
# countable. Index 0 is the base colour; index 1 is a lighter sibling.
WAGON_SHADES_PENDING: tuple[str, str] = ('#0072B2', '#56B4E9')  # blue / sky-blue
WAGON_SHADES_DONE: tuple[str, str] = ('#009E73', '#66C2A5')  # green / light green

# Resource dimensions (metres).
DEFAULT_WAGON_LENGTH_M: float = 16.0
LOCO_LENGTH_M: float = 19.0
# Wagons pack flush (no gap): in reality there is no space between coupled
# wagons. Individual wagons are told apart by alternating fill shade + border
# rather than by a gap. Kept as a tunable constant (0 = flush).
UNIFORM_GAP_M: float = 0.0

# Fallback transit duration (simulation minutes) used when an explicit
# departure time is not available in the event log (e.g. locomotives, which
# record arrivals via ``previous_location`` but no move-start row).
DEFAULT_TRANSIT_MIN: float = 12.0

# When inferring which wagons a locomotive hauls, a wagon's transit is matched
# to a loco move on the same from->to whose timing is within this tolerance
# (simulation minutes). The loco and wagon event logs use slightly different
# conventions (the loco logs arrival where the wagon logs departure), so a few
# minutes of slack is needed.
CONSIST_MATCH_TOL_MIN: float = 30.0


# --- Resource timeline model ------------------------------------------------


@dataclass
class Dwell:
    """A stationary span of a resource sitting on a track (fixed centre)."""

    track: str
    t_arrive: float
    t_depart: float  # math.inf for the final (open-ended) dwell
    center_x: float = 0.0


@dataclass
class Move:
    """A transit span of a resource travelling between two tracks."""

    t_depart: float
    t_arrive: float
    route: tuple[str, ...]
    from_track: str
    to_track: str
    anchor_from_x: float = 0.0
    anchor_to_x: float = 0.0


@dataclass
class ResourceTrack:  # pylint: disable=too-many-instance-attributes
    """Full ordered timeline (dwells + moves) for a single resource."""

    resource_id: str
    resource_type: str
    length_m: float = DEFAULT_WAGON_LENGTH_M
    dwells: list[Dwell] = field(default_factory=list)
    moves: list[Move] = field(default_factory=list)
    t_retrofitted: float | None = None
    first_seen: float = 0.0
    last_seen: float = 0.0


@dataclass
class ConsistLeg:
    """One transport leg: a locomotive coupled to a rake of wagons.

    ``car_ids`` / ``car_lengths`` are ordered front-to-back, loco first (it
    always leads at the throat side); the loco's ``loco_move`` carries the
    shared window, route and anchored endpoints. Used to render the consist as
    one rigid train along the route so cars keep their spacing instead of
    converging over the long mainline run.
    """

    loco_id: str
    car_ids: list[str]
    car_lengths: list[float]
    t_depart: float
    t_arrive: float
    loco_move: Move
    car_moves: list[Move] = field(default_factory=list)


# --- Frame model ------------------------------------------------------------


@dataclass(frozen=True)
class FrameStats:
    """Aggregate live statistics for a single animation frame."""

    to_retrofit: int  # wagons present and not yet retrofitted
    present_retrofitted: int  # retrofitted wagons currently in the system
    cumulative_retrofitted: int  # wagons retrofitted up to this time
    cumulative_rejected: int  # wagons rejected up to this time
    utilization: dict[str, float]  # track id -> occupied length / real length


@dataclass(frozen=True)
class FrameData:  # pylint: disable=too-many-instance-attributes
    """Rectangle centres + lengths for a single animation frame."""

    t: float
    datetime_label: str
    wagon_x: list[float]
    wagon_y: list[float]
    wagon_len: list[float]
    wagon_color: list[str]
    wagon_ids: list[str]
    wagon_shade: list[int]
    loco_x: list[float]
    loco_y: list[float]
    loco_len: list[float]
    loco_ids: list[str]
    stats: FrameStats


# === Movement-segment extraction ============================================


def active_track_ids(resource_locations: pd.DataFrame | None, route_graph: rg.RouteGraph | None) -> list[str]:
    """Return the union of track ids referenced by routes and the event log.

    This is the set of lanes worth drawing — it includes runtime ids (e.g.
    workshop ``WS_01``) that may not appear verbatim in ``tracks.json``.
    """
    ids: set[str] = set()
    if route_graph is not None:
        ids |= set(route_graph.track_ids)
    if resource_locations is not None and not resource_locations.empty and 'location' in resource_locations.columns:
        ids |= {str(v) for v in resource_locations['location'].dropna().unique() if str(v).strip()}
    return sorted(ids)


def _parse_route(value: Any) -> tuple[str, ...]:
    """Parse a pipe-delimited ``route_path`` value into a tuple of track ids."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ()
    text = str(value).strip()
    if not text:
        return ()
    return tuple(part for part in text.split('|') if part)


def _is_blank(value: Any) -> bool:
    """Return True for missing / empty cell values."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() == ''


def _retrofit_times(states: pd.DataFrame | None) -> dict[str, float]:
    """Map each wagon id to the timestamp it first reaches ``retrofitted``."""
    if states is None or states.empty or 'state' not in states.columns:
        return {}
    done = states[states['state'] == 'retrofitted']
    if done.empty:
        return {}
    grouped = done.groupby('resource_id')['timestamp'].min()
    return {str(rid): float(ts) for rid, ts in grouped.items()}


def wagon_lengths(train_schedule: pd.DataFrame | None) -> dict[str, float]:
    """Map each wagon id to its real length (metres) from the train schedule."""
    if train_schedule is None or train_schedule.empty:
        return {}
    if 'wagon_id' not in train_schedule.columns or 'length' not in train_schedule.columns:
        return {}
    lengths: dict[str, float] = {}
    for _, row in train_schedule.iterrows():
        try:
            lengths[str(row['wagon_id'])] = float(row['length'])
        except (ValueError, TypeError):
            continue
    return lengths


def rejected_times(rejected_wagons: pd.DataFrame | None) -> list[float]:
    """Return sorted rejection timestamps (minutes) for TRACK_FULL rejections only."""
    if rejected_wagons is None or rejected_wagons.empty or 'timestamp' not in rejected_wagons.columns:
        return []
    df = rejected_wagons
    if 'rejection_type' in df.columns:
        df = df[df['rejection_type'] == 'TRACK_FULL']
    times: list[float] = []
    for value in df['timestamp']:
        try:
            times.append(float(value))
        except (ValueError, TypeError):
            continue
    return sorted(times)


# --- Capacity timeline (backend reservation events) -------------------------

# Per-track: sorted list of (timestamp, utilization_fraction) pairs.
CapacityTimeline = dict[str, list[tuple[float, float]]]


def parse_capacity_timeline(track_capacity: pd.DataFrame | None) -> CapacityTimeline:
    """Parse ``track_capacity.csv`` into a per-track step-function of utilization.

    Each track gets a sorted list of ``(timestamp, used_after / capacity)``
    entries.  Lookup at a given time uses binary search for the last event ≤ t.
    """
    if track_capacity is None or track_capacity.empty:
        return {}
    required = {'timestamp', 'track_id', 'used_after', 'capacity'}
    if not required.issubset(track_capacity.columns):
        return {}
    timeline: CapacityTimeline = {}
    for track_id, grp in track_capacity.groupby('track_id', sort=False):
        entries: list[tuple[float, float]] = []
        for _, row in grp.sort_values('timestamp').iterrows():
            cap = float(row['capacity'])
            if cap <= 0:
                continue
            entries.append((float(row['timestamp']), float(row['used_after']) / cap))
        if entries:
            timeline[str(track_id)] = entries
    return timeline


def _capacity_util_at(timeline: CapacityTimeline, track_id: str, t: float) -> float | None:
    """Look up the backend utilization for *track_id* at time *t* (or None if unknown)."""
    entries = timeline.get(track_id)
    if not entries:
        return None
    idx = bisect.bisect_right(entries, (t, math.inf)) - 1
    if idx < 0:
        return 0.0
    return entries[idx][1]


def _build_timeline(resource_id: str, resource_type: str, rows: pd.DataFrame) -> ResourceTrack | None:
    """Build a single resource timeline from its ordered location rows."""
    rows = rows.sort_values('timestamp')
    track = ResourceTrack(resource_id=resource_id, resource_type=resource_type)

    cur_track: str | None = None
    cur_arrive = 0.0
    pending_route: tuple[str, ...] = ()
    pending_depart: float | None = None

    for _, row in rows.iterrows():
        ts = float(row['timestamp'])
        location = None if _is_blank(row.get('location')) else str(row['location'])
        route = _parse_route(row.get('route_path'))

        if cur_track is None:
            if location is None:
                continue
            cur_track, cur_arrive = location, ts
            track.first_seen = ts
            continue

        if route:  # move-start marker (wagons)
            pending_route, pending_depart = route, ts

        if location is not None and location != cur_track:
            depart = pending_depart if pending_depart is not None else max(cur_arrive, ts - DEFAULT_TRANSIT_MIN)
            depart = min(max(depart, cur_arrive), ts)
            track.dwells.append(Dwell(track=cur_track, t_arrive=cur_arrive, t_depart=depart))
            route_used = pending_route if pending_route else (cur_track, location)
            track.moves.append(
                Move(t_depart=depart, t_arrive=ts, route=route_used, from_track=cur_track, to_track=location)
            )
            cur_track, cur_arrive = location, ts
            pending_route, pending_depart = (), None

    if cur_track is not None:
        track.dwells.append(Dwell(track=cur_track, t_arrive=cur_arrive, t_depart=math.inf))
        track.last_seen = float(rows['timestamp'].max())
        return track
    return None


def extract_timelines(
    resource_locations: pd.DataFrame | None,
    resource_states: pd.DataFrame | None,
    lengths: dict[str, float] | None = None,
) -> dict[str, ResourceTrack]:
    """Extract per-resource dwell/move timelines from the event logs.

    Wagons use the populated ``route_path`` rows to determine the departure
    time and the path taken. Locomotives (which only record arrivals via
    ``previous_location``) fall back to :data:`DEFAULT_TRANSIT_MIN`. ``lengths``
    maps wagon ids to real lengths (metres); missing wagons fall back to
    :data:`DEFAULT_WAGON_LENGTH_M` and locomotives to :data:`LOCO_LENGTH_M`.
    """
    if resource_locations is None or resource_locations.empty:
        return {}

    lengths = lengths or {}
    retrofit = _retrofit_times(resource_states)
    timelines: dict[str, ResourceTrack] = {}
    for resource_id, rows in resource_locations.groupby('resource_id'):
        rid = str(resource_id)
        rtype = str(rows['resource_type'].iloc[0]) if 'resource_type' in rows.columns else 'wagon'
        timeline = _build_timeline(rid, rtype, rows)
        if timeline is None:
            continue
        timeline.t_retrofitted = retrofit.get(rid)
        timeline.length_m = LOCO_LENGTH_M if rtype == 'locomotive' else lengths.get(rid, DEFAULT_WAGON_LENGTH_M)
        timelines[rid] = timeline
    return timelines


# === Stable position allocation =============================================


def _stack_centers(tl: TrackLayout, present: list[tuple[float, bool, str, float]]) -> dict[str, float]:
    """Pack present resources flush from the far end (away from the throat) as a LIFO stack.

    The earliest arrival sits deepest (against the far end); later arrivals — and
    locomotives on an arrival tie — sit nearer the throat, where a loco couples.
    There are never holes: the present set is re-packed every frame, so a
    departure makes the rest slide flush toward the far end.
    """
    order = sorted(present, key=lambda p: (p[0], p[1]))
    centers: dict[str, float] = {}
    # Determine packing direction: fill away from the throat toward the far end.
    if abs(tl.throat_x - tl.x_end) < 1e-9:
        # Throat is on the right edge (left-zone) → far end is x_start, fill rightward
        x = tl.x_start
        for _t_arrive, _is_loco, rid, length in order:
            centers[rid] = x + length / 2.0
            x += length + UNIFORM_GAP_M
    else:
        # Throat is on the left edge (right-zone / single) → far end is x_end, fill leftward
        x = tl.x_end
        for _t_arrive, _is_loco, rid, length in order:
            centers[rid] = x - length / 2.0
            x -= length + UNIFORM_GAP_M
    return centers


def _workshop_centers(tl: TrackLayout, present: list[tuple[float, bool, str, float]]) -> dict[str, float]:
    """Place present workshop occupants in evenly-spaced bay slots inside the box."""
    order = sorted(present, key=lambda p: (p[0], p[1]))
    n_slots = max(1, tl.bays or 1, len(order))
    width = tl.x_end - tl.x_start
    return {rid: tl.x_start + width * (slot + 0.5) / n_slots for slot, (_ta, _lc, rid, _ln) in enumerate(order)}


def _centers_for(tl: TrackLayout | None, present: list[tuple[float, bool, str, float]]) -> dict[str, float]:
    """Dispatch flush-stack vs workshop-slot packing for a track's occupants."""
    if tl is None or not present:
        return {}
    if tl.is_workshop:
        return _workshop_centers(tl, present)
    return _stack_centers(tl, present)


def _present_on(timelines: dict[str, ResourceTrack], track_id: str, t: float) -> list[tuple[float, bool, str, float]]:
    """Return (t_arrive, is_loco, id, length) for resources parked on ``track_id`` at ``t``."""
    present: list[tuple[float, bool, str, float]] = []
    for rt in timelines.values():
        if t < rt.first_seen:
            continue
        for dwell in rt.dwells:
            if dwell.track == track_id and dwell.t_arrive <= t <= dwell.t_depart:
                present.append((dwell.t_arrive, rt.resource_type == 'locomotive', rt.resource_id, rt.length_m))
                break
    return present


def _packed_centers(
    layout: YardLayout, timelines: dict[str, ResourceTrack], track_id: str, t: float
) -> dict[str, float]:
    """Return {resource_id: center_x} for the resources parked on ``track_id`` at ``t``."""
    return _centers_for(layout.tracks.get(track_id), _present_on(timelines, track_id, t))


def _all_packed_centers(
    layout: YardLayout, timelines: dict[str, ResourceTrack], t: float
) -> dict[str, dict[str, float]]:
    """Compute packed centres for every occupied track at ``t`` in a single scan."""
    present_by_track: dict[str, list[tuple[float, bool, str, float]]] = defaultdict(list)
    for rt in timelines.values():
        if t < rt.first_seen:
            continue
        for dwell in rt.dwells:
            if dwell.t_arrive <= t <= dwell.t_depart:
                present_by_track[dwell.track].append(
                    (dwell.t_arrive, rt.resource_type == 'locomotive', rt.resource_id, rt.length_m)
                )
                break
    return {track: _centers_for(layout.tracks.get(track), items) for track, items in present_by_track.items()}


def _mid_x(layout: YardLayout, track_id: str) -> float:
    """Return a track's mid-x fallback (used when a resource is not found parked)."""
    tl = layout.tracks.get(track_id)
    return (tl.x_start + tl.x_end) / 2.0 if tl is not None else 0.0


def _anchor_moves(layout: YardLayout, timelines: dict[str, ResourceTrack]) -> None:
    """Anchor each move to the resource's compacted slot at its endpoints (in place)."""
    for rt in timelines.values():
        for move in rt.moves:
            from_centers = _packed_centers(layout, timelines, move.from_track, move.t_depart)
            to_centers = _packed_centers(layout, timelines, move.to_track, move.t_arrive)
            move.anchor_from_x = from_centers.get(rt.resource_id, _mid_x(layout, move.from_track))
            move.anchor_to_x = to_centers.get(rt.resource_id, _mid_x(layout, move.to_track))


def _best_loco_move(wm: Move, candidates: list[tuple[str, int, Move]]) -> tuple[str, int] | None:
    """Return the (loco_id, move_index) best matching a wagon move, or None."""
    best_key: tuple[str, int] | None = None
    best_dist = CONSIST_MATCH_TOL_MIN
    for loco_id, index, lm in candidates:
        if lm.from_track != wm.from_track or lm.to_track != wm.to_track:
            continue
        dist = min(abs(lm.t_arrive - wm.t_depart), abs(lm.t_depart - wm.t_depart), abs(lm.t_arrive - wm.t_arrive))
        if dist <= best_dist:
            best_key, best_dist = (loco_id, index), dist
    return best_key


def infer_consists(timelines: dict[str, ResourceTrack]) -> dict[str, list[ConsistLeg]]:  # pylint: disable=too-many-locals
    """Couple wagons to the locomotive that hauls them and synchronise motion (in place).

    No data source links a wagon to its loco, so each loco move is matched to the
    wagons departing the same ``from->to`` at a close time (see
    :data:`CONSIST_MATCH_TOL_MIN`). For a matched leg the loco move (and its
    bracketing dwells) is snapped to the rake's window and route — the wagon data
    is trusted — so the loco and its wagons travel together. Returns the consist
    legs keyed by every member resource id; unmatched (empty) loco trips produce
    no leg.
    """
    locos = [rt for rt in timelines.values() if rt.resource_type == 'locomotive']
    wagons = [rt for rt in timelines.values() if rt.resource_type != 'locomotive']
    by_key: dict[tuple[str, int], tuple[ResourceTrack, Move]] = {}
    candidates: list[tuple[str, int, Move]] = []
    for loco in locos:
        for index, lm in enumerate(loco.moves):
            by_key[(loco.resource_id, index)] = (loco, lm)
            candidates.append((loco.resource_id, index, lm))

    rakes: dict[tuple[str, int], list[tuple[ResourceTrack, int, Move]]] = defaultdict(list)
    for wagon in wagons:
        for widx, wm in enumerate(wagon.moves):
            key = _best_loco_move(wm, candidates)
            if key is not None:
                rakes[key].append((wagon, widx, wm))

    legs_by_resource: dict[str, list[ConsistLeg]] = defaultdict(list)
    for key, members in rakes.items():
        leg = _build_leg(by_key[key], key[1], members)
        legs_by_resource[leg.loco_id].append(leg)
        for car_id in leg.car_ids[1:]:
            legs_by_resource[car_id].append(leg)
    return dict(legs_by_resource)


def _build_leg(
    loco_move: tuple[ResourceTrack, Move], index: int, members: list[tuple[ResourceTrack, int, Move]]
) -> ConsistLeg:
    """Snap a loco move to its rake's window/route and return the consist leg."""
    loco, lm = loco_move
    dep = min(wm.t_depart for _w, _i, wm in members)
    arr = max(wm.t_arrive for _w, _i, wm in members)
    lm.t_depart, lm.t_arrive = dep, arr
    lm.route = members[0][2].route or lm.route
    if index < len(loco.dwells):
        loco.dwells[index].t_depart = dep
    if index + 1 < len(loco.dwells):
        loco.dwells[index + 1].t_arrive = arr
    # Order wagons newest-first: the latest source arrival sits closest to the
    # loco (the throat side), matching the flush-stack packing.
    ordered = sorted(members, key=lambda m: m[0].dwells[m[1]].t_arrive, reverse=True)
    car_ids = [loco.resource_id, *[w.resource_id for w, _i, _wm in ordered]]
    car_lengths = [loco.length_m, *[w.length_m for w, _i, _wm in ordered]]
    car_moves = [lm, *[wm for _w, _i, wm in ordered]]
    return ConsistLeg(loco.resource_id, car_ids, car_lengths, dep, arr, lm, car_moves)


def assign_positions(layout: YardLayout, timelines: dict[str, ResourceTrack]) -> dict[str, list[ConsistLeg]]:
    """Infer loco/wagon consists, anchor every move, and return the consist legs.

    Parked positions are *not* precomputed: they are compacted per frame (see
    :func:`_all_packed_centers`) so wagons stay hole-free and slide as neighbours
    leave. Only move endpoints are anchored here, to the compacted slot the
    resource occupies at departure / arrival.
    """
    legs = infer_consists(timelines)
    _anchor_moves(layout, timelines)
    return legs


# === Position resolver ======================================================


def _move_waypoints(layout: YardLayout, move: Move) -> list[tuple[float, float]]:
    """Build the route-aware waypoint path for a transit segment.

    In single-column mode the path routes out to the shared vertical throat at
    each route lane. In three-zone mode it routes to the source track's ladder,
    and — for cross-zone moves — along the Mainline corridor to the destination
    zone's ladder, so the resource visibly passes through the Mainline.
    """
    a = layout.tracks.get(move.from_track)
    b = layout.tracks.get(move.to_track)
    lane_from = a.lane_y if a is not None else 0.0
    lane_to = b.lane_y if b is not None else 0.0
    throat_a = a.throat_x if a is not None else layout.throat_x
    throat_b = b.throat_x if b is not None else layout.throat_x
    start = (move.anchor_from_x, lane_from)
    end = (move.anchor_to_x, lane_to)

    if layout.mode != 'zones' or a is None or b is None:
        points: list[tuple[float, float]] = [start]
        for track_id in move.route:
            tl = layout.tracks.get(track_id)
            if tl is not None:
                points.append((layout.throat_x, tl.lane_y))
        points.append(end)
        return points

    points = [start, (throat_a, lane_from)]
    if a.zone == b.zone:
        points.append((throat_a, lane_to))
    else:  # cross-zone: traverse the Mainline corridor between the two ladders
        points.extend(
            [
                (throat_a, layout.corridor_y),
                (throat_b, layout.corridor_y),
                (throat_b, lane_to),
            ]
        )
    points.append(end)
    return points


def _interp_path(points: list[tuple[float, float]], frac: float) -> tuple[float, float]:
    """Linearly interpolate a position at ``frac`` (0..1) along a polyline."""
    if frac <= 0.0 or len(points) == 1:
        return points[0]
    if frac >= 1.0:
        return points[-1]
    seg_lengths = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
    total = sum(seg_lengths)
    if total == 0.0:
        return points[0]
    target = frac * total
    walked = 0.0
    for i, seg_len in enumerate(seg_lengths):
        if walked + seg_len >= target:
            local = 0.0 if seg_len == 0 else (target - walked) / seg_len
            (x0, y0), (x1, y1) = points[i], points[i + 1]
            return (x0 + local * (x1 - x0), y0 + local * (y1 - y0))
        walked += seg_len
    return points[-1]


def _path_length(points: list[tuple[float, float]]) -> float:
    """Return the total arc length of a polyline."""
    return sum(math.dist(points[i], points[i + 1]) for i in range(len(points) - 1))


def _car_offset(leg: ConsistLeg, idx: int) -> float:
    """Centre-to-centre arc distance from the loco (index 0) to car ``idx``."""
    if idx <= 0:
        return 0.0
    off = leg.car_lengths[0] / 2.0 + leg.car_lengths[idx] / 2.0
    for j in range(1, idx):
        off += leg.car_lengths[j]
    return off


def _covering_leg(legs: list[ConsistLeg] | None, t: float) -> ConsistLeg | None:
    """Return the consist leg whose window contains ``t`` (or None)."""
    if not legs:
        return None
    for leg in legs:
        if leg.t_depart <= t <= leg.t_arrive:
            return leg
    return None


def _consist_position(leg: ConsistLeg, idx: int, layout: YardLayout, t: float) -> tuple[float, float]:
    """Position car ``idx`` of a consist as part of one rigid, spaced train.

    Every car follows its **own** route (its own compacted source/dest slots),
    sharing a single progress lagged by the car's offset behind the loco —
    expressed as a fraction of the loco's path so cars on slightly different-
    length paths stay evenly spaced. The loco leads out and settles at its
    throat-side slot first; each wagon tucks into its own (deeper) slot, so the
    train keeps its spacing over the long mainline run yet lands flush at both
    ends with no holes and no overlap.
    """
    move = leg.car_moves[idx] if idx < len(leg.car_moves) else leg.loco_move
    path = _move_waypoints(layout, move)
    ref_len = _path_length(_move_waypoints(layout, leg.loco_move)) or 1.0
    off_frac = _car_offset(leg, idx) / ref_len
    tail_frac = _car_offset(leg, len(leg.car_ids) - 1) / ref_len
    denom = leg.t_arrive - leg.t_depart
    raw = 0.0 if denom <= 0 else min(1.0, max(0.0, (t - leg.t_depart) / denom))
    progress = raw * (1.0 + tail_frac)
    return _interp_path(path, min(1.0, max(0.0, progress - off_frac)))


def _resolve_position(
    rt: ResourceTrack,
    layout: YardLayout,
    centers: dict[str, dict[str, float]],
    legs: dict[str, list[ConsistLeg]],
    t: float,
) -> tuple[float, float] | None:
    """Resolve a resource's (x, y) using per-frame packed ``centers`` and consist ``legs``."""
    if t < rt.first_seen:
        return None
    for dwell in rt.dwells:
        if dwell.t_arrive <= t <= dwell.t_depart:
            tl = layout.tracks.get(dwell.track)
            if tl is None:
                return None
            cx = centers.get(dwell.track, {}).get(rt.resource_id)
            return (cx if cx is not None else _mid_x(layout, dwell.track), tl.lane_y)
    for move in rt.moves:
        if move.t_depart <= t <= move.t_arrive:
            leg = _covering_leg(legs.get(rt.resource_id), t)
            if leg is not None:
                return _consist_position(leg, leg.car_ids.index(rt.resource_id), layout, t)
            denom = move.t_arrive - move.t_depart
            frac = 0.0 if denom <= 0 else (t - move.t_depart) / denom
            return _interp_path(_move_waypoints(layout, move), frac)
    return None


def position_at(
    rt: ResourceTrack,
    layout: YardLayout,
    timelines: dict[str, ResourceTrack],
    t: float,
    legs: dict[str, list[ConsistLeg]] | None = None,
) -> tuple[float, float] | None:
    """Resolve a resource's (x, y) centre at simulation time ``t``.

    Returns ``None`` before the resource first appears. While parked it sits at
    its compacted (hole-free, flush-right) slot among co-present resources; while
    moving it follows its route — as part of a rigid consist when ``legs`` says
    so. Requires :func:`assign_positions` to have been run on ``timelines`` (pass
    its returned ``legs`` for coupled movement).
    """
    return _resolve_position(rt, layout, _all_packed_centers(layout, timelines, t), legs or {}, t)


# === Frame builder ==========================================================


def sim_time_bounds(timelines: dict[str, ResourceTrack]) -> tuple[float, float]:
    """Return the (start, end) simulation time spanning all resources."""
    if not timelines:
        return (0.0, 0.0)
    start = min(rt.first_seen for rt in timelines.values())
    end = max(rt.last_seen for rt in timelines.values())
    if end <= start:
        end = start + 1.0
    return (start, end)


def _wagon_color(rt: ResourceTrack, t: float) -> str:
    """Return the wagon colour at time ``t`` (green once retrofitted)."""
    if rt.t_retrofitted is not None and t >= rt.t_retrofitted:
        return WAGON_COLOR_DONE
    return WAGON_COLOR_PENDING


def _empty_acc() -> dict[str, list[Any]]:
    """Return empty per-category arrays for a frame under construction."""
    return {
        'wagon_x': [],
        'wagon_y': [],
        'wagon_len': [],
        'wagon_color': [],
        'wagon_ids': [],
        'loco_x': [],
        'loco_y': [],
        'loco_len': [],
        'loco_ids': [],
    }


def _shade_indices(xs: list[float], ys: list[float]) -> list[int]:
    """Assign an alternating 0/1 shade per wagon, by position along each lane.

    Wagons on the same lane (same ``y``) are ranked left-to-right; the shade is
    the rank parity, so flush neighbours render in alternating brightness and
    can be told apart without a gap.
    """
    shades = [0] * len(xs)
    order = sorted(range(len(xs)), key=lambda i: (ys[i], xs[i]))
    prev_y: float | None = None
    rank = 0
    for i in order:
        if ys[i] != prev_y:
            prev_y, rank = ys[i], 0
        shades[i] = rank % 2
        rank += 1
    return shades


def _dwell_track_at(rt: ResourceTrack, t: float) -> str | None:
    """Return the track a resource is parked on at ``t`` (None while in transit)."""
    if t < rt.first_seen:
        return None
    for dwell in rt.dwells:
        if dwell.t_arrive <= t <= dwell.t_depart:
            return dwell.track
    return None


def _frame_stats(  # pylint: disable=too-many-locals
    layout: YardLayout,
    timelines: dict[str, ResourceTrack],
    t: float,
    rejected_at: list[float],
    capacity_timeline: CapacityTimeline | None = None,
) -> FrameStats:
    """Compute the aggregate live statistics for simulation time ``t``."""
    to_retrofit = present_done = cumulative_done = 0
    occupied: dict[str, float] = defaultdict(float)
    for rt in timelines.values():
        if rt.resource_type == 'locomotive':
            continue
        done = rt.t_retrofitted is not None and t >= rt.t_retrofitted
        cumulative_done += 1 if done else 0
        present = t >= rt.first_seen
        if present:
            present_done += 1 if done else 0
            to_retrofit += 0 if done else 1
            track = _dwell_track_at(rt, t)
            if track is not None:
                occupied[track] += rt.length_m

    utilization: dict[str, float] = {}
    for track_id, tl in layout.tracks.items():
        if tl.track_type == 'mainline' or tl.length_m <= 0:
            continue
        if capacity_timeline:
            cap_val = _capacity_util_at(capacity_timeline, track_id, t)
            if cap_val is not None:
                utilization[track_id] = cap_val
                continue
        utilization[track_id] = occupied.get(track_id, 0.0) / tl.length_m

    cumulative_rejected = sum(1 for rt_t in rejected_at if rt_t <= t)
    return FrameStats(
        to_retrofit=to_retrofit,
        present_retrofitted=present_done,
        cumulative_retrofitted=cumulative_done,
        cumulative_rejected=cumulative_rejected,
        utilization=utilization,
    )


def _collect_frame_arrays(
    layout: YardLayout, timelines: dict[str, ResourceTrack], legs: dict[str, list[ConsistLeg]], t: float
) -> dict[str, list[Any]]:
    """Accumulate per-resource rectangle arrays for a single frame."""
    acc = _empty_acc()
    centers = _all_packed_centers(layout, timelines, t)
    for rt in timelines.values():
        pos = _resolve_position(rt, layout, centers, legs, t)
        if pos is None:
            continue
        if rt.resource_type == 'locomotive':
            acc['loco_x'].append(pos[0])
            acc['loco_y'].append(pos[1])
            acc['loco_len'].append(rt.length_m)
            acc['loco_ids'].append(rt.resource_id)
        else:
            acc['wagon_x'].append(pos[0])
            acc['wagon_y'].append(pos[1])
            acc['wagon_len'].append(rt.length_m)
            acc['wagon_color'].append(_wagon_color(rt, t))
            acc['wagon_ids'].append(rt.resource_id)
    return acc


@dataclass(frozen=True)
class _FrameInputs:
    """Shared inputs for building every frame of one animation."""

    layout: YardLayout
    timelines: dict[str, ResourceTrack]
    legs: dict[str, list[ConsistLeg]]
    rejected_at: list[float]
    t_start: float
    capacity_timeline: CapacityTimeline


def _build_one_frame(inputs: _FrameInputs, t: float) -> FrameData:
    """Assemble a single :class:`FrameData` (rectangles + shades + stats) at ``t``."""
    acc = _collect_frame_arrays(inputs.layout, inputs.timelines, inputs.legs, t)
    return FrameData(
        t=t,
        datetime_label=_format_time(inputs.t_start, t),
        wagon_x=acc['wagon_x'],
        wagon_y=acc['wagon_y'],
        wagon_len=acc['wagon_len'],
        wagon_color=acc['wagon_color'],
        wagon_ids=acc['wagon_ids'],
        wagon_shade=_shade_indices(acc['wagon_x'], acc['wagon_y']),
        loco_x=acc['loco_x'],
        loco_y=acc['loco_y'],
        loco_len=acc['loco_len'],
        loco_ids=acc['loco_ids'],
        stats=_frame_stats(inputs.layout, inputs.timelines, t, inputs.rejected_at, inputs.capacity_timeline),
    )


def build_frames(  # noqa: PLR0913  # pylint: disable=too-many-arguments,too-many-positional-arguments
    layout: YardLayout,
    timelines: dict[str, ResourceTrack],
    num_frames: int,
    bounds: tuple[float, float] | None = None,
    rejected_at: list[float] | None = None,
    capacity_timeline: CapacityTimeline | None = None,
) -> list[FrameData]:
    """Build the per-frame rectangle arrays over a uniform simulation-time grid.

    ``num_frames`` (the user-selected resolution) sets the grid density. Each
    frame carries wagon / locomotive rectangle centres + lengths + colours,
    per-wagon shade indices, and aggregate live :class:`FrameStats`.
    ``rejected_at`` lists rejection timestamps (minutes) for the cumulative
    rejected-wagon counter.
    """
    if not timelines or num_frames < 1:
        return []
    legs = assign_positions(layout, timelines)
    t_start, t_end = bounds if bounds is not None else sim_time_bounds(timelines)
    span = t_end - t_start
    inputs = _FrameInputs(layout, timelines, legs, rejected_at or [], t_start, capacity_timeline or {})

    frames: list[FrameData] = []
    for index in range(num_frames):
        frac = 0.0 if num_frames == 1 else index / (num_frames - 1)
        frames.append(_build_one_frame(inputs, t_start + frac * span))
    return frames


def _format_time(t_start: float, t: float) -> str:
    """Format a simulation timestamp (minutes) as an elapsed D/H:M label."""
    elapsed = t - t_start
    days = int(elapsed // (24 * 60))
    hours = int((elapsed % (24 * 60)) // 60)
    minutes = int(elapsed % 60)
    if days > 0:
        return f'Day {days + 1} {hours:02d}:{minutes:02d}'
    return f'{hours:02d}:{minutes:02d}'
