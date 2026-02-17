# 1. MVP System Overview

## 1.1 MVP Scope and Goals

### Primary Goal
Functional prototype for Pop-Up workshop simulation that **solves real business problems** and serves as foundation for community development.

### MVP User Stories (Priority 1)
- **US-001**: Develop standardized Pop-Up workshops (Templates)
- **US-002**: Estimate throughput for workshop layouts
- **US-003**: Import infrastructure data (CSV/JSON)
- **US-004**: Assess capacity for planned workshop

### Not in MVP Scope
- **US-005-008**: Advanced visualization and real-time features
- **Web UI**: CLI-only, no web interface
- **Database**: File-based configuration only
- **Advanced Security**: Local application without authentication

## 1.2 System Context

**Note:** See [Architecture Section 3](../architecture/03-context.md) for detailed context diagram.

```mermaid
graph TB
    subgraph "PopUpSim MVP System"
        PopUpSim[PopUpSim MVP<br/>Pop-Up Workshop Simulation]
    end

    subgraph "Users"
        Planner[Strategic Planner<br/>Workshop Templates]
        DetailPlanner[Company Planner<br/>Capacity Assessment]
    end

    subgraph "External Systems"
        Files[Configuration Files<br/>JSON, CSV]
        ExtSys[External Systems<br/>Infrastructure Data]
        Results[Result Export<br/>CSV, PNG]
    end

    Planner -->|Creates Templates| PopUpSim
    DetailPlanner -->|Configures Scenarios| PopUpSim

    PopUpSim -->|Loads Configuration| Files
    PopUpSim -->|Imports Infrastructure| ExtSys
    PopUpSim -->|Exports Results| Results

    classDef system fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef user fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class PopUpSim system
    class Planer,Detailplaner user
    class Files,ExtSys,Results external
```

## 1.3 Container Architecture (C4 Level 2)

**Note:** See [Architecture Section 5](../architecture/05-building-blocks.md) for detailed building blocks.

```mermaid
graph TB
    subgraph "PopUpSim MVP - Desktop Application"
        subgraph "Python Application"
            CFG[Configuration Context<br/>File loading & validation<br/>CONTAINER]
            RWF[Retrofit Workflow Context<br/>Core simulation logic<br/>CONTAINER]
            RLY[Railway Infrastructure Context<br/>Track management<br/>CONTAINER]
            EXT[External Trains Context<br/>Train arrivals<br/>CONTAINER]
        end

        subgraph "Data (File System)"
            ConfigFiles[Input Files<br/>JSON/CSV<br/>DATA]
            ResultFiles[Output Files<br/>CSV/PNG<br/>DATA]
        end

        subgraph "External Libraries"
            SimPy[SimPy Framework<br/>EXTERNAL]
            Matplotlib[Matplotlib<br/>EXTERNAL]
            Pydantic[Pydantic<br/>EXTERNAL]
        end
    end

    subgraph "User"
        Developer[Developer<br/>CLI/Editor<br/>PERSON]
    end

    Developer -->|Creates Config| ConfigFiles
    Developer -->|Starts| CFG
    Developer -->|Analyzes| ResultFiles

    CFG -->|Reads| ConfigFiles
    CFG -->|Validates| Pydantic
    CFG -->|Scenario| RWF
    CFG -->|Scenario| RLY
    CFG -->|Scenario| EXT

    RLY <-->|Track state| RWF
    EXT -->|Train arrivals| RWF
    RWF -->|Uses| SimPy
    RWF -->|Uses| Matplotlib
    RWF -->|Writes| ResultFiles

    classDef container fill:#1168bd,stroke:#0b4884,stroke-width:2px,color:#fff
    classDef data fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
    classDef external fill:#999999,stroke:#6b6b6b,stroke-width:2px,color:#fff
    classDef person fill:#08427b,stroke:#052e56,stroke-width:2px,color:#fff

    class CFG,RWF,RLY,EXT container
    class ConfigFiles,ResultFiles data
    class SimPy,Matplotlib,Pydantic external
    class Developer person
```

## 1.4 Technology Stack

