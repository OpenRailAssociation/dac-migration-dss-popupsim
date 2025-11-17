"""Automatic routing for railway networks."""

import json
import networkx as nx
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Route:
    """A route between two points in the railway network."""
    start_node: str
    end_node: str
    path: List[str]
    distance: float


class RailwayRouter:
    """Automatic router for railway networks."""
    
    def __init__(self, network_data: Dict):
        """Initialize router with railway network data."""
        self.network = network_data
        self.graph = self._build_graph()
    
    def _build_graph(self) -> nx.Graph:
        """Build NetworkX graph from railway data."""
        G = nx.Graph()
        
        for way in self.network.get('ways', []):
            geometry = way.get('geometry', [])
            way_id = str(way.get('id', ''))
            
            # Add nodes and edges from geometry
            for i in range(len(geometry) - 1):
                node1 = f"node_{geometry[i]['lat']}_{geometry[i]['lon']}"
                node2 = f"node_{geometry[i+1]['lat']}_{geometry[i+1]['lon']}"
                
                # Calculate distance between consecutive points
                dist = self._calculate_distance(geometry[i], geometry[i+1])
                
                G.add_edge(node1, node2, weight=dist, way_id=way_id)
        
        return G
    
    def _calculate_distance(self, point1: Dict, point2: Dict) -> float:
        """Calculate distance between two points using projected coordinates."""
        if 'x' in point1 and 'y' in point1:
            # Use projected coordinates if available
            dx = point2['x'] - point1['x']
            dy = point2['y'] - point1['y']
            return (dx**2 + dy**2)**0.5
        else:
            # Fallback to simple lat/lon difference
            dlat = point2['lat'] - point1['lat']
            dlon = point2['lon'] - point1['lon']
            return (dlat**2 + dlon**2)**0.5 * 111000  # Rough conversion to meters
    
    def find_route(self, start_coords: Tuple[float, float], 
                   end_coords: Tuple[float, float]) -> Optional[Route]:
        """Find shortest route between two coordinate points."""
        start_node = self._find_nearest_node(start_coords)
        end_node = self._find_nearest_node(end_coords)
        
        if not start_node or not end_node:
            return None
        
        try:
            path = nx.shortest_path(self.graph, start_node, end_node, weight='weight')
            distance = nx.shortest_path_length(self.graph, start_node, end_node, weight='weight')
            
            return Route(start_node, end_node, path, distance)
        except nx.NetworkXNoPath:
            return None
    
    def find_waypoint_route(self, waypoints: List[Tuple[float, float]]) -> Optional[Route]:
        """Find route through multiple waypoints."""
        if len(waypoints) < 2:
            return None
        
        full_path = []
        total_distance = 0
        
        for i in range(len(waypoints) - 1):
            segment = self.find_route(waypoints[i], waypoints[i + 1])
            if not segment:
                return None
            
            if full_path and segment.path[0] == full_path[-1]:
                full_path.extend(segment.path[1:])
            else:
                full_path.extend(segment.path)
            
            total_distance += segment.distance
        
        start_node = self._find_nearest_node(waypoints[0])
        end_node = self._find_nearest_node(waypoints[-1])
        
        return Route(start_node, end_node, full_path, total_distance)
    
    def _find_nearest_node(self, coords: Tuple[float, float]) -> Optional[str]:
        """Find the nearest node to given coordinates."""
        lat, lon = coords
        min_dist = float('inf')
        nearest_node = None
        
        for way in self.network.get('ways', []):
            for point in way.get('geometry', []):
                node_id = f"node_{point['lat']}_{point['lon']}"
                dist = ((point['lat'] - lat)**2 + (point['lon'] - lon)**2)**0.5
                
                if dist < min_dist:
                    min_dist = dist
                    nearest_node = node_id
        
        return nearest_node


def load_network(filepath: str) -> RailwayRouter:
    """Load railway network and create router."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return RailwayRouter(data)


def auto_route(network_file: str, start_coords: Tuple[float, float], 
               end_coords: Tuple[float, float]) -> Optional[Route]:
    """Automatically find route between two points."""
    router = load_network(network_file)
    return router.find_route(start_coords, end_coords)


def auto_waypoint_route(network_file: str, waypoints: List[Tuple[float, float]]) -> Optional[Route]:
    """Automatically find route through waypoints."""
    router = load_network(network_file)
    return router.find_waypoint_route(waypoints)