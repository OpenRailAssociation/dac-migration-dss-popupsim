# 10. MVP Migration Path

## Overview

**Note:** See [Architecture Section 9](../architecture/09-architecture-decisions.md) for architecture decisions.

This document describes the evolution from MVP to full version.

## MVP vs Full Version

| Aspect | MVP | Full Version |
|--------|-----|--------------|
| **Contexts** | 3 simplified | More specialized (TBD) |
| **UI** | CLI only | Web interface |
| **Data** | File-based | Database + Files |
| **Integration** | Direct calls | Event-driven |
| **Deployment** | Desktop | Cloud-ready |
| **Use Cases** | 4 priority | 8 complete |
| **Visualization** | Matplotlib PNG | Interactive web charts |
| **API** | Python only | REST API |

## Migration Phases

### Phase 1: MVP Foundation (5 weeks)
**Goal**: Working prototype with core functionality

**Deliverables**:
- 3 bounded contexts implemented
- File-based configuration
- SimPy simulation engine
- CSV/PNG output
- 4 priority use cases working

**Success Criteria**:
- Simulation runs without errors
- Results are plausible
- Code passes all quality checks

### Phase 2: Context Refinement (TBD)
**Goal**: Split MVP contexts into specialized contexts

**Changes**: To be determined based on MVP learnings

**Possible evolution**:
- Configuration Context → May remain as-is
- Simulation Domain Context → May split into specialized contexts (Infrastructure, Resource Management, Train Operations, Workshop)
- Simulation Control Context → May split into Simulation Control + Analytics

**Effort**: To be estimated after MVP

### Phase 3: Event-Driven Architecture (3-4 weeks)
**Goal**: Replace direct calls with event-driven communication

**Changes**:
- Implement event bus
- Define domain events
- Add event handlers
- Implement saga pattern for complex workflows

**Benefits**:
- Loose coupling between contexts
- Better scalability
- Easier testing
- Audit trail

**Effort**: Estimated 3-4 weeks (to be validated)

### Phase 4: Web Interface (4-6 weeks)
**Goal**: Add web-based UI

**Changes**:
- FastAPI backend
- Vue.js frontend
- REST API endpoints
- Interactive charts (Plotly)
- Real-time updates (WebSockets)

**Effort**: Estimated 4-6 weeks (to be validated)

### Phase 5: Database Integration (2-3 weeks)
**Goal**: Add persistent storage

**Changes**:
- PostgreSQL database
- SQLAlchemy ORM
- Repository pattern
- Migration scripts

**Effort**: Estimated 2-3 weeks (to be validated)

### Phase 6: Cloud Deployment (2-3 weeks)
**Goal**: Enable cloud deployment

**Changes**:
- Docker containers
- Kubernetes manifests
- CI/CD pipelines
- Monitoring and logging

**Effort**: Estimated 2-3 weeks (to be validated)

## Context Evolution

### Configuration Context

**MVP**:
```python
class ConfigurationService:
    def load_scenario_from_file(self, file_path: str) -> ScenarioConfig:
        # Direct file loading
        pass
```

**Full Version**:
```python
class ConfigurationService:
    def __init__(self, repository: ConfigRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus
    
    async def load_scenario(self, scenario_id: str) -> ScenarioConfig:
        # Load from database
        config = await self.repository.get_by_id(scenario_id)
        
        # Publish event
        await self.event_bus.publish(ScenarioLoadedEvent(config))
        
        return config
```

### Simulation Domain Context

**MVP**: Single context with all domain logic

**Full Version**: Split into 4 specialized contexts

```python
# Infrastructure Context
class InfrastructureService:
    async def get_track_topology(self) -> TrackTopology:
        pass

# Resource Management Context
class ResourceService:
    async def allocate_locomotive(self, route: Route) -> Locomotive:
        pass

# Train Operations Context
class TrainOperationsService:
    async def process_train_arrival(self, train: Train) -> None:
        pass

# Workshop Context
class WorkshopService:
    async def start_retrofit(self, wagon: Wagon, track: WorkshopTrack) -> None:
        pass
```

### Simulation Control Context

**MVP**: Orchestration + KPI calculation

**Full Version**: Split into Simulation Control + Analytics

```python
# Simulation Control Context
class SimulationControlService:
    async def start_simulation(self, scenario_id: str) -> SimulationRun:
        pass

# Analytics Context
class AnalyticsService:
    async def calculate_kpis(self, simulation_id: str) -> KPIReport:
        pass
    
    async def generate_insights(self, simulation_id: str) -> list[Insight]:
        pass
```

## Technology Evolution

### Backend

**MVP**:
- Python 3.13+
- SimPy
- Pydantic
- Matplotlib

**Full Version**:
- FastAPI (web framework)
- PostgreSQL (database)
- SQLAlchemy (ORM)
- Celery (async tasks)
- Redis (caching)
- Plotly (interactive charts)

### Frontend

**MVP**: None (CLI only)

