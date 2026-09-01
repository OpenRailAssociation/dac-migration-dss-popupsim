"""Unit tests for the animation data transforms (animation_data.py).

These tests use small synthetic event logs mirroring the real
``resource_locations`` / ``resource_states`` shape. They cover the left-throat
two-zone layout (with a bottom mainline corridor), the per-frame stack (LIFO)
compaction, and loco/wagon consist coupling.
"""

import itertools
import math

from dashboard_components import animation_data as ad
from dashboard_components import routes_graph as rg
import pandas as pd
import pytest

# --- Fixtures ---------------------------------------------------------------


@pytest.fixture
def tracks_config() -> list[dict]:
    """Return a minimal tracks config covering several track types."""
    return [
        {'id': 'collection1', 'edges': ['collection1'], 'type': 'collection'},
        {'id': 'retrofit1', 'edges': ['retrofit1'], 'type': 'retrofit'},
        {'id': 'WS_01', 'edges': ['WS_01'], 'type': 'workshop'},
        {'id': 'retrofitted1', 'edges': ['retrofitted1'], 'type': 'retrofitted'},
        {'id': 'Mainline', 'edges': ['Mainline'], 'type': 'mainline'},
        {'id': 'track_19', 'edges': ['track_19'], 'type': 'rescource_parking'},
    ]


@pytest.fixture
def topology() -> dict:
    """Return a matching topology with edge lengths."""
    return {
        'nodes': [1, 2],
        'edges': {
            'collection1': {'nodes': [1, 2], 'length': 500.0},
            'retrofit1': {'nodes': [1, 2], 'length': 426.0},
            'WS_01': {'nodes': [1, 2], 'length': 260.0},
            'retrofitted1': {'nodes': [1, 2], 'length': 704.0},
            'Mainline': {'nodes': [1, 2], 'length': 8000.0},
            'track_19': {'nodes': [1, 2], 'length': 169.0},
        },
    }


@pytest.fixture
def workshops_config() -> list[dict]:
    """Return a workshop config providing bay counts."""
    return [{'id': 'WS_01', 'name': 'First workshop', 'retrofit_stations': 2, 'track': 'WS1'}]


@pytest.fixture
def layout(tracks_config, topology, workshops_config) -> ad.YardLayout:
    """Return a built yard layout for the synthetic config (no routes -> single zone)."""
    return ad.build_layout(tracks_config, topology, workshops_config)


@pytest.fixture
def train_schedule() -> pd.DataFrame:
    """Return a train schedule with per-wagon real lengths."""
    return pd.DataFrame(
        [
            {'train_id': 'T1', 'wagon_id': 'W0001', 'length': 15.9},
            {'train_id': 'T1', 'wagon_id': 'W0002', 'length': 23.5},
        ]
    )


@pytest.fixture
def w0001_locations() -> pd.DataFrame:
    """Return a location log mirroring wagon W0001's real trace."""
    return pd.DataFrame(
        [
            {
                'timestamp': 360.0,
                'resource_id': 'W0001',
                'resource_type': 'wagon',
                'location': 'collection1',
                'route_path': None,
            },
            {
                'timestamp': 433.0,
                'resource_id': 'W0001',
                'resource_type': 'wagon',
                'location': 'collection1',
                'route_path': 'collection1|Mainline|retrofit1',
            },
            {
                'timestamp': 493.0,
                'resource_id': 'W0001',
                'resource_type': 'wagon',
                'location': 'retrofit1',
                'route_path': None,
            },
            {
                'timestamp': 503.0,
                'resource_id': 'W0001',
                'resource_type': 'wagon',
                'location': 'retrofit1',
                'route_path': 'retrofit1|WS_01',
            },
            {
                'timestamp': 508.0,
                'resource_id': 'W0001',
                'resource_type': 'wagon',
                'location': 'WS_01',
                'route_path': None,
            },
        ]
    )


