# Infrastructure Context - Detailed Design

## Übersicht

Der Infrastructure Context verwaltet die Gleistopologie als Knoten-Kanten-Modell und stellt die räumliche Grundlage für alle Rangier- und Transportoperationen bereit.

## Domain Model

### **Graph-Implementierung (MVP + Migration)**

#### **Phase 1: Simple Graph (MVP)**
```python
class SimpleGraph:
    def __init__(self):
        self._adjacency: Dict[str, List[Tuple[str, float]]] = {}  # node -> [(neighbor, weight)]
    
    def add_edge(self, from_node: str, to_node: str, weight: float = 1.0) -> None:
        if from_node not in self._adjacency:
            self._adjacency[from_node] = []
        if to_node not in self._adjacency:
            self._adjacency[to_node] = []
        
        self._adjacency[from_node].append((to_node, weight))
        self._adjacency[to_node].append((from_node, weight))  # Bidirectional
    
    def dijkstra(self, start: str, end: str) -> Optional[List[str]]:
        """Simple Dijkstra implementation"""
        if start not in self._adjacency or end not in self._adjacency:
            return None
        
        distances = {node: float('inf') for node in self._adjacency}
        distances[start] = 0
        previous = {}
        unvisited = set(self._adjacency.keys())
        
        while unvisited:
            current = min(unvisited, key=lambda x: distances[x])
            if distances[current] == float('inf'):
                break
            
            unvisited.remove(current)
            
            if current == end:
                # Reconstruct path
                path = []
                while current in previous:
                    path.append(current)
                    current = previous[current]
                path.append(start)
                return list(reversed(path))
            
            for neighbor, weight in self._adjacency[current]:
                if neighbor in unvisited:
                    alt = distances[current] + weight
                    if alt < distances[neighbor]:
                        distances[neighbor] = alt
                        previous[neighbor] = current
        
        return None
```

#### **Phase 2: NetworkX Integration (Future)**
```python
class NetworkXGraph:
    def __init__(self):
        import networkx as nx
        self._graph = nx.Graph()
    
    def add_edge(self, from_node: str, to_node: str, weight: float = 1.0) -> None:
        self._graph.add_edge(from_node, to_node, weight=weight)
    
    def dijkstra(self, start: str, end: str) -> Optional[List[str]]:
        try:
            return nx.shortest_path(self._graph, start, end, weight='weight')
        except nx.NetworkXNoPath:
            return None
```

### **Entities (MVP Version)**

#### **Track (Gleis)**
```python
@dataclass
class Track:
    id: TrackId
    name: str
    length: Length
    track_type: TrackType
    capacity: Capacity
    current_occupancy: Length
    connected_nodes: List[NodeId]
    
    def available_capacity(self) -> Length:
        return self.capacity.free_length(self.current_occupancy)
    
    def can_accommodate(self, required_length: Length) -> bool:
        return self.available_capacity() >= required_length
    
    def reserve_space(self, length: Length) -> None:
        if not self.can_accommodate(length):
            raise InsufficientCapacityError()
        self.current_occupancy += length
```

#### **Node (Knoten)**
```python
@dataclass
class Node:
    id: NodeId
    name: str
    node_type: NodeType
    connected_tracks: List[TrackId]
    position: Position
    
    def is_junction(self) -> bool:
        return len(self.connected_tracks) > 2
```