**Note:** See [Architecture Section 7.10](../architecture/07-deployment.md#710-technology-stack-summary) for complete stack.

### Core
- **Python 3.13+**: Main language
- **SimPy**: Discrete event simulation
- **Pydantic 2.0+**: Data validation
- **Matplotlib**: Visualization (charts)
- **Pandas**: Data processing (CSV)

### Development
- **uv**: Package manager
- **pytest**: Testing framework
- **Ruff**: Code formatting and linting
- **MyPy**: Type checking
- **Pylint**: Static analysis

### Not in MVP
- ❌ **Web Frontend**: CLI/Desktop only
- ❌ **REST API**: Direct Python calls
- ❌ **Database**: File-based only

## 1.5 Deployment Architecture

**Note:** See [Architecture Section 7](../architecture/07-deployment.md) for detailed deployment view.

```mermaid
graph TB
    subgraph "Developer Laptop"
        subgraph "PopUpSim MVP"
            Python[Python 3.13+<br/>SimPy + Matplotlib]
        end

        subgraph "File System"
            Input[config/<br/>scenario.json<br/>train_schedule.csv]
            Output[results/<br/>*.csv<br/>charts/*.png]
        end

        CLI[Terminal/IDE<br/>python main.py]
    end

    CLI -->|Starts| Python
    Python -->|Reads| Input
    Python -->|Writes| Output
    CLI -->|Opens| Output

    classDef process fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef files fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef user fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class Python process
    class Input,Output files
    class CLI user
```

### Installation Requirements
- **Python 3.13+** with uv
- **RAM**: To be measured during implementation
- **Disk**: ~500MB for installation and data
- **No web browser** required

## 1.6 Quality Attributes MVP

**Note:** See [Architecture Section 1.2](../architecture/01-introduction-goals.md#12-quality-goals) for quality goals.

### Performance Goals
- **Startup Time**: To be measured
- **Simulation Speed**: To be measured
- **Chart Generation**: To be measured
- **Memory Usage**: To be measured

### Functional Goals
- **Determinism**: Identical results with same inputs
- **Accuracy**: Plausible throughput estimates
- **Completeness**: All MVP user stories covered
- **Usability**: Quick scenario setup

### Technical Goals
- **Testability**: High code coverage for domain logic
- **Maintainability**: Clear separation between contexts
- **Extensibility**: Easy to add new features
- **Portability**: Runs on Windows, macOS, Linux

## 1.7 Constraints and Assumptions

**Note:** See [Architecture Section 2](../architecture/02-constraints.md) for detailed constraints.

### Technical Constraints
- **Desktop Application**: No web interface
- **File-based I/O**: No database
- **CLI-based**: No graphical user interface
- **Synchronous Processing**: No async/parallel processing

### Business Constraints
- **Pop-Up Workshops**: Focus on DAC retrofit
- **Microscopic Simulation**: Individual wagons and resources
- **Deterministic**: Reproducible results
- **Planning Tool**: Not for real-time operations

### Assumptions
- **Users**: Developers and technical planners
- **Data Quality**: Correct and complete input data
- **Hardware**: Standard business laptop
- **Network**: No network dependencies
- **Editor**: Users can manually edit JSON/CSV

## 1.8 Risks and Mitigation

**Note:** See [Architecture Section 11](../architecture/11-risks-technical-debt.md) for detailed risks.

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Performance with large scenarios** | Medium | High | Early benchmarking |
| **SimPy learning curve** | High | Medium | Prototyping and documentation |
| **Matplotlib limitations** | Low | Low | Simple 2D charts sufficient |

### Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Incomplete domain model** | Medium | High | Close alignment with domain experts |
| **Unrealistic results** | Medium | High | Validation with real data |
| **User acceptance** | Low | High | Focus on visualization |

## 1.9 Success Criteria

### Technical Metrics
- **Development Time:** 5 weeks
- **Simulation Speed:** To be measured
- **Scalability:** To be measured
- **Portability:** Runs on Windows/Mac/Linux with uv

### Functional Metrics
- **Functionality:** Basic retrofitting simulation works
- **Output:** KPIs are correctly calculated and exported
- **Visualization:** Matplotlib charts display simulation results
- **Extensibility:** Architecture foundation for full version established

### Acceptance Criteria
- ✅ **Template Creation**: Standardized workshop templates can be created
- ✅ **Throughput Estimation**: Plausible throughput calculations
- ✅ **Data Import**: CSV/JSON import works without errors
- ✅ **Capacity Analysis**: Capacity bottlenecks are identified
- ✅ **Stability**: Multiple simulations run consecutively without crashes
- ✅ **Usability**: Developer creates scenario quickly
- ✅ **Expert Validation**: Positive evaluation by domain experts