**Full Version**:
- Vue.js 3
- TypeScript
- Vite (build tool)
- Pinia (state management)
- Chart.js or Plotly.js

### Infrastructure

**MVP**: Desktop application

**Full Version**:
- Docker
- Kubernetes
- GitHub Actions (CI/CD)
- Prometheus (monitoring)
- Grafana (dashboards)

## API Evolution

### MVP: Python API

```python
from popupsim.application import PopUpSimApplication

app = PopUpSimApplication()
results = app.run_complete_analysis("scenario.json")
```

### Full Version: REST API

```python
# FastAPI endpoints
@app.post("/api/scenarios")
async def create_scenario(scenario: ScenarioCreate) -> Scenario:
    pass

@app.post("/api/simulations")
async def start_simulation(request: SimulationRequest) -> SimulationRun:
    pass

@app.get("/api/simulations/{simulation_id}/results")
async def get_results(simulation_id: str) -> SimulationResults:
    pass
```

## Data Storage Evolution

### MVP: Files

```
config/
├── scenario.json
└── train_schedule.csv

results/
├── summary.csv
├── wagons.csv
└── charts/
```

### Full Version: Database + Files

```sql
-- PostgreSQL schema
CREATE TABLE scenarios (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    config JSONB,
    created_at TIMESTAMP
);

CREATE TABLE simulation_runs (
    id UUID PRIMARY KEY,
    scenario_id UUID REFERENCES scenarios(id),
    status VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE simulation_results (
    id UUID PRIMARY KEY,
    simulation_run_id UUID REFERENCES simulation_runs(id),
    kpis JSONB,
    created_at TIMESTAMP
);
```

## Testing Evolution

### MVP: Unit + Integration Tests

```python
def test_simulation() -> None:
    config = load_config("test_scenario.json")
    results = run_simulation(config)
    assert results.total_wagons_processed > 0
```

### Full Version: Comprehensive Testing

```python
# Unit tests
def test_domain_logic() -> None:
    pass

# Integration tests
async def test_api_endpoint() -> None:
    async with AsyncClient(app=app) as client:
        response = await client.post("/api/scenarios", json=scenario_data)
        assert response.status_code == 201

# E2E tests
async def test_complete_workflow() -> None:
    # Create scenario → Run simulation → Get results
    pass

# Performance tests
def test_simulation_performance() -> None:
    # Benchmark with 1000 wagons
    pass
```

## Deployment Evolution

### MVP: Local Installation

```bash
git clone <repo>
uv sync
uv run python main.py
```

### Full Version: Cloud Deployment

```bash
# Build Docker image
docker build -t popupsim:latest .

# Deploy to Kubernetes
kubectl apply -f k8s/

# Access via URL
https://popupsim.example.com
```

## Migration Checklist

### Phase 2: Context Refinement
- [ ] Define bounded context boundaries
- [ ] Create context interfaces
- [ ] Implement context services
- [ ] Update tests
- [ ] Update documentation

### Phase 3: Event-Driven Architecture
- [ ] Implement event bus
- [ ] Define domain events
- [ ] Create event handlers
- [ ] Add event sourcing (optional)
- [ ] Update integration tests

### Phase 4: Web Interface
- [ ] Design API endpoints
- [ ] Implement FastAPI backend
- [ ] Create Vue.js frontend
- [ ] Add authentication
- [ ] Deploy web application

### Phase 5: Database Integration
- [ ] Design database schema
- [ ] Implement repositories
- [ ] Add migrations
- [ ] Update services
- [ ] Add database tests

### Phase 6: Cloud Deployment
- [ ] Create Dockerfiles
- [ ] Write Kubernetes manifests
- [ ] Setup CI/CD pipelines
- [ ] Configure monitoring
- [ ] Deploy to cloud

## Risk Mitigation

### Technical Risks
- **SimPy Replacement**: Thin adapter pattern allows easy replacement
- **Database Migration**: Repository pattern isolates data access
- **API Changes**: Versioned API endpoints prevent breaking changes

### Business Risks
- **Feature Creep**: Stick to defined phases
- **Timeline Slippage**: Regular checkpoints and adjustments
- **Resource Constraints**: Prioritize critical features

## Success Metrics

### MVP Success
- ✅ 4 use cases working
- ✅ Simulation accuracy validated
- ✅ Code quality standards met
- ✅ Documentation complete

### Full Version Success
- ✅ 8 use cases working
- ✅ Web interface deployed
- ✅ Multi-user support
- ✅ Cloud deployment operational
- ✅ Performance targets met

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: MVP | 5 weeks | None |
| Phase 2: Contexts | 2-3 weeks | Phase 1 |
| Phase 3: Events | 3-4 weeks | Phase 2 |
| Phase 4: Web UI | 4-6 weeks | Phase 3 |
| Phase 5: Database | 2-3 weeks | Phase 4 |
| Phase 6: Cloud | 2-3 weeks | Phase 5 |
| **Total** | **18-24 weeks** | Sequential |

**Note**: All estimates are to be validated during implementation.