#### **TrackNetwork (Gleistopologie)**
```python
class TrackNetwork:
    def __init__(self, use_networkx: bool = False):
        self._tracks: Dict[TrackId, Track] = {}
        self._nodes: Dict[NodeId, Node] = {}
        self._routes_cache: Dict[Tuple[TrackId, TrackId], Route] = {}
        
        # Graph implementation strategy
        if use_networkx:
            self._graph = NetworkXGraph()
        else:
            self._graph = SimpleGraph()
    
    def add_track(self, track: Track) -> None:
        self._tracks[track.id] = track
        self._invalidate_routes_cache()
        
        # Add to graph
        for node_id in track.connected_nodes:
            self._graph.add_edge(track.id.value, node_id.value, track.length.meters)
    
    def add_node(self, node: Node) -> None:
        self._nodes[node.id] = node
        
        # Connect tracks through this node
        for i, track1_id in enumerate(node.connected_tracks):
            for track2_id in node.connected_tracks[i+1:]:
                # Add connection through node (weight = 0 for node traversal)
                self._graph.add_edge(track1_id.value, track2_id.value, 0.0)
    
    def find_route(self, from_track: TrackId, to_track: TrackId) -> Optional[Route]:
        cache_key = (from_track, to_track)
        if cache_key not in self._routes_cache:
            self._routes_cache[cache_key] = self._calculate_route(from_track, to_track)
        return self._routes_cache[cache_key]
    
    def _calculate_route(self, from_track: TrackId, to_track: TrackId) -> Optional[Route]:
        path = self._graph.dijkstra(from_track.value, to_track.value)
        if not path:
            return None
        
        # Convert string path back to TrackIds and calculate metrics
        track_path = [TrackId(track_id) for track_id in path if track_id in [t.id.value for t in self._tracks.values()]]
        total_distance = sum(self._tracks[track_id].length.meters for track_id in track_path)
        estimated_time = timedelta(minutes=total_distance / 100)  # 100m/min average speed
        
        return Route(
            start_track=from_track,
            end_track=to_track,
            path=track_path,
            total_distance=Length(total_distance),
            estimated_travel_time=estimated_time
        )
    
    def get_tracks_by_type(self, track_type: TrackType) -> List[Track]:
        return [track for track in self._tracks.values() if track.track_type == track_type]
    
    def _invalidate_routes_cache(self) -> None:
        self._routes_cache.clear()
```

### **Value Objects**

#### **TrackId**
```python
@dataclass(frozen=True)
class TrackId:
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("TrackId cannot be empty")
```

#### **Length**
```python
@dataclass(frozen=True)
class Length:
    meters: float
    
    def __post_init__(self):
        if self.meters < 0:
            raise ValueError("Length cannot be negative")
    
    def __add__(self, other: 'Length') -> 'Length':
        return Length(self.meters + other.meters)
    
    def __ge__(self, other: 'Length') -> bool:
        return self.meters >= other.meters
```

#### **TrackType**
```python
class TrackType(Enum):
    HAUPTSTRECKE = "hauptstrecke"
    SAMMELGLEIS = "sammelgleis"
    WERKSTATT_ZUFUEHRUNG = "werkstatt_zufuehrung"
    WERKSTATT_ABFUEHRUNG = "werkstatt_abfuehrung"
    PARKGLEIS = "parkgleis"
    RANGIERGLEIS = "rangiergleis"
```

#### **NodeType**
```python
class NodeType(Enum):
    WEICHE = "weiche"
    PRELLBOCK = "prellbock"
    SIGNAL = "signal"
    JUNCTION = "junction"
```

#### **Capacity**
```python
@dataclass(frozen=True)
class Capacity:
    total_length: Length
    minimum_free_buffer: Length = Length(25.0)  # 25m Puffer
    
    def free_length(self, current_occupancy: Length) -> Length:
        occupied_with_buffer = current_occupancy + self.minimum_free_buffer
        if occupied_with_buffer >= self.total_length:
            return Length(0.0)
        return Length(self.total_length.meters - occupied_with_buffer.meters)
```

#### **Route**
```python
@dataclass(frozen=True)
class Route:
    start_track: TrackId
    end_track: TrackId
    path: List[TrackId]
    total_distance: Length
    estimated_travel_time: timedelta
    
    def contains_track(self, track_id: TrackId) -> bool:
        return track_id in self.path
```

### **Aggregates**

#### **StationHead (Bahnhofskopf)**
```python
class StationHead:
    def __init__(self, id: StationHeadId, name: str, tracks: List[TrackId], nodes: List[NodeId]):
        self.id = id
        self.name = name
        self._tracks = tracks
        self._nodes = nodes
        self._is_occupied = False
        self._occupying_locomotive: Optional[str] = None
    
    def is_available(self) -> bool:
        return not self._is_occupied
    
    def occupy(self, locomotive_id: str) -> None:
        if self._is_occupied:
            raise StationHeadOccupiedError(f"Station head {self.id} is already occupied")
        self._is_occupied = True
        self._occupying_locomotive = locomotive_id
        
        # Domain Event
        DomainEvents.raise_event(StationHeadOccupiedEvent(self.id, locomotive_id))
    
    def release(self) -> None:
        if not self._is_occupied:
            raise StationHeadNotOccupiedError(f"Station head {self.id} is not occupied")
        
        locomotive_id = self._occupying_locomotive
        self._is_occupied = False
        self._occupying_locomotive = None
        
        # Domain Event
        DomainEvents.raise_event(StationHeadReleasedEvent(self.id, locomotive_id))
```