@pytest.fixture
def w0001_states() -> pd.DataFrame:
    """Return a state log marking the retrofit-completion timestamp."""
    return pd.DataFrame(
        [
            {'timestamp': 360.0, 'resource_id': 'W0001', 'resource_type': 'wagon', 'state': 'arrived'},
            {'timestamp': 433.0, 'resource_id': 'W0001', 'resource_type': 'wagon', 'state': 'moving'},
            {'timestamp': 493.0, 'resource_id': 'W0001', 'resource_type': 'wagon', 'state': 'queued'},
            {'timestamp': 508.0, 'resource_id': 'W0001', 'resource_type': 'wagon', 'state': 'in_workshop'},
            {'timestamp': 574.0, 'resource_id': 'W0001', 'resource_type': 'wagon', 'state': 'retrofitted'},
        ]
    )


@pytest.fixture
def loco_locations() -> pd.DataFrame:
    """Return a locomotive location log (uses previous_location, no route_path)."""
    return pd.DataFrame(
        [
            {
                'timestamp': 360.0,
                'resource_id': 'LOCO_01',
                'resource_type': 'locomotive',
                'location': 'track_19',
                'previous_location': None,
                'route_path': None,
            },
            {
                'timestamp': 420.0,
                'resource_id': 'LOCO_01',
                'resource_type': 'locomotive',
                'location': 'collection1',
                'previous_location': 'track_19',
                'route_path': None,
            },
            {
                'timestamp': 500.0,
                'resource_id': 'LOCO_01',
                'resource_type': 'locomotive',
                'location': 'retrofit1',
                'previous_location': 'collection1',
                'route_path': None,
            },
        ]
    )


def _track_layout(track_type: str, length: float, bays: int | None = None) -> ad.TrackLayout:
    """Build a single left-throat TrackLayout (throat at x=0, extends right)."""
    return ad.TrackLayout(
        track_id='T',
        track_type=track_type,
        lane_y=0.0,
        x_start=0.0,
        x_end=length,
        length_m=length,
        color='#000000',
        is_workshop=track_type == 'workshop',
        bays=bays,
        throat_x=0.0,
        zone='local',
    )


def _one_track_layout(track_type: str, length: float, bays: int | None = None) -> ad.YardLayout:
    """Build a single-track yard layout for compaction tests."""
    return ad.YardLayout(
        tracks={'T': _track_layout(track_type, length, bays)},
        throat_x=0.0,
        x_max=length,
        y_min=0.0,
        y_max=0.0,
        mode='single',
        left_throat_x=0.0,
    )


def _wagons(track: str, specs: list[tuple[str, float, float, float]]) -> dict[str, ad.ResourceTrack]:
    """Build wagons on ``track`` from (id, length, t_arrive, t_depart) specs."""
    timelines: dict[str, ad.ResourceTrack] = {}
    for rid, length, t_arrive, t_depart in specs:
        rt = ad.ResourceTrack(rid, 'wagon', length_m=length, dwells=[ad.Dwell(track, t_arrive, t_depart)])
        rt.first_seen = t_arrive
        timelines[rid] = rt
    return timelines


def _intervals(
    layout: ad.YardLayout, timelines: dict[str, ad.ResourceTrack], track: str, t: float
) -> list[tuple[float, float]]:
    """Return sorted (start, end) x-extents of resources packed on ``track`` at ``t``."""
    centers = ad._packed_centers(layout, timelines, track, t)
    spans = [(cx - timelines[rid].length_m / 2.0, cx + timelines[rid].length_m / 2.0) for rid, cx in centers.items()]
    return sorted(spans)


def _has_overlap(intervals: list[tuple[float, float]]) -> bool:
    """Return True if any two sorted intervals overlap by more than a rounding epsilon."""
    return any(a[1] - b[0] > 1e-6 for a, b in itertools.pairwise(intervals))


# --- Segment extraction -----------------------------------------------------


