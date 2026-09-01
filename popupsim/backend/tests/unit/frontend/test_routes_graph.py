"""Unit tests for routes.json parsing and clustering (routes_graph.py)."""

from dashboard_components import routes_graph as rg
import pytest


@pytest.fixture
def routes_json() -> dict:
    """Return a routes payload mirroring the hack4rail connectivity shape."""
    return {
        'routes': [
            {'id': 'track_19_collection1', 'duration': 60.0, 'path': ['track_19', 'Mainline', 'collection1']},
            {'id': 'collection1_retrofit', 'duration': 60.0, 'path': ['collection1', 'Mainline', 'retrofit']},
            {'id': 'track_19_retrofit', 'duration': 5.0, 'path': ['track_19', 'retrofit']},
            {'id': 'track_19_WS_01', 'duration': 5.0, 'path': ['track_19', 'WS_01']},
            {'id': 'retrofit_WS_01', 'duration': 5.0, 'path': ['retrofit', 'WS_01']},
            {'id': 'WS_01_retrofitted', 'duration': 5.0, 'path': ['WS_01', 'retrofitted']},
            {'id': 'retrofitted_parking1', 'duration': 30.0, 'path': ['retrofitted', 'parking1']},
            {'id': 'retrofitted_parking6', 'duration': 30.0, 'path': ['retrofitted', 'Mainline', 'parking6']},
        ]
    }


class TestParseRoutes:
    """Tests for parse_routes."""

    def test_empty_input_yields_empty_graph(self):
        """No routes yields an empty, all-local graph."""
        graph = rg.parse_routes(None)
        assert graph.track_ids == frozenset()
        assert graph.adjacency == {}

    def test_track_ids_collected(self, routes_json):
        """Every track referenced in any path is collected."""
        graph = rg.parse_routes(routes_json)
        assert 'WS_01' in graph.track_ids
        assert 'collection1' in graph.track_ids
        assert 'Mainline' in graph.track_ids

    def test_adjacency_is_undirected_with_min_duration(self, routes_json):
        """Adjacency is symmetric and keeps the minimum duration."""
        graph = rg.parse_routes(routes_json)
        assert graph.adjacency['track_19']['retrofit'] == 5.0
        assert graph.adjacency['retrofit']['track_19'] == 5.0

    def test_direct_excludes_mainline_hops(self, routes_json):
        """Direct neighbours only include non-Mainline hops."""
        graph = rg.parse_routes(routes_json)
        assert 'retrofit' in graph.direct['track_19']  # direct 5-min hop
        assert 'collection1' not in graph.direct.get('track_19', {})  # only via Mainline

    def test_paths_recorded(self, routes_json):
        """Endpoint pairs map to their full ordered path."""
        graph = rg.parse_routes(routes_json)
        assert graph.paths[('track_19', 'collection1')] == ('track_19', 'Mainline', 'collection1')


class TestClusters:
    """Tests for cluster classification."""

    def test_hub_and_local_and_remote(self, routes_json):
        """track_19 is the hub; locally-reachable tracks are local; rest remote."""
        graph = rg.parse_routes(routes_json)
        assert graph.cluster['track_19'] == 'hub'
        assert graph.cluster['retrofit'] == 'local'
        assert graph.cluster['WS_01'] == 'local'
        assert graph.cluster['retrofitted'] == 'local'
        assert graph.cluster['parking1'] == 'local'  # directly off retrofitted
        assert graph.cluster['Mainline'] == 'mainline'

    def test_collection_and_far_parking_are_remote(self, routes_json):
        """Tracks only reachable across the Mainline are remote."""
        graph = rg.parse_routes(routes_json)
        assert graph.cluster['collection1'] == 'remote'
        assert graph.cluster['parking6'] == 'remote'

    def test_cluster_rank_orders_remote_above_local(self):
        """Cluster ranks place remote on top and local below the Mainline."""
        assert rg.CLUSTER_RANK['remote'] < rg.CLUSTER_RANK['mainline'] < rg.CLUSTER_RANK['local']
