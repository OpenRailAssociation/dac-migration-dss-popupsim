# 11. Risks and Technical Debt (MVP)

## 11.1 MVP Risk Overview

### MVP Risk Matrix

```mermaid
graph TB
    subgraph "MVP Risk Assessment"
        subgraph "High Impact"
            HH[High Probability<br/>High Impact]
            LH[Low Probability<br/>High Impact]
        end

        subgraph "Low Impact"
            HL[High Probability<br/>Low Impact]
            LL[Low Probability<br/>Low Impact]
        end
    end

    HH --> |Critical| R1[SimPy integration fails]
    LH --> |Major| R2[Performance bottlenecks]
    HL --> |Minor| R3[Platform compatibility]
    LL --> |Negligible| R4[Output format issues]

    classDef critical fill:#d32f2f,stroke:#b71c1c,color:#fff
    classDef major fill:#ff9800,stroke:#e65100,color:#fff
    classDef minor fill:#ffc107,stroke:#ff8f00,color:#000
    classDef negligible fill:#4caf50,stroke:#2e7d32,color:#fff

    class R1 critical
    class R2 major
    class R3 minor
    class R4 negligible
```

## 11.2 MVP Technical Risks

### Risk 1: SimPy Integration Complexity

| Aspect | Details |
|--------|----------|
| **Description** | Direct SimPy integration could become too complex |
| **Probability** | Medium (40%) |
| **Impact** | High - Simulation doesn't work |
| **Symptoms** | Unexpected SimPy behavior, hard-to-debug processes |

**Mitigation:**
- ✅ **Simple SimPy processes**: Use only basic events
- ✅ **Early prototyping**: Implement SimPy integration first (validated in 3-Länderhack POC)
- ✅ **Documentation**: Document SimPy patterns
- ✅ **Team expertise**: Leverage POC experience from hackathon

### Risk 2: Performance Issues with Larger Scenarios

| Aspect | Details |
|--------|----------|
| **Description** | MVP could become too slow with > 1000 wagons |
| **Probability** | Medium (30%) |
| **Impact** | Medium - Limited scenario size |
| **Symptoms** | Long execution times, high memory usage |

**Mitigation:**
- ✅ **Profiling**: Early performance measurements
- ✅ **Optimization**: Algorithm improvements
- ✅ **Limits**: Define accepted scenario sizes
- ✅ **Monitoring**: Memory/CPU monitoring

### Risk 3: Schedule Overrun

| Aspect | Details |
|--------|----------|
| **Description** | 5-week development time might not be sufficient |
| **Probability** | High (60%) |
| **Impact** | High - MVP goals not achieved |
| **Symptoms** | Milestone delays, unfinished features |

**Mitigation:**
- ✅ **Scope reduction**: Cut additional features if necessary
- ✅ **Parallel development**: Optimize team coordination
- ✅ **Weekly reviews**: Early risk detection
- ✅ **Minimum MVP**: Define absolutely minimal functionality

## 11.3 MVP Technical Debt

### Debt 1: Direct Framework Dependencies

```python
# MVP: Direct SimPy usage (Technical Debt)
import simpy

class WorkshopService:
    def __init__(self):
        self.env = simpy.Environment()  # Direct dependency

    def run_process(self):
        self.env.process(self.retrofit_process())  # Tight coupling

# Future: Abstracted interface
class WorkshopService:
    def __init__(self, simulation_engine: SimulationEnginePort):
        self._sim_engine = simulation_engine  # Dependency injection
```