## Domain Services

#### **RouteCalculationService**
```python
class RouteCalculationService:
    def __init__(self, track_network: TrackNetwork):
        self._network = track_network
    
    def calculate_shortest_route(self, from_track: TrackId, to_track: TrackId) -> Optional[Route]:
        # Dijkstra-Algorithmus für kürzeste Route
        pass
    
    def calculate_fastest_route(self, from_track: TrackId, to_track: TrackId) -> Optional[Route]:
        # Berücksichtigt Geschwindigkeitsbegrenzungen
        pass
    
    def find_alternative_routes(self, from_track: TrackId, to_track: TrackId, blocked_tracks: List[TrackId]) -> List[Route]:
        # Alternative Routen bei blockierten Gleisen
        pass
```

#### **CapacityManagementService**
```python
class CapacityManagementService:
    def __init__(self, track_repository: TrackRepository):
        self._track_repository = track_repository
    
    def find_available_tracks(self, track_type: TrackType, required_capacity: Length) -> List[Track]:
        tracks = self._track_repository.find_by_type(track_type)
        return [track for track in tracks if track.can_accommodate(required_capacity)]
    
    def get_track_utilization(self, track_id: TrackId) -> float:
        track = self._track_repository.get_by_id(track_id)
        return track.current_occupancy.meters / track.capacity.total_length.meters
```

## Repository Interfaces

#### **TrackRepository**
```python
class TrackRepository(ABC):
    @abstractmethod
    def get_by_id(self, track_id: TrackId) -> Track:
        pass
    
    @abstractmethod
    def find_by_type(self, track_type: TrackType) -> List[Track]:
        pass
    
    @abstractmethod
    def find_by_capacity_available(self, min_capacity: Length) -> List[Track]:
        pass
    
    @abstractmethod
    def save(self, track: Track) -> None:
        pass
```

#### **TrackNetworkRepository**
```python
class TrackNetworkRepository(ABC):
    @abstractmethod
    def get_network(self) -> TrackNetwork:
        pass
    
    @abstractmethod
    def save_network(self, network: TrackNetwork) -> None:
        pass
```

## Domain Events

#### **Track Events**
```python
@dataclass(frozen=True)
class TrackCapacityChangedEvent:
    track_id: TrackId
    previous_occupancy: Length
    new_occupancy: Length
    timestamp: datetime

@dataclass(frozen=True)
class TrackFullEvent:
    track_id: TrackId
    track_type: TrackType
    timestamp: datetime

@dataclass(frozen=True)
class StationHeadOccupiedEvent:
    station_head_id: StationHeadId
    locomotive_id: str  # String statt LocomotiveId - keine geteilte Entität
    timestamp: datetime

@dataclass(frozen=True)
class StationHeadReleasedEvent:
    station_head_id: StationHeadId
    locomotive_id: str  # String statt LocomotiveId - keine geteilte Entität
    timestamp: datetime
```

## Application Services

#### **TrackManagementService**
```python
class TrackManagementService:
    def __init__(self, 
                 track_repository: TrackRepository,
                 capacity_service: CapacityManagementService,
                 route_service: RouteCalculationService):
        self._track_repository = track_repository
        self._capacity_service = capacity_service
        self._route_service = route_service
    
    def reserve_track_capacity(self, track_id: TrackId, required_length: Length) -> None:
        track = self._track_repository.get_by_id(track_id)
        track.reserve_space(required_length)
        self._track_repository.save(track)
    
    def find_suitable_track(self, track_type: TrackType, required_capacity: Length) -> Optional[Track]:
        available_tracks = self._capacity_service.find_available_tracks(track_type, required_capacity)
        return available_tracks[0] if available_tracks else None
    
    def calculate_route_between_tracks(self, from_track: TrackId, to_track: TrackId) -> Optional[Route]:
        return self._route_service.calculate_shortest_route(from_track, to_track)
        return self._route_service.calculate_shortest_route(from_track, to_track)
```

## Infrastructure Interfaces

#### **TopologyDataProvider**
```python
class TopologyDataProvider(ABC):
    @abstractmethod
    def load_tracks_from_file(self, file_path: str) -> List[Track]:
        pass
    
    @abstractmethod
    def load_nodes_from_file(self, file_path: str) -> List[Node]:
        pass

#### **ExternalTopologyService**
```python
class ExternalTopologyService(ABC):
    @abstractmethod
    def import_from_external_api(self, api_endpoint: str, api_type: str) -> TrackNetwork:
        pass
    
    @abstractmethod
    def sync_topology_updates(self) -> List[TopologyChangeEvent]:
        pass
    
    @abstractmethod
    def validate_external_topology(self, network: TrackNetwork) -> ValidationResult:
        pass
