# Configuration Context

## Übersicht

Der Configuration Context ist verantwortlich für das Einlesen, Validieren und Verwalten aller Konfigurationsdaten für PopUpSim Szenarien. Er orchestriert den Import von Infrastrukturdaten, Werkstatt-Konfigurationen und Simulationsparametern.

## Fachliche Verantwortlichkeit

### Kernaufgaben
- **Datenimport**: Einlesen von Infrastrukturdaten (CSV, JSON, externe Systeme)
- **Validierung**: Plausibilitätsprüfung und Konsistenz-Checks
- **Konfigurationsmanagement**: Szenario-Templates und Parameter-Sets
- **Export/Import**: Vollständige Szenarien speichern und laden

### User Stories Mapping
- **US-003**: Infrastrukturdaten importieren und Gleisen Funktionen zuweisen
- **US-001**: Standardisierte Pop-Up-Werkstätten entwickeln (Templates)
- **US-004**: Kapazitätsabschätzung für geplante Werkstatt (Validierung)

## Domain Model

### Aggregate: Scenario Configuration

```python
@dataclass
class ScenarioConfiguration:
    """Aggregate Root für komplette Szenario-Konfiguration"""
    id: ScenarioId
    name: str
    description: str
    version: str
    created_at: datetime
    
    # Konfigurationsteile
    infrastructure: InfrastructureConfig
    workshops: WorkshopConfig
    resources: ResourceConfig
    simulation_parameters: SimulationConfig
    
    def validate(self) -> ValidationResult:
        """Vollständige Szenario-Validierung"""
        validator = ScenarioValidator()
        return validator.validate_complete_scenario(self)
    
    def export_template(self) -> ScenarioTemplate:
        """Erstellt wiederverwendbares Template"""
        return ScenarioTemplate.from_configuration(self)

@dataclass
class InfrastructureConfig:
    """Infrastruktur-Konfiguration"""
    tracks: List[TrackConfig]
    nodes: List[NodeConfig]
    connections: List[ConnectionConfig]
    
    def validate_topology(self) -> TopologyValidationResult:
        """Prüft Gleistopologie auf Konsistenz"""
        return TopologyValidator().validate(self.tracks, self.connections)

@dataclass
class TrackConfig:
    """Einzelgleis-Konfiguration"""
    id: str
    name: str
    length: float
    track_type: TrackType  # SAMMELGLEIS, ZUFÜHRUNGSGLEIS, WERKSTATTGLEIS
    capacity: int
    functions: List[TrackFunction]
    
    def assign_function(self, function: TrackFunction) -> None:
        """Weist Gleis eine Funktion zu (US-003)"""
        if function not in self.functions:
            self.functions.append(function)

@dataclass
class WorkshopConfig:
    """Werkstatt-Konfiguration"""
    id: str
    name: str
    stations: List[RetrofitStationConfig]
    capacity: int
    processing_times: ProcessingTimeConfig
    
    def calculate_theoretical_throughput(self) -> ThroughputEstimate:
        """Berechnet theoretischen Durchsatz (US-004)"""
        return ThroughputCalculator().estimate(self)

@dataclass
class ScenarioTemplate:
    """Wiederverwendbare Szenario-Vorlage"""
    template_id: str
    name: str
    category: TemplateCategory  # STANDARD_WORKSHOP, LARGE_CAPACITY, etc.
    parameters: Dict[str, Any]
    
    def instantiate(self, custom_params: Dict[str, Any]) -> ScenarioConfiguration:
        """Erstellt Szenario aus Template"""
        merged_params = {**self.parameters, **custom_params}
        return ScenarioBuilder().build_from_template(self, merged_params)
```

### Value Objects

```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    
    def has_blocking_errors(self) -> bool:
        return any(error.severity == ErrorSeverity.BLOCKING for error in self.errors)

@dataclass(frozen=True)
class ThroughputEstimate:
    wagons_per_hour: float
    wagons_per_day: float
    bottleneck_station: Optional[str]
    confidence_level: float

class TrackType(Enum):
    SAMMELGLEIS = "sammelgleis"
    ZUFÜHRUNGSGLEIS = "zuführungsgleis"
    WERKSTATTGLEIS = "werkstattgleis"
    PARKPLATZ = "parkplatz"

class TrackFunction(Enum):
    ARRIVAL_COLLECTION = "arrival_collection"
    DEPARTURE_COLLECTION = "departure_collection"
    RETROFIT_QUEUE = "retrofit_queue"
    PARKING = "parking"
```

## Domain Services

### Configuration Import Service