**Debt Details:**
- **Type**: Architecture debt
- **Priority**: High
- **Effort**: Estimated 2-3 days refactoring (to be validated)
- **Created by**: [ADR MVP-001](09-architecture-decisions.md#adr-mvp-001-simpy-for-discrete-event-simulation) (SimPy decision)
- **Full version solution**: Hexagonal architecture with ports

### Debt 2: Missing Event Architecture

```python
# MVP: Direct service calls (Technical Debt)
class SimulationService:
    def run(self):
        config = self.config_service.load()  # Direct call
        workshop = self.workshop_service.setup(config)  # Direct call
        results = self.workshop_service.run(workshop)  # Direct call

# Future: Event-driven
class SimulationService:
    def run(self):
        self.event_bus.publish(ConfigurationRequested())
        # Asynchronous event handling
```

**Debt Details:**
- **Type**: Integration debt
- **Priority**: Medium
- **Effort**: Estimated 1-2 weeks refactoring (to be validated)
- **Created by**: [ADR MVP-007](09-architecture-decisions.md#adr-mvp-007-direct-method-calls-between-contexts) (Direct calls decision)
- **Full version solution**: Event-driven architecture

### Debt 3: File-Based Persistence

```python
# MVP: File-based storage (Technical Debt)
class ConfigurationService:
    def load_scenario(self, path: str):
        with open(f"{path}/scenario.json") as f:  # Direct file access
            return json.load(f)

# Future: Repository pattern
class ConfigurationService:
    def __init__(self, repo: ConfigurationRepository):
        self._repo = repo  # Abstracted storage

    def load_scenario(self, id: str):
        return self._repo.find_by_id(id)  # Storage-agnostic
```

**Debt Details:**
- **Type**: Persistence debt
- **Priority**: Low
- **Effort**: Estimated 3-5 days refactoring (to be validated)
- **Created by**: [ADR MVP-002](09-architecture-decisions.md#adr-mvp-002-file-based-data-storage) (File storage decision)
- **Full version solution**: Database + Repository pattern

## 11.4 MVP Quality Risks

### Code Quality Risks

```mermaid
graph TB
    subgraph "MVP Quality Risks"
        subgraph "Code Quality"
            Complexity[High complexity<br/>Monolithic functions]
            Coverage[Low test coverage<br/>< 70% coverage]
            Documentation[Missing documentation<br/>Undocumented APIs]
        end

        subgraph "Architecture Quality"
            Coupling[High coupling<br/>Direct dependencies]
            Cohesion[Low cohesion<br/>Mixed responsibilities]
            Flexibility[Low flexibility<br/>Hard to extend]
        end

        subgraph "Maintainability"
            Understanding[Hard to understand<br/>Complex business logic]
            Changes[Hard to change<br/>Ripple effects]
            Testing[Hard to test<br/>Integrated components]
        end
    end

    classDef quality fill:#ff9800,stroke:#e65100
    classDef architecture fill:#2196f3,stroke:#1565c0
    classDef maintainability fill:#9c27b0,stroke:#6a1b9a

    class Complexity,Coverage,Documentation quality
    class Coupling,Cohesion,Flexibility architecture
    class Understanding,Changes,Testing maintainability
```

### Quality Metrics Monitoring

| Metric | MVP Goal | Current Status | Risk |
|--------|----------|----------------|------|
| **Cyclomatic complexity** | < 10 | TBD | Medium |
| **Test coverage** | > 70% | TBD | High |
| **Documentation coverage** | > 80% | TBD | Low |
| **Number of dependencies** | < 10 | 7 | Low |

## 11.5 MVP Migration Risks

### Migration to Full Version

```mermaid
graph TB
    subgraph "Migration Risks"
        subgraph "Architecture Migration"
            LayerToHex[Layered → Hexagonal<br/>Major refactoring]
            DirectToEvent[Direct calls → Events<br/>Integration changes]
            FileToDb[Files → Database<br/>Data migration]
        end

        subgraph "Technology Migration"
            MatplotlibToWeb[Matplotlib → Web UI<br/>Complete rewrite]
            MonolithToServices[Monolith → Services<br/>Deployment changes]
        end

        subgraph "Team Migration"
            SkillGap[Skill gaps<br/>New technologies]
            TimeEstimation[Time estimation<br/>Unknown complexity]
        end
    end

    classDef architecture fill:#e3f2fd
    classDef technology fill:#e8f5e8
    classDef team fill:#fff3e0

    class LayerToHex,DirectToEvent,FileToDb architecture
    class MatplotlibToWeb,MonolithToServices technology
    class SkillGap,TimeEstimation team
```

### Migration Effort Estimation

> **Note:** Effort estimates are preliminary and will be refined during MVP implementation based on actual complexity.

| Migration | Estimated Effort | Risk | Mitigation |
|-----------|-----------------|------|------------|
| **Layered → Hexagonal** | 2-3 weeks | High | Interface preparation |
| **Direct → Event-driven** | 1-2 weeks | Medium | Define event interfaces |
| **Files → Database** | 3-5 days | Low | Repository pattern |
| **Matplotlib → Web** | 4-6 weeks | High | Prepare JSON API |

## 11.6 MVP Risk Mitigation

### Risk Monitoring

```python
# MVP Risk Monitoring
class RiskMonitor:
    def check_performance_risk(self, execution_time: float):
        if execution_time > 60:  # seconds
            logging.warning(f"Performance risk: {execution_time}s execution")

    def check_memory_risk(self, memory_mb: float):
        if memory_mb > 100:  # MB
            logging.warning(f"Memory risk: {memory_mb}MB usage")

    def check_complexity_risk(self, function_lines: int):
        if function_lines > 50:
            logging.warning(f"Complexity risk: {function_lines} lines")
```

### Continuous Risk Assessment

| Week | Risk Review | Actions |
|------|-------------|----------|
| **Week 1** | SimPy integration | Create prototype |
| **Week 2** | Performance tests | Initial benchmarks |
| **Week 3** | Code quality | Refactoring if needed |
| **Week 4** | Migration preparation | Interface preparation |
| **Week 5** | Final review | Document debt |

## 11.7 MVP Debt Repayment

### Debt Prioritization

```mermaid
graph TB
    subgraph "Technical Debt Prioritization"
        subgraph "High Priority"
            HP1[SimPy abstraction<br/>Blocks hexagonal migration]
            HP2[Service interfaces<br/>Blocks event architecture]
        end

        subgraph "Medium Priority"
            MP1[Repository pattern<br/>Blocks database migration]
            MP2[Error handling<br/>Blocks production use]
        end

        subgraph "Low Priority"
            LP1[Code documentation<br/>Maintainability]
            LP2[Test coverage<br/>Quality assurance]
        end
    end

    classDef high fill:#d32f2f,stroke:#b71c1c,color:#fff
    classDef medium fill:#ff9800,stroke:#e65100,color:#fff
    classDef low fill:#4caf50,stroke:#2e7d32,color:#fff

    class HP1,HP2 high
    class MP1,MP2 medium
    class LP1,LP2 low
```

### Debt Repayment Plan

> **Note:** Effort estimates are preliminary and will be refined after MVP completion based on actual codebase complexity.

| Phase | Debt | Estimated Effort | Benefit |
|-------|------|-----------------|----------|
| **Post-MVP** | SimPy abstraction | ~3 days | Hexagonal architecture possible |
| **Pre-Full** | Service interfaces | ~5 days | Event-driven architecture possible |
| **Full-Dev** | Repository pattern | ~3 days | Database integration possible |
| **Production** | Error handling | ~2 days | Production readiness |

---


