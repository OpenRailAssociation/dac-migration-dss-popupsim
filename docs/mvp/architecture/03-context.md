# 3. System Scope and Context (MVP)

## 3.1 Business Context

**PopUpSim MVP's Role:**

PopUpSim MVP is a **proof-of-concept desktop tool** for simulating Pop-Up workshop operations during the DAC migration. The MVP validates the simulation approach with 4 priority use cases before building the full web-based version.

**MVP Business Logic:**
1. **Developers configure scenarios** using JSON/CSV files
2. **MVP simulates retrofit workflow** using SimPy discrete event simulation
3. **Results exported to CSV/PNG** for manual analysis
4. **Validates simulation approach** for full version development

```mermaid
C4Context
    title Business Context - PopUpSim MVP

    Person(developer, "Developer", "Creates scenarios, runs simulations, validates results")
    Person(planner, "Workshop Planner", "Reviews results, provides feedback on simulation logic")

    System(popupsim_mvp, "PopUpSim", "Desktop simulation tool: file-based configuration, SimPy engine, Streamlit dashboard")

    SystemDb_Ext(config_files, "Configuration Files", "JSON/CSV scenario definitions")
    SystemDb(results_files, "Result Files", "CSV data + JSON metrics")

    Rel(developer, config_files, "Creates/edits")
    Rel(developer, popupsim_mvp, "Runs simulation")
    Rel(popupsim_mvp, config_files, "Reads configuration")
    Rel(popupsim_mvp, results_files, "Writes results")
    Rel(developer, results_files, "Analyzes")
    Rel(planner, results_files, "Reviews for validation")
```

### 3.1.1 Communication Partners

| External Entity | Input to MVP | Output from MVP | Business Purpose |
|-----------------|--------------|-----------------|------------------|
| **Developer** | Scenario configurations, test data | Simulation results, KPI data | Develop and validate simulation logic |
| **Workshop Planner** | Requirements, feedback | Result analysis, throughput estimates | Validate simulation accuracy against real-world expectations |
| **Configuration Files** | Scenario definitions, workshop setup, train schedules | - | Define simulation parameters and input data |
| **Result Files** | - | CSV data, JSON metrics, event logs | Store simulation results for analysis (viewed via the Streamlit dashboard) |

## 3.2 Technical Context

```mermaid
C4Context
    title Technical Context - PopUpSim MVP

    Person(users, "Users", "Developers/Planners")

    System_Boundary(mvp_boundary, "PopUpSim") {
        Container(main, "Main Application (CLI)", "Python + Typer", "Entry point (run/optimize), orchestrates simulation")
        Container(config_reader, "Configuration Context", "Python + Pydantic", "Parses and validates JSON/CSV")
        Container(external_trains, "External Trains Context", "Python", "Schedules train arrivals, creates wagons")
        Container(railway, "Railway Infrastructure Context", "Python", "Manages track capacity and occupancy")
        Container(sim_engine, "Retrofit Workflow Context", "Python + SimPy", "Discrete event simulation, coordination, result export")
        Container(dashboard, "Dashboard", "Python + Streamlit + Plotly", "Interactive visualization of results")
    }

    SystemDb_Ext(config_files, "Configuration Files", "JSON/CSV on Local FS")
    SystemDb(results_storage, "Results Storage", "Local File System (CSV/JSON)")

    Rel(users, main, "Executes", "Command line")
    Rel(main, config_reader, "Loads configuration")
    Rel(config_reader, config_files, "File I/O", "Read")
    Rel(main, sim_engine, "Runs simulation")
    Rel(external_trains, sim_engine, "Train arrival events")
    Rel(railway, sim_engine, "Track state")
    Rel(sim_engine, results_storage, "Exports results", "File I/O (Write)")
    Rel(users, dashboard, "Views results")
    Rel(dashboard, results_storage, "Reads results", "File I/O")
```

### 3.2.1 Technical Channels