class TestExtractTimelines:
    """Tests for movement-segment extraction."""

    def test_wagon_segments_follow_route_path(self, w0001_locations, w0001_states):
        """Wagon dwells/moves should follow the recorded location sequence."""
        timelines = ad.extract_timelines(w0001_locations, w0001_states)
        rt = timelines['W0001']
        assert rt.resource_type == 'wagon'
        assert [d.track for d in rt.dwells] == ['collection1', 'retrofit1', 'WS_01']
        assert len(rt.moves) == 2

    def test_wagon_departure_uses_moving_event(self, w0001_locations, w0001_states):
        """The move should start at the route_path/moving row and end at arrival."""
        rt = ad.extract_timelines(w0001_locations, w0001_states)['W0001']
        first_move = rt.moves[0]
        assert first_move.t_depart == 433.0
        assert first_move.t_arrive == 493.0
        assert first_move.route == ('collection1', 'Mainline', 'retrofit1')

    def test_retrofit_timestamp_detected(self, w0001_locations, w0001_states):
        """The retrofit-completion timestamp should be captured for colouring."""
        rt = ad.extract_timelines(w0001_locations, w0001_states)['W0001']
        assert rt.t_retrofitted == 574.0

    def test_locomotive_uses_default_transit_and_length(self, loco_locations):
        """Locomotives use the default transit fallback and default length."""
        rt = ad.extract_timelines(loco_locations, None)['LOCO_01']
        assert rt.resource_type == 'locomotive'
        assert rt.length_m == ad.LOCO_LENGTH_M
        assert rt.moves[0].t_depart == pytest.approx(420.0 - ad.DEFAULT_TRANSIT_MIN)

    def test_wagon_length_from_schedule(self, w0001_locations, w0001_states, train_schedule):
        """Wagon length should be taken from the train schedule when provided."""
        lengths = ad.wagon_lengths(train_schedule)
        rt = ad.extract_timelines(w0001_locations, w0001_states, lengths)['W0001']
        assert rt.length_m == pytest.approx(15.9)

    def test_empty_input_returns_empty(self):
        """Empty or missing location logs should yield no timelines."""
        assert ad.extract_timelines(None, None) == {}
        assert ad.extract_timelines(pd.DataFrame(), None) == {}


class TestWagonLengths:
    """Tests for the wagon-length lookup helper."""

    def test_maps_ids_to_lengths(self, train_schedule):
        """Each wagon id should map to its float length."""
        lengths = ad.wagon_lengths(train_schedule)
        assert lengths == {'W0001': pytest.approx(15.9), 'W0002': pytest.approx(23.5)}

    def test_missing_columns_returns_empty(self):
        """A schedule without the expected columns yields an empty map."""
        assert ad.wagon_lengths(pd.DataFrame([{'foo': 1}])) == {}
        assert ad.wagon_lengths(None) == {}


# --- Yard layout ------------------------------------------------------------


class TestBuildLayout:
    """Tests for the left-throat synthetic yard layout."""

    def test_tracks_are_left_throat(self, layout):
        """Every non-mainline track's throat is on its left edge and extends right."""
        for tl in layout.tracks.values():
            if tl.zone == 'mainline':
                continue
            assert tl.throat_x == pytest.approx(tl.x_start)
            assert tl.x_end > tl.x_start

    def test_mainline_is_bottom_corridor(self, layout):
        """The mainline sits at the top lane in single-column mode."""
        main = layout.tracks['Mainline']
        assert main.zone == 'single'
        assert main.lane_y == max(t.lane_y for t in layout.tracks.values())

    def test_workshop_tagged_with_bays(self, layout):
        """Workshop tracks should be tagged and carry their bay count."""
        ws = layout.tracks['WS_01']
        assert ws.is_workshop is True
        assert ws.bays == 2

    def test_x_axis_is_metric(self, layout):
        """Non-mainline tracks span their real length in metres from the throat."""
        assert layout.tracks['collection1'].x_end - layout.tracks['collection1'].x_start == pytest.approx(500.0)
        assert layout.tracks['retrofitted1'].x_end - layout.tracks['retrofitted1'].x_start == pytest.approx(704.0)

    def test_single_mode_without_remote(self, layout):
        """Without a remote cluster the layout uses the single-column mode."""
        assert layout.mode == 'single'


# --- Stack (LIFO) compaction ------------------------------------------------