```

#### **TopologyIntegrationService**
```python
class TopologyIntegrationService:
    def __init__(self, 
                 local_provider: TopologyDataProvider,
                 external_service: Optional[ExternalTopologyService] = None):
        self._local_provider = local_provider
        self._external_service = external_service
    
    def load_topology(self, source: TopologySource) -> TrackNetwork:
        if source == TopologySource.LOCAL:
            return self._load_from_local()
        elif source == TopologySource.EXTERNAL and self._external_service:
            return self._load_from_external()
        else:
            raise UnsupportedTopologySourceError()
    
    def sync_with_external_system(self) -> None:
        if self._external_service:
            changes = self._external_service.sync_topology_updates()
            self._apply_topology_changes(changes)
```

## Integration mit Train Operations Context

**Statt Shared Kernel: Customer/Supplier Beziehung**

### **Infrastructure als Supplier:**
```python
class TopologyQueryService:
    """Public Interface für andere Contexts"""
    
    def get_track_info(self, track_id: TrackId) -> TrackInfo:
        """Gibt vereinfachte Track-Informationen zurück"""
        track = self._track_repository.get_by_id(track_id)
        return TrackInfo(
            id=track.id,
            name=track.name,
            length=track.length,
            track_type=track.track_type,
            available_capacity=track.available_capacity()
        )
    
    def find_route(self, from_track: TrackId, to_track: TrackId) -> Optional[RouteInfo]:
        """Gibt vereinfachte Route-Informationen zurück"""
        route = self._route_service.calculate_shortest_route(from_track, to_track)
        if route:
            return RouteInfo(
                path=[str(track_id) for track_id in route.path],
                distance=route.total_distance.meters,
                estimated_time=route.estimated_travel_time
            )
        return None
    
    def get_available_tracks_by_type(self, track_type: str, min_capacity: float) -> List[TrackInfo]:
        """Findet verfügbare Gleise für andere Contexts"""
        tracks = self._capacity_service.find_available_tracks(
            TrackType(track_type), 
            Length(min_capacity)
        )
        return [self._to_track_info(track) for track in tracks]
```

### **Data Transfer Objects (DTOs):**
```python
@dataclass(frozen=True)
class TrackInfo:
    """Vereinfachte Track-Darstellung für andere Contexts"""
    id: str
    name: str
    length: float
    track_type: str
    available_capacity: float

@dataclass(frozen=True)
class RouteInfo:
    """Vereinfachte Route-Darstellung für andere Contexts"""
    path: List[str]
    distance: float
    estimated_time: timedelta
```

### **Vorteile dieser Lösung:**
- **Keine geteilten Entitäten** zwischen Contexts
- **Klare API-Grenzen** über DTOs
- **Unabhängige Entwicklung** möglich
- **Einfache Versionierung** der Schnittstellen
- **Bessere Testbarkeit** durch Mock-Implementierungen

## Externe System Integration

### **Topologie-Quellen:**
```python
class TopologySource(Enum):
    LOCAL = "local"          # Aus Szenario-Dateien
    EXTERNAL = "external"    # Aus externen APIs oder Systemen
    HYBRID = "hybrid"        # Kombination aus beiden
```

### **Integration Strategy:**
1. **MVP**: Nur lokale Dateien (CSV/JSON)
2. **Phase 2**: Integration externer APIs über REST
3. **Phase 3**: Real-time Synchronisation mit externen Systemen

### **Vorteile der Architektur:**
- **Flexibilität**: Verschiedene Datenquellen unterstützt
- **Erweiterbarkeit**: Neue externe Systeme einfach integrierbar
- **Testbarkeit**: Mock-Implementierungen für externe Services
- **Offline-Fähigkeit**: Lokale Daten als Fallback

## Nächste Schritte

1. **DTO-Definitionen** für Context-Grenzen finalisieren
2. **TopologyQueryService** als öffentliche API implementieren
3. **Externe System Adapter** für verschiedene APIs entwickeln
4. **Integration Tests** für verschiedene Topologie-Quellen

**Sollen wir mit dem Resource Management Context fortfahren oder die DTO-Schnittstellen weiter detaillieren?**