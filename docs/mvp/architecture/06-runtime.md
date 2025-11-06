# 6. Runtime View (MVP)

## 6.1 Runtime Scenario: Develop Standardized Pop-Up Workshop (US-001)

**Use Case:** [US-001](../../requirements/use-cases.md#us-001) - Strategic Migration Planner develops standardized workshop designs

**Goal:** Test different workshop configurations to find optimal standardized design

### Scenario Description

Strategic planner creates multiple workshop configuration variants (2 stations, 4 stations, 6 stations) and runs simulations to compare throughput and identify optimal design.

### Runtime Interaction

```mermaid
sequenceDiagram
    participant Planner as Strategic Planner
    participant CLI as CLI
    participant Config as Configuration Context
    participant Domain as Simulation Domain Context
    participant Control as Simulation Control Context
    participant Files as File System

    Planner->>Files: Create workshop_2stations.json
    Planner->>Files: Create workshop_4stations.json
    Planner->>Files: Create workshop_6stations.json

    loop For each configuration
        Planner->>CLI: python main.py --config workshop_Xstations.json
        CLI->>Config: load_configuration()
        Config->>Files: Read JSON/CSV
        Config->>Config: Validate with Pydantic
        Config-->>CLI: Validated config objects

        CLI->>Domain: setup_domain(config)
        Domain->>Domain: Create stations, tracks, resources
        Domain-->>CLI: Domain ready

        CLI->>Control: run_simulation(domain, 24h)
        Control->>Domain: Start SimPy environment

        loop Simulation time (24h)
            Domain->>Domain: Train arrivals (hourly)
            Domain->>Domain: Wagon processing
            Domain->>Domain: Calculate KPIs (real-time)
        end

        Control->>Control: Aggregate results
        Control->>Files: Write simulation_results_Xstations.csv
        Control->>Files: Write kpi_charts_Xstations.png
        Control-->>CLI: Simulation complete
        CLI-->>Planner: Results available
    end

    Planner->>Files: Compare CSV results
    Planner->>Planner: Select optimal configuration
```

### Key Runtime Aspects

| Aspect | Description | Quality Goal |
|--------|-------------|-------------|
| **Configuration Validation** | Pydantic validates workshop parameters before simulation starts | Reliability |
| **Iterative Testing** | Planner runs multiple configurations sequentially | Usability |
| **Real-time KPI Calculation** | Analysis Engine calculates metrics during simulation | Accuracy |
| **File-based Comparison** | Results exported to CSV for manual comparison | Simplicity |

### Performance Characteristics

> **Note:** Performance metrics will be measured during MVP implementation. Estimates are placeholders for architecture documentation.

---

## 6.2 Runtime Scenario: Estimate Workshop Throughput (US-002)

**Use Case:** [US-002](../../requirements/use-cases.md#us-002) - Strategic planner estimates throughput capacity

**Goal:** Determine maximum wagon throughput for a given workshop layout

### Scenario Description

Strategic planner runs simulation with increasing wagon arrival rates to find throughput limits and identify bottlenecks.

### Runtime Interaction

```mermaid
sequenceDiagram
    participant Planner as Strategic Planner
    participant CLI as CLI
    participant Config as Configuration Context
    participant Domain as Simulation Domain Context
    participant Analysis as Analysis Engine
    participant Control as Simulation Control Context
    participant Files as File System

    Planner->>Files: Create scenario_high_load.json
    Note over Files: 30 wagons/hour arrival rate

    Planner->>CLI: python main.py --config scenario_high_load.json
    CLI->>Config: load_configuration()
    Config-->>CLI: Validated config

    CLI->>Domain: setup_domain(config)
    Domain-->>CLI: Domain ready

    CLI->>Control: run_simulation(domain, 24h)
    Control->>Domain: Start SimPy environment

    loop Every simulation hour
        Domain->>Domain: Train arrives (30 wagons)
        Domain->>Domain: Assign wagons to stations

        alt Station available
            Domain->>Domain: Start retrofit process
            Domain->>Analysis: Record: wagon_processing_started
        else All stations busy
            Domain->>Domain: Add to queue
            Domain->>Analysis: Record: wagon_queued
            Analysis->>Analysis: Calculate queue length
        end

        Domain->>Domain: Complete retrofits
        Domain->>Analysis: Record: wagon_completed
        Analysis->>Analysis: Calculate throughput
        Analysis->>Analysis: Calculate utilization

        alt Queue length > threshold
            Analysis->>Analysis: Flag: bottleneck detected
        end
    end

    Control->>Analysis: Get aggregated KPIs
    Analysis-->>Control: Throughput, utilization, bottlenecks

    Control->>Files: Write throughput_analysis.csv
    Control->>Files: Write bottleneck_chart.png
    Control-->>CLI: Analysis complete

    CLI-->>Planner: Results with bottleneck identification
    Planner->>Files: Review bottleneck_chart.png
    Planner->>Planner: Decide: Add stations or optimize layout
```

### Key Runtime Aspects

| Aspect | Description | Quality Goal |
|--------|-------------|-------------|
| **Real-time Bottleneck Detection** | Analysis Engine identifies bottlenecks during simulation | Accuracy |
| **Queue Monitoring** | Tracks queue length at each station | Reliability |
| **Utilization Tracking** | Calculates station utilization continuously | Accuracy |
| **Threshold-based Alerts** | Flags when queue exceeds acceptable limits | Usability |

### State Transitions: Wagon Processing

```mermaid
stateDiagram-v2
    [*] --> Arrived: Train arrival
    Arrived --> Queued: No station available
    Arrived --> InRetrofit: Station available
    Queued --> InRetrofit: Station becomes available
    InRetrofit --> Completed: Retrofit finished
    Completed --> [*]

    note right of Queued
        Analysis Engine tracks
        queue length here
    end note

    note right of InRetrofit
        Analysis Engine calculates
        utilization here
    end note
```
> **Note:** This needs to be updated since it does not reflect the process correctly.

### Performance Characteristics

> **Note:** Performance metrics will be measured during MVP implementation. Actual timing depends on hardware and simulation complexity.

---

## 6.3 Runtime Scenario: Import Infrastructure Data (US-003)

**Use Case:** [US-003](../../requirements/use-cases.md#us-003) - Company Planner imports existing infrastructure data

**Goal:** Import track topology and workshop layout from existing railway infrastructure data

### Scenario Description

Company planner has existing infrastructure data (track layouts, station locations) in CSV format and wants to import it into PopUpSim for capacity assessment.

### Runtime Interaction

```mermaid
sequenceDiagram
    participant Planner as Company Planner
    participant CLI as CLI
    participant Config as Configuration Context
    participant Parser as CSV Parser
    participant Validator as Pydantic Validator
    participant Files as File System

    Planner->>Files: Prepare infrastructure_topology.csv
    Note over Files: Contains: track_id, length, connections
    Planner->>Files: Prepare workshop_layout.csv
    Note over Files: Contains: station_id, location, capacity

    Planner->>CLI: python main.py --import-infra infrastructure_topology.csv workshop_layout.csv
    CLI->>Config: import_infrastructure()

    Config->>Files: Read infrastructure_topology.csv
    Files-->>Config: CSV data (tracks)
    Config->>Parser: Parse track data
    Parser->>Parser: Convert to Track objects
    Parser-->>Config: Parsed tracks

    Config->>Files: Read workshop_layout.csv
    Files-->>Config: CSV data (workshops)
    Config->>Parser: Parse workshop data
    Parser->>Parser: Convert to Workshop objects
    Parser-->>Config: Parsed workshops

    Config->>Validator: Validate infrastructure consistency
    Validator->>Validator: Check track connections valid
    Validator->>Validator: Check workshop locations on tracks
    Validator->>Validator: Check capacity constraints

    alt Validation successful
        Validator-->>Config: Infrastructure valid
        Config->>Files: Write validated_scenario.json
        Config-->>CLI: Import successful
        CLI-->>Planner: Infrastructure imported, ready for simulation
    else Validation failed
        Validator--xConfig: ValidationError: Invalid track connections
        Config-->>CLI: Import failed with errors
        CLI-->>Planner: Error summary + data issues
    end
```

### Key Runtime Aspects

| Aspect | Description | Quality Goal |
|--------|-------------|-------------|
| **CSV Parsing** | Flexible parsing of company-specific CSV formats | Usability |
| **Data Validation** | Validates infrastructure consistency (track connections, locations) | Reliability |
| **Error Reporting** | Clear feedback on data quality issues | Usability |
| **JSON Export** | Converts imported data to PopUpSim format | Accessibility |

### Data Validation Checks

**Infrastructure Consistency:**
- Track connections form valid network (no orphaned tracks)
- Workshop locations reference existing tracks
- Station capacities are positive integers
- Track lengths are positive values

**Business Rules:**
- At least one workshop station defined
- Track network is connected (no isolated segments)
- Workshop locations don't overlap

### Performance Characteristics

> **Note:** Import performance depends on infrastructure size. Will be measured during MVP implementation.

---

## 6.4 Runtime Scenario: Assess Planned Workshop Capacity (US-004)

**Use Case:** [US-004](../../requirements/use-cases.md#us-004) - Company Planner assesses capacity for planned workshop

**Goal:** Evaluate if planned workshop layout meets company's retrofit capacity requirements

### Scenario Description

Company planner has imported infrastructure data (US-003) and now runs simulation with company-specific wagon schedules to assess if planned workshop meets capacity targets.

### Runtime Interaction

```mermaid
sequenceDiagram
    participant Planner as Company Planner
    participant CLI as CLI
    participant Config as Configuration Context
    participant Domain as Simulation Domain Context
    participant Analysis as Analysis Engine
    participant Control as Simulation Control Context
    participant Files as File System

    Note over Planner: Has imported infrastructure (US-003)

    Planner->>Files: Create company_wagon_schedule.csv
    Note over Files: Company-specific arrival patterns
    Planner->>Files: Update validated_scenario.json
    Note over Files: Add capacity target: 500 wagons/week

    Planner->>CLI: python main.py --config validated_scenario.json --schedule company_wagon_schedule.csv
    CLI->>Config: load_configuration()
    Config->>Files: Read validated_scenario.json
    Config->>Files: Read company_wagon_schedule.csv
    Config-->>CLI: Configuration with capacity target

    CLI->>Domain: setup_domain(config)
    Domain->>Domain: Create imported infrastructure
    Domain->>Domain: Load company wagon schedule
    Domain-->>CLI: Domain ready

    CLI->>Control: run_simulation(domain, 168h)
    Note over Control: 1 week simulation
    Control->>Domain: Start SimPy environment

    loop Every hour (168 hours)
        Domain->>Domain: Process scheduled arrivals
        Domain->>Domain: Wagon processing
        Domain->>Analysis: Record wagon events
        Analysis->>Analysis: Track throughput
    end

    Control->>Analysis: Get capacity
    Analysis->>Analysis: Calculate: actual vs target

    alt Capacity target met
        Analysis-->>Control: Throughput: 520 wagons (target: 500)
        Control->>Files: Write capacity_assessment_PASS.csv
        Control->>Files: Write capacity_chart.png
        Control-->>CLI: Capacity target achieved
        CLI-->>Planner: Workshop layout sufficient
    else Capacity target not met
        Analysis-->>Control: Throughput: 450 wagons (target: 500)
        Control->>Files: Write capacity_assessment_FAIL.csv
        Control->>Files: Write bottleneck_analysis.png
        Control-->>CLI: Capacity target missed
        CLI-->>Planner: Workshop needs optimization
        Planner->>Planner: Review bottlenecks, adjust layout
    end
```

### Key Runtime Aspects

| Aspect | Description | Quality Goal |
|--------|-------------|-------------|
| **Company-Specific Schedules** | Uses actual wagon arrival patterns from company data | Accuracy |
| **Capacity Target Comparison** | Compares simulation results against company requirements | Reliability |
| **Pass/Fail Assessment** | Clear indication if workshop meets capacity needs | Usability |
| **Bottleneck Identification** | Identifies specific constraints when target not met | Accuracy |

### Capacity Assessment Logic

```mermaid
stateDiagram-v2
    [*] --> RunSimulation: Load config + schedule
    RunSimulation --> CalculateCapacity: Simulation complete
    CalculateCapacity --> CompareTarget: Throughput calculated

    CompareTarget --> CapacityMet: Actual >= Target
    CompareTarget --> CapacityMissed: Actual < Target

    CapacityMet --> GenerateReport: PASS
    CapacityMissed --> AnalyzeBottlenecks: FAIL
    AnalyzeBottlenecks --> GenerateReport: With recommendations

    GenerateReport --> [*]

    note right of CompareTarget
        Target from company requirements
        Actual from simulation results
    end note

    note right of AnalyzeBottlenecks
        Identify limiting factors:
        - Station capacity
        - Track congestion
        - Resource availability
    end note
```

### Performance Characteristics

> **Note:**  Performance will be measured during MVP implementation.

---

## 6.5 Error Scenarios

### 6.5.1 Invalid Configuration

**Trigger:** User provides configuration with multiple validation errors

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Config as Configuration Context
    participant Validator as Pydantic Validator
    participant Files as File System

    User->>CLI: python main.py --config invalid.json
    CLI->>Config: load_configuration()
    Config->>Files: Read invalid.json
    Files-->>Config: JSON data

    Config->>Validator: Validate all fields
    Validator->>Validator: Collect all validation errors
    Note over Validator: Does NOT stop at first error
    Validator->>Validator: Check station_count <= 0
    Validator->>Validator: Check workers_per_station > 10
    Validator->>Validator: Check retrofit_time < 0
    Validator-->>Config: ValidationError with 3 errors

    Config->>Config: Format error summary
    Config--xCLI: ValidationError with error list

    CLI->>CLI: Print validation summary:
    Note over CLI: Configuration validation failed (3 errors):<br/>1. station_count must be > 0 (got: -1)<br/>2. workers_per_station must be <= 10 (got: 15)<br/>3. retrofit_time must be > 0 (got: -5)

    CLI-->>User: Complete error summary + example config
    Note over User: User fixes all errors at once
```

**Key Behavior:**
- Pydantic collects ALL validation errors before reporting
- User sees complete list of issues in one summary
- Enables fixing all problems in single iteration

**Recovery:** User corrects all configuration errors based on comprehensive error summary

### 6.5.2 Simulation Failure

**Trigger:** Unexpected error during simulation execution

```mermaid
sequenceDiagram
    participant CLI
    participant Control as Simulation Control Context
    participant Domain as Simulation Domain Context
    participant Files as File System

    CLI->>Control: run_simulation()
    Control->>Domain: Start SimPy
    Domain->>Domain: Processing...
    Domain--xControl: SimulationError: Resource conflict
    Control->>Control: Catch exception
    Control->>Files: Write partial_results.csv
    Control->>Files: Write error_log.json
    Control-->>CLI: Simulation failed (partial results saved)
    CLI-->>CLI: Log error details
```

**Recovery:** Partial results saved for debugging, user can adjust configuration

## 6.6 Performance Considerations

> **Note:** Performance requirements and actual measurements will be determined during MVP implementation. The following aspects will be evaluated:

### Performance Aspects to Measure

| Aspect | Measurement Goal | Rationale |
|--------|------------------|----------|
| **Configuration Loading** | Time to load and validate JSON/CSV files | Affects user experience for iterative testing |
| **Domain Setup** | Time to create simulation entities | Impacts startup time |
| **Simulation Execution** | Time to run 24h simulation with varying wagon counts | Core performance metric |
| **Output Generation** | Time to create CSV files and charts | Affects result availability |

### Scalability Testing Plan

**Test scenarios to evaluate:**
- Small workshop (one Workshop with two retrofit stations, low wagon volume)
- Standard workshop (two workshops with three retrofit stations, medium wagon volume)
- High-load scenario (four workshops with three, high wagon volume)

**Success criteria:**
- Simulation completes without errors
- Results are accurate and reproducible
- User experience is acceptable for iterative testing (see Quality Goal 1: Rapid development)

---