class TestCompaction:
    """Tests for the per-frame, hole-free stack compaction."""

    def test_stack_packs_earliest_deepest(self):
        """Earliest arrival sits at the far (right) end; later arrivals toward the throat."""
        layout = _one_track_layout('collection', 100.0)
        timelines = _wagons('T', [('A', 16.0, 0.0, 200.0), ('B', 16.0, 10.0, 200.0)])
        centers = ad._packed_centers(layout, timelines, 'T', 100.0)
        assert centers['A'] == pytest.approx(92.0)  # 100 - 16/2, flush against far end
        assert centers['B'] < centers['A']

    def test_no_gap_between_adjacent(self):
        """Adjacent packed wagons sit flush (no hole)."""
        layout = _one_track_layout('collection', 100.0)
        timelines = _wagons('T', [('A', 16.0, 0.0, 200.0), ('B', 24.0, 10.0, 200.0)])
        a, b = (
            ad._packed_centers(layout, timelines, 'T', 100.0)['A'],
            ad._packed_centers(layout, timelines, 'T', 100.0)['B'],
        )
        a_near = a - 16.0 / 2  # throat-side edge of A
        b_far = b + 24.0 / 2  # far-side edge of B
        assert a_near - b_far == pytest.approx(ad.UNIFORM_GAP_M)

    def test_departure_makes_others_slide(self):
        """When a wagon departs, the remaining present wagons re-pack flush (no hole)."""
        layout = _one_track_layout('collection', 100.0)
        timelines = _wagons('T', [('A', 16.0, 0.0, 50.0), ('B', 16.0, 0.0, 200.0)])
        # While both present, B is left of A; after A leaves, B slides to the far end.
        assert ad._packed_centers(layout, timelines, 'T', 10.0)['B'] < 92.0
        assert ad._packed_centers(layout, timelines, 'T', 60.0)['B'] == pytest.approx(92.0)

    def test_locomotive_sits_on_throat_side(self):
        """A locomotive parked with wagons sits on the throat (left) side of them."""
        layout = _one_track_layout('collection', 100.0)
        timelines = _wagons('T', [('W', 16.0, 0.0, 200.0)])
        loco = ad.ResourceTrack('L', 'locomotive', length_m=19.0, dwells=[ad.Dwell('T', 10.0, 200.0)])
        loco.first_seen = 10.0
        timelines['L'] = loco
        centers = ad._packed_centers(layout, timelines, 'T', 100.0)
        assert centers['L'] < centers['W']

    def test_workshop_uses_bay_slots(self):
        """Workshop occupants take distinct bay-slot centres inside the box."""
        layout = _one_track_layout('workshop', 260.0, bays=2)
        timelines = _wagons('T', [('A', 16.0, 0.0, 200.0), ('B', 16.0, 10.0, 200.0)])
        centers = sorted(ad._packed_centers(layout, timelines, 'T', 100.0).values())
        assert centers == pytest.approx([260.0 * 0.25, 260.0 * 0.75])

    def test_no_overlap_when_wagons_fit(self):
        """Wagons whose true lengths fit must never overlap."""
        layout = _one_track_layout('collection', 100.0)
        timelines = _wagons('T', [(f'W{i}', 10.0, float(i), 200.0) for i in range(7)])
        assert not _has_overlap(_intervals(layout, timelines, 'T', 150.0))

    def test_overflow_positions_are_distinct(self):
        """Over-capacity wagons pack sequentially (distinct centres), never stacked."""
        layout = _one_track_layout('collection', 10.0)
        timelines = _wagons('T', [(f'W{i}', 1.0, float(i), 200.0) for i in range(15)])
        centres = list(ad._packed_centers(layout, timelines, 'T', 150.0).values())
        assert len({round(c, 6) for c in centres}) == len(centres)

    def test_workshop_overflow_stays_within_box(self):
        """More wagons than bays must still render inside the workshop box."""
        layout = _one_track_layout('workshop', 260.0, bays=2)
        timelines = _wagons('T', [(f'W{i}', 16.0, float(i), 200.0) for i in range(3)])
        tl = layout.tracks['T']
        for rid, center in ad._packed_centers(layout, timelines, 'T', 150.0).items():
            half = timelines[rid].length_m / 2.0
            assert center - half >= tl.x_start - 1e-6
            assert center + half <= tl.x_end + 1e-6


# --- Consist coupling -------------------------------------------------------


