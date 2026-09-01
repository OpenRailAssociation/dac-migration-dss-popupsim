"""Pure parsing of ``routes.json`` into a connectivity graph.

``routes.json`` lists directed routes between tracks, each with an ordered
``path`` (the tracks/edges traversed) and a ``duration``. This module turns that
into:

* an undirected adjacency map (track -> {neighbour: min duration}),
* the subset of *direct* neighbours (hops that do not traverse the ``Mainline``),
* a cluster classification of every track relative to the locomotive hub.

No Streamlit / Plotly / pandas imports, so it stays trivially unit-testable.
"""

from __future__ import annotations

from collections import defaultdict
from collections import deque
from dataclasses import dataclass
import itertools
import math
from typing import Any

# The locomotive depot acts as the local hub; the Mainline is the long-haul
# connector between the local yard and the arrival / remote-storage side.
HUB_TRACK: str = 'track_19'
MAINLINE: str = 'Mainline'

# Cluster ranks drive top-to-bottom lane ordering (remote on top, Mainline as
# the central spine, the local yard below).
CLUSTER_RANK: dict[str, int] = {'remote': 0, 'mainline': 1, 'hub': 2, 'local': 2}


@dataclass(frozen=True)
class RouteGraph:
    """Connectivity derived from ``routes.json``."""

    adjacency: dict[str, dict[str, float]]
    direct: dict[str, dict[str, float]]
    cluster: dict[str, str]
    track_ids: frozenset[str]
    paths: dict[tuple[str, str], tuple[str, ...]]

    def neighbours(self, track_id: str) -> dict[str, float]:
        """Return the adjacency (neighbour -> min duration) for a track."""
        return self.adjacency.get(track_id, {})


def _add_edge(store: dict[str, dict[str, float]], a: str, b: str, duration: float) -> None:
    """Add/relax an undirected edge with the minimum duration seen."""
    store[a][b] = min(store[a].get(b, math.inf), duration)
    store[b][a] = min(store[b].get(a, math.inf), duration)


def _classify_clusters(direct: dict[str, dict[str, float]], track_ids: set[str]) -> dict[str, str]:
    """Classify tracks as hub / local / remote / mainline.

    ``local`` = reachable from :data:`HUB_TRACK` using only direct (non-Mainline)
    hops; ``remote`` = everything else (only reachable across the Mainline).
    """
    local: set[str] = set()
    if HUB_TRACK in track_ids:
        queue: deque[str] = deque([HUB_TRACK])
        local.add(HUB_TRACK)
        while queue:
            node = queue.popleft()
            for neighbour in direct.get(node, {}):
                if neighbour != MAINLINE and neighbour not in local:
                    local.add(neighbour)
                    queue.append(neighbour)

    cluster: dict[str, str] = {}
    for track_id in track_ids:
        if track_id == MAINLINE:
            cluster[track_id] = 'mainline'
        elif track_id == HUB_TRACK:
            cluster[track_id] = 'hub'
        elif track_id in local:
            cluster[track_id] = 'local'
        else:
            cluster[track_id] = 'remote'
    return cluster


def parse_routes(routes_json: dict[str, Any] | None) -> RouteGraph:
    """Parse a ``routes.json`` payload into a :class:`RouteGraph`.

    Returns an empty graph (all-local classification) when no routes are given.
    """
    routes = (routes_json or {}).get('routes', [])
    adjacency: dict[str, dict[str, float]] = defaultdict(dict)
    direct: dict[str, dict[str, float]] = defaultdict(dict)
    paths: dict[tuple[str, str], tuple[str, ...]] = {}
    track_ids: set[str] = set()

    for route in routes:
        path = [str(p) for p in route.get('path', []) if str(p)]
        if len(path) < 2:
            continue
        duration = float(route.get('duration', 0.0))
        track_ids.update(path)
        paths[(path[0], path[-1])] = tuple(path)
        for a, b in itertools.pairwise(path):
            _add_edge(adjacency, a, b, duration)
        if MAINLINE not in path:
            _add_edge(direct, path[0], path[-1], duration)

    cluster = _classify_clusters(direct, track_ids)
    return RouteGraph(
        adjacency={k: dict(v) for k, v in adjacency.items()},
        direct={k: dict(v) for k, v in direct.items()},
        cluster=cluster,
        track_ids=frozenset(track_ids),
        paths=paths,
    )