| Channel | Transmission Media | Protocol/Format | Direction | Description |
|---------|-------------------|-----------------|-----------|-------------|
| **Configuration Input** | Local File System | File I/O (JSON/CSV) | Input | Scenario configuration files |
| **Results Output** | Local File System | File I/O (CSV/JSON) | Output | Simulation results consumed by the dashboard |
| **Internal Communication** | Process Memory | Python function calls | Internal | Direct method invocation between components |

### 3.2.2 Security and Quality Requirements

**Local Deployment Security:**
- **Input validation** with Pydantic schema validation
- **File system permissions** using standard OS user permissions
- **No network access** required (fully offline)

**Operational Considerations:**
- **Error logging** to console and log files
- **Progress indicators** for simulation execution
- **Input file validation** before simulation starts

## 3.3 Data Flow Context

### 3.3.1 Input Data Flow

```mermaid
flowchart LR
    subgraph "Input Sources"
        manual["Manual Files<br/>• JSON editing<br/>• CSV creation"]
        templates["Templates<br/>• Example configs<br/>• Test scenarios"]
    end

    subgraph "Processing"
        validation["Input Validation<br/>• Pydantic schemas<br/>• Business rules"]
        parsing["Data Parsing<br/>• JSON/CSV processing<br/>• Type conversion"]
    end

    subgraph "Configuration Data"
        scenario["Scenario Parameters"]
        workshop["Workshop Configuration"]
        schedule["Train Schedules"]
        routes["Routes"]
        topology["Track Infrastructure"]
    end

    subgraph "Simulation"
        simulation["SimPy Simulation<br/>• Event processing<br/>• State management"]
    end

    manual --> validation
    templates --> validation
    validation --> parsing
    parsing --> scenario
    parsing --> workshop
    parsing --> schedule
    parsing --> routes
    parsing --> topology

    topology --> routes
    routes --> schedule
    topology --> workshop

    scenario --> simulation
    workshop --> simulation
    schedule --> simulation
    routes --> simulation
    topology --> simulation

    classDef input fill:#e3f2fd
    classDef process fill:#fff3e0
    classDef data fill:#f3e5f5
    classDef sim fill:#e8f5e8

    class manual,templates input
    class validation,parsing process
    class scenario,workshop,schedule data
    class simulation sim
```

### 3.3.2 Output Data Flow

```mermaid
flowchart TB
    subgraph "Simulation Execution"
        sim_engine["Simulation Engine<br/>• SimPy event simulation<br/>• Generates events during runtime"]
        analysis_engine["Analysis Engine<br/>• Processes events in real-time<br/>• Calculates KPIs during simulation"]
    end

    subgraph "Output Processing"
        formatting["Output Formatting<br/>• CSV export<br/>• Chart generation"]
    end

    sim_engine --> analysis_engine
    analysis_engine --> formatting

    subgraph "File Output"
        files["Result Files<br/>• CSV (KPIs)<br/>• PNG (Charts)<br/>• JSON (Logs)"]
    end

    formatting --> files

    classDef sim fill:#e8f5e8
    classDef process fill:#fff3e0
    classDef output fill:#f3e5f5

    class sim_engine,analysis_engine sim
    class formatting process
    class files output
```

## 3.4 Critical Dependencies Analysis

### 3.4.1 Current Critical Dependencies

| Dependency | Criticality | Failure Impact | Mitigation Strategy |
|------------|-------------|----------------|--------------------|
| **Python Runtime (3.13+)** | High | System inoperable | Version pinning, startup checks |
| **SimPy Library** | High | Simulation engine fails | Version pinning, dependency monitoring |
| **Configuration Files** | High | Cannot start simulation | Validation, example files, clear error messages |
| **File System Access** | High | Cannot save/load data | Permission checks, error handling |
| **Streamlit / Plotly** | Medium | No interactive dashboard | CSV/JSON output still available |
| **Pandas** | Medium | Slower CSV processing | Native Python CSV fallback |

---