class TestConsists:
    """Tests for loco/wagon consist inference and synchronised motion."""

    @staticmethod
    def _coupled() -> dict[str, ad.ResourceTrack]:
        """Build a loco and two wagons making the same collection1->retrofit1 trip."""
        wagons = {}
        for rid, t_arr in (('W1', 0.0), ('W2', 5.0)):
            rt = ad.ResourceTrack(rid, 'wagon', length_m=16.0)
            rt.dwells = [ad.Dwell('collection1', t_arr, 100.0), ad.Dwell('retrofit1', 200.0, math.inf)]
            rt.moves = [ad.Move(100.0, 200.0, ('collection1', 'Mainline', 'retrofit1'), 'collection1', 'retrofit1')]
            rt.first_seen = t_arr
            wagons[rid] = rt
        loco = ad.ResourceTrack('L', 'locomotive', length_m=19.0)
        loco.dwells = [ad.Dwell('collection1', 90.0, 95.0), ad.Dwell('retrofit1', 130.0, math.inf)]
        loco.moves = [ad.Move(95.0, 130.0, (), 'collection1', 'retrofit1')]
        loco.first_seen = 90.0
        return {**wagons, 'L': loco}

    def test_loco_move_snaps_to_rake_window(self):
        """The loco's hauling move is snapped to the rake's depart/arrive window."""
        timelines = self._coupled()
        legs = ad.infer_consists(timelines)
        assert 'L' in legs
        leg = legs['L'][0]
        assert (leg.t_depart, leg.t_arrive) == (100.0, 200.0)
        assert timelines['L'].moves[0].t_depart == 100.0
        assert timelines['L'].moves[0].t_arrive == 200.0

    def test_consist_includes_loco_and_wagons(self):
        """The leg lists the loco first, then its wagons."""
        leg = ad.infer_consists(self._coupled())['L'][0]
        assert leg.car_ids[0] == 'L'
        assert set(leg.car_ids[1:]) == {'W1', 'W2'}

    def test_loco_leads_throat_side_during_transit(self, tracks_config, topology, workshops_config):
        """Mid-transit the loco stays on the throat side and cars do not overlap."""
        graph = rg.parse_routes(
            {'routes': [{'id': 'r', 'duration': 5.0, 'path': ['collection1', 'Mainline', 'retrofit1']}]}
        )
        layout = ad.build_layout(tracks_config, topology, workshops_config, graph, sorted(graph.track_ids))
        timelines = self._coupled()
        legs = ad.assign_positions(layout, timelines)
        # At arrival the loco sits on the throat side (smaller x) of both wagons.
        loco_pos = ad.position_at(timelines['L'], layout, timelines, 200.0, legs)
        w1_pos = ad.position_at(timelines['W1'], layout, timelines, 200.0, legs)
        w2_pos = ad.position_at(timelines['W2'], layout, timelines, 200.0, legs)
        assert loco_pos is not None
        assert w1_pos is not None
        assert w2_pos is not None
        loco_x = loco_pos[0]
        w1_x = w1_pos[0]
        w2_x = w2_pos[0]
        assert loco_x < w1_x
        assert loco_x < w2_x
        assert abs(w1_x - w2_x) > 1e-6  # the two wagons do not coincide

    def test_unmatched_loco_trip_left_alone(self):
        """A loco trip with no matching wagons produces no leg."""
        loco = ad.ResourceTrack('L', 'locomotive', length_m=19.0)
        loco.dwells = [ad.Dwell('track_19', 0.0, 10.0), ad.Dwell('collection1', 22.0, math.inf)]
        loco.moves = [ad.Move(10.0, 22.0, (), 'track_19', 'collection1')]
        loco.first_seen = 0.0
        assert ad.infer_consists({'L': loco}) == {}


# --- Frame stats ------------------------------------------------------------