```python
class ConfigurationImportService:
    """Domain Service für Datenimport"""
    
    def __init__(self, 
                 file_parser: FileParserPort,
                 validator: ConfigurationValidator):
        self._parser = file_parser
        self._validator = validator
    
    def import_infrastructure_from_file(self, file_path: str, 
                                      file_format: FileFormat) -> InfrastructureConfig:
        """Importiert Infrastrukturdaten aus Datei (US-003)"""
        # 1. Datei parsen
        raw_data = self._parser.parse_file(file_path, file_format)
        
        # 2. Domain Objects erstellen
        tracks = [TrackConfig.from_raw_data(track_data) 
                 for track_data in raw_data.tracks]
        connections = [ConnectionConfig.from_raw_data(conn_data)
                      for conn_data in raw_data.connections]
        
        # 3. Infrastruktur-Config erstellen
        infra_config = InfrastructureConfig(
            tracks=tracks,
            nodes=self._extract_nodes(connections),
            connections=connections
        )
        
        # 4. Validierung
        validation_result = infra_config.validate_topology()
        if validation_result.has_blocking_errors():
            raise InvalidTopologyError(validation_result.errors)
        
        return infra_config
    
    def assign_track_functions(self, 
                             infra_config: InfrastructureConfig,
                             function_assignments: Dict[str, List[TrackFunction]]) -> None:
        """Weist Gleisen Funktionen zu (US-003)"""
        for track_id, functions in function_assignments.items():
            track = infra_config.find_track_by_id(track_id)
            if not track:
                raise TrackNotFoundError(track_id)
            
            for function in functions:
                track.assign_function(function)

class ScenarioTemplateService:
    """Domain Service für Template-Management"""
    
    def create_standard_templates(self) -> List[ScenarioTemplate]:
        """Erstellt standardisierte Werkstatt-Templates (US-001)"""
        templates = []
        
        # Small Workshop Template
        small_workshop = ScenarioTemplate(
            template_id="small_workshop_v1",
            name="Kleine Pop-Up-Werkstatt",
            category=TemplateCategory.SMALL_CAPACITY,
            parameters={
                "workshop_stations": 2,
                "daily_capacity": 50,
                "track_count": 4,
                "processing_time_minutes": 45
            }
        )
        templates.append(small_workshop)
        
        # Large Workshop Template
        large_workshop = ScenarioTemplate(
            template_id="large_workshop_v1",
            name="Große Pop-Up-Werkstatt",
            category=TemplateCategory.LARGE_CAPACITY,
            parameters={
                "workshop_stations": 6,
                "daily_capacity": 200,
                "track_count": 12,
                "processing_time_minutes": 35
            }
        )
        templates.append(large_workshop)
        
        return templates
```

### Configuration Validator

```python
class ConfigurationValidator:
    """Domain Service für Validierung"""
    
    def validate_complete_scenario(self, 
                                 config: ScenarioConfiguration) -> ValidationResult:
        """Vollständige Szenario-Validierung"""
        errors = []
        warnings = []
        
        # Infrastructure Validation
        infra_result = self._validate_infrastructure(config.infrastructure)
        errors.extend(infra_result.errors)
        warnings.extend(infra_result.warnings)
        
        # Workshop Validation
        workshop_result = self._validate_workshops(config.workshops)
        errors.extend(workshop_result.errors)
        warnings.extend(workshop_result.warnings)
        
        # Cross-Context Validation
        cross_result = self._validate_cross_context(config)
        errors.extend(cross_result.errors)
        warnings.extend(cross_result.warnings)
        
        return ValidationResult(
            is_valid=len([e for e in errors if e.severity == ErrorSeverity.BLOCKING]) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_infrastructure(self, 
                               infra: InfrastructureConfig) -> ValidationResult:
        """Infrastruktur-spezifische Validierung"""
        errors = []
        
        # Topology Check
        if not self._is_topology_connected(infra.tracks, infra.connections):
            errors.append(ValidationError(
                code="TOPOLOGY_DISCONNECTED",
                message="Gleistopologie ist nicht vollständig verbunden",
                severity=ErrorSeverity.BLOCKING
            ))
        
        # Capacity Check
        for track in infra.tracks:
            if track.length <= 0:
                errors.append(ValidationError(
                    code="INVALID_TRACK_LENGTH",
                    message=f"Gleis {track.id} hat ungültige Länge: {track.length}",
                    severity=ErrorSeverity.BLOCKING
                ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])
    
    def _validate_cross_context(self, 
                              config: ScenarioConfiguration) -> ValidationResult:
        """Context-übergreifende Validierung"""
        errors = []
        warnings = []
        
        # Workshop-Infrastructure Compatibility
        total_workshop_capacity = sum(w.capacity for w in config.workshops.stations)
        total_track_capacity = sum(t.capacity for t in config.infrastructure.tracks 
                                 if TrackFunction.RETROFIT_QUEUE in t.functions)
        
        if total_workshop_capacity > total_track_capacity * 1.2:
            warnings.append(ValidationWarning(
                code="CAPACITY_MISMATCH",
                message="Werkstattkapazität übersteigt Gleiskapazität um mehr als 20%"
            ))
        
        return ValidationResult(is_valid=True, errors=errors, warnings=warnings)
```

## Application Services

### Scenario Setup Service