class TestFrameStats:
    """Tests for the per-frame live statistics."""

    @staticmethod
    def _timelines() -> dict[str, ad.ResourceTrack]:
        """Two wagons on one track; W1 retrofitted at t=50, W2 never."""
        w1 = ad.ResourceTrack('W1', 'wagon', length_m=20.0, dwells=[ad.Dwell('T', 0.0, math.inf)])
        w1.first_seen, w1.t_retrofitted = 0.0, 50.0
        w2 = ad.ResourceTrack('W2', 'wagon', length_m=30.0, dwells=[ad.Dwell('T', 10.0, math.inf)])
        w2.first_seen = 10.0
        return {'W1': w1, 'W2': w2}

    def test_counts_before_and_after_retrofit(self):
        """to_retrofit / retrofitted counts reflect presence and completion."""
        layout = _one_track_layout('collection', 100.0)
        timelines = self._timelines()
        early = ad._frame_stats(layout, timelines, 5.0, [])
        assert (early.to_retrofit, early.present_retrofitted, early.cumulative_retrofitted) == (1, 0, 0)
        late = ad._frame_stats(layout, timelines, 60.0, [])
        assert (late.to_retrofit, late.present_retrofitted, late.cumulative_retrofitted) == (1, 1, 1)

    def test_track_utilization_is_occupied_over_real_length(self):
        """Utilization sums real wagon lengths over the real track length."""
        layout = _one_track_layout('collection', 100.0)
        stats = ad._frame_stats(layout, self._timelines(), 60.0, [])
        assert stats.utilization['T'] == pytest.approx(0.5)  # (20 + 30) / 100

    def test_cumulative_rejected_is_monotonic(self):
        """Rejected counter accumulates as timestamps are passed."""
        layout = _one_track_layout('collection', 100.0)
        timelines = self._timelines()
        rejected = [40.0, 70.0]
        assert ad._frame_stats(layout, timelines, 5.0, rejected).cumulative_rejected == 0
        assert ad._frame_stats(layout, timelines, 60.0, rejected).cumulative_rejected == 1
        assert ad._frame_stats(layout, timelines, 100.0, rejected).cumulative_rejected == 2

    def test_mainline_excluded_from_utilization(self, layout):
        """The Mainline is excluded from per-track utilization."""
        stats = ad._frame_stats(layout, self._timelines(), 60.0, [])
        assert 'Mainline' not in stats.utilization

    def test_build_frames_attaches_stats_and_shades(self):
        """build_frames wires stats and alternating shades into every frame."""
        layout = _one_track_layout('collection', 100.0)
        frames = ad.build_frames(layout, self._timelines(), num_frames=5, rejected_at=[40.0])
        assert all(isinstance(f.stats, ad.FrameStats) for f in frames)
        last = frames[-1]
        assert len(last.wagon_shade) == len(last.wagon_x)
        if len(last.wagon_shade) == 2:
            assert set(last.wagon_shade) == {0, 1}


# --- Position resolver ------------------------------------------------------


class TestPositionAt:
    """Tests for the position resolver."""

    def test_parked_uses_compacted_slot(self, layout, w0001_locations, w0001_states):
        """At a dwell the wagon sits at its compacted slot on the track lane."""
        timelines = ad.extract_timelines(w0001_locations, w0001_states)
        legs = ad.assign_positions(layout, timelines)
        rt = timelines['W0001']
        expected_x = ad._packed_centers(layout, timelines, 'collection1', 360.0)['W0001']
        pos = ad.position_at(rt, layout, timelines, 360.0, legs)
        assert pos == pytest.approx((expected_x, layout.tracks['collection1'].lane_y))

    def test_move_routes_through_throat(self, layout, w0001_locations, w0001_states):
        """An intra-zone move routes through the throat (x == throat_x)."""
        timelines = ad.extract_timelines(w0001_locations, w0001_states)
        ad.assign_positions(layout, timelines)
        waypoints = ad._move_waypoints(layout, timelines['W0001'].moves[0])
        assert any(abs(p[0] - layout.throat_x) < 1e-9 for p in waypoints)

    def test_none_before_first_seen(self, layout, w0001_locations, w0001_states):
        """A resource has no position before it first appears."""
        timelines = ad.extract_timelines(w0001_locations, w0001_states)
        legs = ad.assign_positions(layout, timelines)
        assert ad.position_at(timelines['W0001'], layout, timelines, 100.0, legs) is None


# --- Frame builder ----------------------------------------------------------


class TestBuildFrames:
    """Tests for the per-frame builder."""

    def test_frame_count_matches_resolution(self, layout, w0001_locations, w0001_states):
        """The number of frames equals the requested resolution."""
        timelines = ad.extract_timelines(w0001_locations, w0001_states)
        assert len(ad.build_frames(layout, timelines, num_frames=50)) == 50

    def test_first_frame_carries_position_and_length(self, layout, w0001_locations, w0001_states, train_schedule):
        """The first frame places the wagon at its compacted slot and carries its length."""
        lengths = ad.wagon_lengths(train_schedule)
        timelines = ad.extract_timelines(w0001_locations, w0001_states, lengths)
        frames = ad.build_frames(layout, timelines, num_frames=10)
        first = frames[0]
        assert first.t == pytest.approx(360.0)
        assert first.wagon_ids == ['W0001']
        assert first.wagon_len[0] == pytest.approx(15.9)
        expected_x = ad._packed_centers(layout, timelines, 'collection1', 360.0)['W0001']
        assert first.wagon_x[0] == pytest.approx(expected_x)

    def test_color_flips_at_retrofit_time(self, layout, w0001_locations, w0001_states):
        """Wagon colour switches from blue to green at the retrofit timestamp."""
        timelines = ad.extract_timelines(w0001_locations, w0001_states)
        frames = ad.build_frames(layout, timelines, num_frames=3, bounds=(560.0, 580.0))
        assert frames[0].wagon_color[0] == ad.WAGON_COLOR_PENDING
        assert frames[-1].wagon_color[0] == ad.WAGON_COLOR_DONE

    def test_locomotives_separated_from_wagons(self, layout, w0001_locations, loco_locations):
        """Locomotives appear only in the locomotive arrays, never the wagon arrays."""
        combined = pd.concat([w0001_locations, loco_locations], ignore_index=True)
        timelines = ad.extract_timelines(combined, None)
        frames = ad.build_frames(layout, timelines, num_frames=5)
        assert any('LOCO_01' in f.loco_ids for f in frames)
        assert all('LOCO_01' not in f.wagon_ids for f in frames)
        assert all(length == ad.LOCO_LENGTH_M for f in frames for length in f.loco_len)

    def test_empty_timelines_returns_empty(self, layout):
        """No timelines yields no frames."""
        assert ad.build_frames(layout, {}, num_frames=10) == []

    def test_sim_time_bounds(self, w0001_locations, loco_locations):
        """Simulation bounds span the earliest and latest resource timestamps."""
        combined = pd.concat([w0001_locations, loco_locations], ignore_index=True)
        timelines = ad.extract_timelines(combined, None)
        assert ad.sim_time_bounds(timelines) == (360.0, 508.0)

    def test_single_frame_does_not_divide_by_zero(self, layout, w0001_locations, w0001_states):
        """A single-frame request produces one finite-time frame."""
        timelines = ad.extract_timelines(w0001_locations, w0001_states)
        frames = ad.build_frames(layout, timelines, num_frames=1)
        assert len(frames) == 1
        assert math.isfinite(frames[0].t)


# --- Routes-aware layout ----------------------------------------------------