```python
class ScenarioSetupService:
    """Application Service für Szenario-Setup"""
    
    def __init__(self,
                 import_service: ConfigurationImportService,
                 template_service: ScenarioTemplateService,
                 scenario_repository: ScenarioRepositoryPort):
        self._import_service = import_service
        self._template_service = template_service
        self._scenarios = scenario_repository
    
    def create_scenario_from_files(self, 
                                 setup_request: ScenarioSetupRequest) -> ScenarioConfiguration:
        """Erstellt Szenario aus Dateien (US-003)"""
        # 1. Infrastructure Import
        infra_config = self._import_service.import_infrastructure_from_file(
            setup_request.infrastructure_file,
            setup_request.file_format
        )
        
        # 2. Function Assignment
        if setup_request.function_assignments:
            self._import_service.assign_track_functions(
                infra_config, 
                setup_request.function_assignments
            )
        
        # 3. Workshop Configuration
        workshop_config = self._create_workshop_config(setup_request.workshop_params)
        
        # 4. Complete Scenario
        scenario = ScenarioConfiguration(
            id=ScenarioId.generate(),
            name=setup_request.scenario_name,
            description=setup_request.description,
            version="1.0",
            created_at=datetime.now(),
            infrastructure=infra_config,
            workshops=workshop_config,
            resources=setup_request.resource_config,
            simulation_parameters=setup_request.sim_params
        )
        
        # 5. Validation
        validation_result = scenario.validate()
        if validation_result.has_blocking_errors():
            raise ScenarioValidationError(validation_result)
        
        # 6. Save
        self._scenarios.save(scenario)
        
        return scenario
    
    def create_scenario_from_template(self, 
                                    template_id: str,
                                    custom_params: Dict[str, Any]) -> ScenarioConfiguration:
        """Erstellt Szenario aus Template (US-001)"""
        template = self._template_service.get_template(template_id)
        scenario = template.instantiate(custom_params)
        
        # Validation & Save
        validation_result = scenario.validate()
        if validation_result.has_blocking_errors():
            raise ScenarioValidationError(validation_result)
        
        self._scenarios.save(scenario)
        return scenario
```

## Ports (Interfaces)

```python
class FileParserPort(ABC):
    """Port für Datei-Parsing"""
    
    @abstractmethod
    def parse_file(self, file_path: str, format: FileFormat) -> RawConfigurationData:
        pass
    
    @abstractmethod
    def supported_formats(self) -> List[FileFormat]:
        pass

class ScenarioRepositoryPort(ABC):
    """Port für Szenario-Persistierung"""
    
    @abstractmethod
    def save(self, scenario: ScenarioConfiguration) -> None:
        pass
    
    @abstractmethod
    def find_by_id(self, scenario_id: ScenarioId) -> Optional[ScenarioConfiguration]:
        pass
    
    @abstractmethod
    def find_templates(self) -> List[ScenarioTemplate]:
        pass
```

## Context Relationships

### Customer/Supplier Relationships
- **Configuration Context** → **Infrastructure Context** (Customer)
- **Configuration Context** → **Workshop Context** (Customer)
- **Configuration Context** → **Resource Management Context** (Customer)

### Shared Kernel
- Gemeinsame Value Objects: `ScenarioId`, `ValidationResult`
- Gemeinsame Enums: `TrackType`, `FileFormat`

### Anti-Corruption Layer
- Externe Datenformate (verschiedene APIs, CSV) werden in Domain Objects übersetzt
- Validierung verhindert inkonsistente Daten in anderen Contexts

## Events

```python
@dataclass
class ScenarioConfigurationCreatedEvent:
    scenario_id: str
    scenario_name: str
    created_by: str
    timestamp: datetime

@dataclass
class InfrastructureImportedEvent:
    scenario_id: str
    track_count: int
    import_source: str
    timestamp: datetime

@dataclass
class ValidationFailedEvent:
    scenario_id: str
    error_count: int
    blocking_errors: List[str]
    timestamp: datetime
```

## Implementation Notes

### File Format Support
- **CSV**: Einfache Track-Listen mit Attributen
- **JSON**: Strukturierte Konfiguration mit Validierung
- **Externe APIs**: Infrastrukturdaten von verschiedenen Quellen
- **Excel**: Für Planer-freundliche Eingabe

### Validation Strategy
- **Syntactic**: Datentypen, Pflichtfelder
- **Semantic**: Geschäftsregeln, Plausibilität
- **Cross-Context**: Konsistenz zwischen Contexts
- **Performance**: Kapazitäts- und Durchsatz-Checks

### Template Categories
- **SMALL_WORKSHOP**: 1-2 Stationen, 20-50 Wagen/Tag
- **MEDIUM_WORKSHOP**: 3-4 Stationen, 50-100 Wagen/Tag  
- **LARGE_WORKSHOP**: 5+ Stationen, 100+ Wagen/Tag
- **SPECIALIZED**: Spezielle Anforderungen (Gefahrgut, etc.)

---

**Referenzen:**
- User Stories: [requirements/use-cases.md](../requirements/use-cases.md)
- Context Map: [context-map.md](../context-map.md)
- File Format Specs: [configuration-management.md](../configuration-management.md)