class TestRoutesAwareLayout:
    """Tests for routes-aware, id-robust layout building."""

    @staticmethod
    def _h4r_config() -> tuple[list[dict], dict, list[dict], dict]:
        """Return hack4rail-style config with a workshop id mismatch (WS1 vs WS_01)."""
        tracks = [
            {'id': 'WS1', 'edges': ['WS1'], 'type': 'workshop'},
            {'id': 'collection1', 'edges': ['collection1'], 'type': 'collection'},
            {'id': 'track_19', 'edges': ['track_19'], 'type': 'rescource_parking'},
            {'id': 'Mainline', 'edges': ['Mainline'], 'type': 'mainline'},
            {'id': 'retrofit', 'edges': ['retrofit'], 'type': 'retrofit'},
        ]
        topology = {
            'edges': {
                'WS1': {'length': 260.0},
                'collection1': {'length': 740.0},
                'track_19': {'length': 169.0},
                'Mainline': {'length': 8000.0},
                'retrofit': {'length': 740.0},
            }
        }
        workshops = [{'id': 'WS_01', 'retrofit_stations': 2, 'track': 'track_WS1'}]
        routes = {
            'routes': [
                {'id': 'a', 'duration': 5.0, 'path': ['track_19', 'WS_01']},
                {'id': 'b', 'duration': 5.0, 'path': ['track_19', 'retrofit']},
                {'id': 'c', 'duration': 60.0, 'path': ['track_19', 'Mainline', 'collection1']},
            ]
        }
        return tracks, topology, workshops, routes

    def test_workshop_id_mismatch_resolved(self):
        """A workshop id (WS_01) absent from tracks.json still gets a lane with bays."""
        tracks, topology, workshops, routes = self._h4r_config()
        graph = rg.parse_routes(routes)
        layout = ad.build_layout(tracks, topology, workshops, graph, sorted(graph.track_ids))
        ws = layout.tracks['WS_01']
        assert ws.is_workshop is True
        assert ws.bays == 2
        assert ws.length_m == pytest.approx(260.0)

    def test_two_zone_placement(self):
        """With a remote cluster the layout uses three zones (left | corridor | right)."""
        tracks, topology, workshops, routes = self._h4r_config()
        graph = rg.parse_routes(routes)
        layout = ad.build_layout(tracks, topology, workshops, graph, sorted(graph.track_ids))
        assert layout.mode == 'zones'
        assert layout.tracks['retrofit'].zone == 'left'
        assert layout.tracks['collection1'].zone == 'right'
        assert layout.tracks['Mainline'].zone == 'middle'
        # Local yard left of left ladder, remote right of right ladder.
        assert layout.tracks['retrofit'].x_end <= layout.left_throat_x + 1e-9
        assert layout.tracks['collection1'].x_start >= layout.right_throat_x - 1e-9
        assert layout.left_throat_x < layout.right_throat_x < layout.x_max

    def test_mainline_corridor_in_the_middle(self):
        """The mainline corridor spans between the two ladders at corridor_y."""
        tracks, topology, workshops, routes = self._h4r_config()
        graph = rg.parse_routes(routes)
        layout = ad.build_layout(tracks, topology, workshops, graph, sorted(graph.track_ids))
        main = layout.tracks['Mainline']
        assert main.lane_y == pytest.approx(layout.corridor_y)
        assert main.x_start == pytest.approx(layout.left_throat_x)
        assert main.x_end == pytest.approx(layout.right_throat_x)

    def test_cross_zone_move_passes_through_corridor(self):
        """A local<->remote move routes through the Mainline corridor height."""
        tracks, topology, workshops, routes = self._h4r_config()
        graph = rg.parse_routes(routes)
        layout = ad.build_layout(tracks, topology, workshops, graph, sorted(graph.track_ids))
        rt = ad.ResourceTrack('W', 'wagon', length_m=16.0)
        rt.dwells = [ad.Dwell('collection1', 0.0, 100.0), ad.Dwell('retrofit', 200.0, math.inf)]
        rt.moves = [ad.Move(100.0, 200.0, ('collection1', 'Mainline', 'retrofit'), 'collection1', 'retrofit')]
        rt.first_seen = 0.0
        ad.assign_positions(layout, {'W': rt})
        waypoints = ad._move_waypoints(layout, rt.moves[0])
        corridor_pts = [p for p in waypoints if abs(p[1] - layout.corridor_y) < 1e-9]
        assert any(abs(p[0] - layout.left_throat_x) < 1e-9 for p in corridor_pts)
        assert any(abs(p[0] - layout.right_throat_x) < 1e-9 for p in corridor_pts)

    def test_layout_without_routes_is_single_mode(self):
        """Without a route graph the layout falls back to a single stacked column."""
        tracks, topology, workshops, _routes = self._h4r_config()
        layout = ad.build_layout(tracks, topology, workshops)
        assert layout.mode == 'single'
        assert set(layout.tracks) == {'WS1', 'collection1', 'track_19', 'Mainline', 'retrofit'}
        assert layout.tracks['Mainline'].lane_y == max(t.lane_y for t in layout.tracks.values())


class TestActiveTrackIds:
    """Tests for the active-id collector."""

    def test_union_of_routes_and_locations(self):
        """Active ids combine route track ids and event-log locations."""
        graph = rg.parse_routes({'routes': [{'id': 'a', 'duration': 5.0, 'path': ['track_19', 'WS_01']}]})
        locs = pd.DataFrame([{'location': 'collection1'}, {'location': 'WS_01'}, {'location': None}])
        ids = ad.active_track_ids(locs, graph)
        assert set(ids) == {'track_19', 'WS_01', 'collection1'}

    def test_handles_missing_inputs(self):
        """Missing locations / graph degrade gracefully."""
        assert ad.active_track_ids(None, None) == []
