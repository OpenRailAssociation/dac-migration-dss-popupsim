# 3. System Scope and Context

## 3.1 Business Context

**PopUpSim's Role in DAC Migration Strategy:**

PopUpSim is a **workshop layout optimization tool** within Europe's 500,000-car DAC retrofit program (2029-2034). The tool helps determine if the migration strategy is feasible by optimizing individual Pop-Up workshop layouts and calculating their throughput capacity.

**Strategic Business Logic:**
1. **Europe must retrofit 500,000 cars** by 2034 using temporary Pop-Up workshop sites
2. **PopUpSim simulates individual workshop layouts** to determine optimal throughput (cars/day)
3. **Strategic planners use results** to calculate: "How many sites with Layout X do we need for 500k cars?"
4. **Layout optimization directly impacts** the feasibility and economics of the entire migration program

**Business Impact Examples:**
- **Layout A**: 30 cars/day → Need 45+ sites across Europe
- **Layout B**: 50 cars/day → Need 27+ sites across Europe
- **Layout C**: 70 cars/day → Need 19+ sites across Europe

```mermaid
C4Context
    title Business Context - PopUpSim in DAC Migration Strategy

    %% Primary Users
    Person(workshop_planner, "Workshop Layout Planner", "DB/SBB/ÖBB engineers optimizing individual Pop-Up site layouts")
    Person(strategic_planner, "Strategic Migration Planner", "Open Rail Association planners determining Europe-wide site requirements")
    Person(operations_manager, "Operations Manager", "Railway company managers evaluating workshop capacity and resource needs")

    %% Central System
    System(popupsim, "PopUpSim", "Workshop layout optimization tool: simulates individual Pop-Up sites to determine optimal throughput")

    %% External Business Systems
    System_Ext(dac_dss, "DAC Migration DSS", "Europe-wide migration coordination system (500k cars, 2029-2034)")
    System_Ext(topology_system, "Railway Topology System", "Track network data provider (future integration)")
    System_Ext(train_mgmt, "Train Management System", "Operational scheduling system (future integration)")

    %% Business Data Sources
    SystemDb_Ext(site_constraints, "Site Constraints", "Physical limitations, regulations, resource availability per country")
    SystemDb(layout_templates, "Layout Templates", "Standardized workshop designs and historical performance data")

    %% Primary Business Relationships
    Rel(workshop_planner, popupsim, "Site-specific constraints, layout variations")
    Rel(strategic_planner, popupsim, "Standardization requirements, throughput targets")
    Rel(operations_manager, popupsim, "Resource planning, capacity validation")

    Rel(popupsim, workshop_planner, "Optimized layouts, bottleneck analysis, throughput estimates")
    Rel(popupsim, strategic_planner, "Site capacity data for Europe-wide planning")
    Rel(popupsim, operations_manager, "Resource utilization, operational feasibility")

    %% Business Data Exchange
    Rel(site_constraints, popupsim, "Physical and regulatory constraints")
    Rel(popupsim, dac_dss, "Site capacity estimates for migration feasibility analysis")
    Rel(popupsim, layout_templates, "Validated layout designs and performance benchmarks")
    Rel(layout_templates, strategic_planner, "Standardized designs for replication")

    %% Future Business Integrations
    Rel(topology_system, popupsim, "Real-time track availability (implementation phase)", "dashed")
    Rel(train_mgmt, popupsim, "Dynamic train scheduling (implementation phase)", "dashed")
```

**Business Value Proposition:**
- **Feasibility Validation**: Determines if 500k car migration is achievable with proposed infrastructure
- **Cost Optimization**: Minimizes number of required Pop-Up sites through layout optimization
- **Risk Mitigation**: Identifies bottlenecks and capacity constraints before site construction
- **Standardization**: Enables reusable workshop designs across European railway companies

### 3.1.1 Communication Partners

| External Entity | Input to PopUpSim | Output from PopUpSim | Business Purpose |
|-----------------|-------------------|----------------------|------------------|
| **Workshop Layout Planner** | Site constraints, layout variations, resource limits | Optimized layouts, throughput estimates, bottleneck analysis | Optimize individual Pop-Up workshop sites for maximum car processing capacity |
| **Strategic Migration Planner** | Standardization requirements, throughput targets | Site capacity data, layout templates, feasibility analysis | Determine total number of Pop-Up sites needed across Europe for 500k car migration |
| **Operations Manager** | Resource availability, operational constraints | Resource utilization reports, operational feasibility assessment | Validate that proposed layouts are operationally viable with available resources |
| **DAC Migration DSS** | - | Aggregated capacity estimates, site requirements | Integrate individual site capacities into Europe-wide migration planning |

### 3.1.2 Data Sources & Outputs

| Entity | Type | Content | Business Purpose |
|--------|------|---------|------------------|
| **Site Constraint Files** | Input | Track topology, physical limitations, regulatory requirements | Define realistic constraints for each Pop-Up workshop location |
| **Workshop Configuration** | Input | Resource capacity, processing times, operating schedules | Model workshop operations and resource availability |
| **Train Schedule Data** | Input | Wagon arrival patterns, service requirements, routing | Simulate realistic workload for capacity planning |
| **Throughput Analysis** | Output | Cars/day capacity, resource utilization, bottleneck identification | Determine optimal layout performance for strategic planning |
| **Layout Comparison Reports** | Output | Side-by-side layout performance, cost-benefit analysis | Support decision-making for standardized workshop designs |
| **Capacity Estimates** | Output | Site-specific throughput data for DAC Migration DSS | Enable Europe-wide migration feasibility assessment |
| **Input File Archive** | Output | Copy of original configuration files with simulation results | Ensure reproducibility and maintain input-output consistency |

### 3.1.3 Future Extensions (Implementation Phase)

| External Entity | Input to PopUpSim | Business Value |
|-----------------|-------------------|----------------|
| **Railway Topology System** | Real-time track availability, maintenance windows | Enable dynamic layout optimization based on actual network conditions |
| **Train Management System** | Live train schedules, dynamic arrivals | Support real-time workshop operations during actual DAC migration |
| **Multi-Site Coordination** | Cross-site capacity sharing, overflow management | Optimize workshop network performance across multiple Pop-Up sites |

## 3.2 Technical Context

```mermaid
C4Context
    title Technical Context - PopUpSim Implementation

    Person(users, "Users", "Web Browsers (Chrome/Firefox/Edge)")

    System_Boundary(popupsim_boundary, "PopUpSim System") {
        Container(web_ui, "Web Interface", "React/Vue.js + Nginx", "Serves UI on port 443, handles static assets")
        Container(api_gateway, "API Gateway", "FastAPI + Uvicorn", "REST endpoints on port 8000, WebSocket support")
        Container(sim_engine, "Simulation Engine", "Python + NumPy/Pandas", "Core simulation logic, multi-threaded processing")
        Container(file_handler, "File Handler", "Python + Pandas", "Configuration parsing, result serialization")
        Container(session_mgmt, "Session Management", "File-based Storage", "Session data, temporary simulation state (future: database)")
    }

    SystemDb_Ext(config_files, "Configuration Files", "JSON/CSV/YAML on Local FS")
    SystemDb(results_storage, "Results Storage", "Local File System + SQLite")

    System_Ext(dac_dss, "DAC Migration DSS", "Future integration (format TBD)")
    System_Ext(topology_api, "Railway Topology API", "Future integration (format TBD)")
    System_Ext(train_mgmt, "Train Management API", "Future integration (format TBD)")

    %% Current Technical Channels
    Rel(users, web_ui, "HTTPS:443", "TLS 1.3, HTTP/2")
    Rel(web_ui, api_gateway, "HTTP:8000/WebSocket", "Internal network")
    Rel(api_gateway, sim_engine, "Internal API", "Process communication")
    Rel(api_gateway, session_mgmt, "File I/O", "Session management")
    Rel(sim_engine, file_handler, "Internal API", "Data processing")
    Rel(file_handler, config_files, "File I/O", "Read operations")
    Rel(file_handler, results_storage, "File I/O + SQL", "Write operations")

    %% Future Technical Channels
    Rel(api_gateway, dac_dss, "REST API:443", "OAuth 2.0 + mTLS (future)", "dashed")
    Rel(topology_api, api_gateway, "GraphQL:443", "OAuth 2.0 + API Keys (future)", "dashed")
    Rel(train_mgmt, api_gateway, "WebSocket:443", "JWT + WSS (future)", "dashed")
```

### 3.2.1 Technical Channels and Transmission Media

**Current Technical Interfaces:**

| Channel | Transmission Media | Protocol/Format | Direction | Description |
|---------|-------------------|-----------------|-----------|-------------|
| **Web Interface** | TCP/IP Network | HTTPS (Port 443) | Bidirectional | User access via web browsers |
| **Configuration Input** | Local File System | File I/O (JSON/CSV/YAML) | Input | Static scenario configuration files (formats under specification) |
| **Results Output** | Local File System | File I/O (JSON/CSV) | Output | Simulation results and exports (formats under specification, future: Parquet for snapshots) |
| **Internal Communication** | Process Memory | HTTP/WebSocket | Internal | API Gateway to Simulation Engine |

**Future Technical Interfaces (To Be Determined):**

| Channel | Transmission Media | Protocol/Format | Direction | Description |
|---------|-------------------|-----------------|-----------|-------------|
| **DAC Integration** | TCP/IP Network | TBD (possibly no integration needed) | Output | Capacity estimates, layout performance data (if required) |
| **Railway Topology** | TCP/IP Network | TBD | Input | Track definitions, constraints, maintenance windows |
| **Train Management** | TCP/IP Network | TBD | Input | Real-time train arrivals, schedule updates |


### 3.2.2 Functional to Technical Mapping

**Current Implementation:**

| Functional Interface | Technical Channel | Transmission Media | Security |
|---------------------|-------------------|-------------------|----------|
| **Web-based Configuration** | Web Browser → HTTP/HTTPS → REST API → Backend | Localhost (127.0.0.1) | Input validation, CSRF protection |
| **File-based Configuration** | Configuration Files → File I/O → File Handler | Local File System | Input validation, schema validation |
| **Results Export** | Simulation Engine → File I/O → Results Storage | Local File System | OS file permissions |
| **Real-time Updates** | Simulation Engine → WebSocket → Web Interface | Localhost (127.0.0.1) | No authentication needed |

**Future Extensions (Technical Details TBD):**

| Functional Interface | Technical Channel | Transmission Media | Security |
|---------------------|-------------------|-------------------|----------|
| External Data Integration | Railway APIs → API Gateway | TCP/IP Network | TBD (authentication method to be determined) |
| Result Sharing | Simulation Engine → DAC Migration DSS | TCP/IP Network | TBD (may not be needed) |
| Dynamic Input | Train Management → Real-time Processing | TCP/IP Network | TBD |

### 3.2.3 Security and Quality Requirements

**Local Deployment Security (Single User):**
- **HTTP/HTTPS** for web interface (TLS optional for local deployment)
- **Localhost binding** (127.0.0.1) to prevent external network access
- **No authentication required** for local single-user access

**Data Protection:**
- **Input validation** with schema validation and file size limits
- **Output sanitization** preventing XSS in web interface
- **File system permissions** using standard OS user permissions
- **No data encryption needed** for local configuration files

**Future External Integration Security:**
- **TLS 1.3** for external API connections (when implemented)
- **Authentication** for external systems (method TBD)
- **Certificate validation** for external API connections

### 3.2.4 Operational Considerations

**Local Application Management:**
- **Error logging** to local files for debugging simulation issues
- **Progress indicators** for long-running simulations
- **Input file archiving** (automatic copy to output folder for reproducibility)

**User Responsibilities:**
- **File management** for configuration and results storage
- **Resource monitoring** using OS task manager (Windows/macOS/Linux)
- **Software updates** through standard installation process
- **Data backup** of important results (if needed - user's choice)

**Future External Integration (When Implemented):**
- **Connection status** for external API availability
- **Error handling** for network connectivity issues

## 3.3 Data Flow Context

### 3.3.1 Input Data Flow

```mermaid
flowchart LR
    subgraph "Input Methods"
        web_ui["Web Interface<br/>• Form-based input<br/>• File upload<br/>• REST API calls"]
        file_system["File System<br/>• Direct file access<br/>• Pre-configured files<br/>• Template loading"]
        external["External Systems<br/>• Future APIs<br/>• Real-time data<br/>• Integration feeds"]
    end

    subgraph "Backend Processing"
        rest_api["REST API<br/>• HTTP endpoints<br/>• JSON payload<br/>• Input validation"]
        file_handler["File Handler<br/>• File I/O operations<br/>• Format detection<br/>• Error handling"]
        validation["Input Validation<br/>• Schema validation (JSON Schema)<br/>• Business rules validation<br/>• Error reporting & graceful shutdown"]
        parsing["Data Parsing<br/>• JSON/CSV processing<br/>• Type conversion & validation<br/>• Error recovery & defaults"]
        persistence["Data Persistence<br/>• Atomic file operations<br/>• Configuration versioning<br/>• Copy input files to output folder"]
    end

    subgraph "Configuration Data Types"
        scenario["Scenario Parameters<br/>• Simulation timeframe<br/>• Random seed<br/>• KPI targets"]
        workshop["Workshop Configuration<br/>• Opening times<br/>• Resource capacity<br/>• Processing times"]
        schedule["Train Schedules<br/>• Arrival times<br/>• Wagon compositions<br/>• Service requirements"]
        routes["Routes<br/>• Prescribed locomotive paths<br/>• Track sequence per route<br/>• Cannot be computed, must be provided"]
        topology["Track Infrastructure<br/>• Individual tracks<br/>• Track properties & constraints<br/>• Workshop placement locations"]
    end

    subgraph "Simulation Pipeline"
        simulation["Simulation Engine<br/>• SimPy discrete event simulation<br/>• Event processing<br/>• Memory-efficient state management"]
        analysis["Analysis Engine<br/>• Statistical processing (NumPy/Pandas)<br/>• KPI aggregation<br/>• Export formatting (JSON/CSV)"]
        input_copy["Input Archiving<br/>• Copy input files to output folder<br/>• Maintain input-output consistency<br/>• Enable result reproducibility"]
    end

    %% Input methods to backend processing
    web_ui --> rest_api
    file_system --> file_handler
    external -.-> rest_api

    %% Backend processing flow
    rest_api --> validation
    file_handler --> validation

    %% Error handling - validation failures stop processing
    validation -->|"Validation Success"| parsing
    validation -->|"Validation Errors"| user_feedback
    
    %% User feedback for errors
    user_feedback["User Feedback<br/>• Error messages<br/>• Validation details<br/>• Graceful shutdown"]
    user_feedback --> web_ui
    user_feedback --> file_system

    parsing --> persistence
    persistence --> input_copy

    %% Backend populates configuration data types
    parsing --> scenario
    parsing --> workshop
    parsing --> schedule
    parsing --> routes
    parsing --> topology

    %% Relationships between configuration data types
    topology --> routes
    routes --> schedule
    topology --> workshop

    %% Configuration data types feed simulation (only after successful validation)
    scenario --> simulation
    workshop --> simulation
    schedule --> simulation
    routes --> simulation
    topology --> simulation
    
    %% Analysis engine gets configuration for output requirements
    scenario --> analysis
    workshop --> analysis

    %% Simulation pipeline (input archiving happens before simulation)
    input_copy --> simulation
    simulation --> analysis

    classDef input fill:#e3f2fd,stroke:#01579b,stroke-width:2px
    classDef backend fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef data fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef process fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class web_ui,file_system,external input
    class rest_api,file_handler,validation,parsing,persistence,user_feedback backend
    class scenario,workshop,schedule,routes,topology data
    class simulation,analysis,input_copy process
```

### 3.3.2 Output Data Flow

During simulation execution, the simulation engine and analysis engine work together to continuously generate result data in memory (both temporal and aggregated data).

```mermaid
flowchart TB
    subgraph "Simulation Execution (From Input Flow)"
        sim_engine["Simulation Engine<br/>• SimPy discrete event simulation<br/>• Generates events during runtime<br/>• Maintains simulation state"]
        analysis_engine["Analysis Engine<br/>• Processes events in real-time<br/>• Calculates KPIs during simulation<br/>• Stores temporal & aggregated data"]
    end

    subgraph "In-Memory Result Data"
        temporal_data["Temporal Data<br/>• Time-series events<br/>• State changes over time<br/>• Individual train movements"]
        aggregated_data["Aggregated Data<br/>• Resource utilization summaries<br/>• Throughput calculations<br/>• Bottleneck analysis"]
    end

    subgraph "Output Processing"
        formatting["Output Formatting<br/>• JSON/CSV export<br/>• Chart data preparation<br/>• Report generation"]
        file_export["File Export<br/>• Write results to disk<br/>• Package with input archive (from input processing)<br/>• Create complete result package"]
    end

    subgraph "Output Types"
        kpis["KPI Reports<br/>• Resource utilization<br/>• Processing times<br/>• Queue lengths<br/>• Throughput (cars/day)"]
        events["Event Logs<br/>• Train arrivals<br/>• Resource assignments<br/>• System events"]
        charts["Visualizations<br/>• Utilization graphs<br/>• Heat maps"]
        summaries["Summaries<br/>• Key findings"]
    end



    subgraph "Delivery Channels"
        web_dashboard["Web Dashboard<br/>• Real-time updates via WebSocket<br/>• Interactive charts<br/>• User interface"]
        file_exports["File Exports<br/>• CSV downloads<br/>• JSON data"]
        rest_api["REST API<br/>• Programmatic access<br/>• Future external integration<br/>• Alternative to file exports"]
        websocket["WebSocket<br/>• Real-time simulation data<br/>• Live progress updates<br/>• Event streaming"]
    end

    subgraph "End Users"
        planners["Workshop Layout Planners<br/>• Layout optimization<br/>• Bottleneck analysis<br/>• Site-specific decisions"]
        analysts["Strategic Migration Planners<br/>• Europe-wide capacity planning<br/>• Site requirement analysis<br/>• Migration feasibility assessment"]
        managers["Operations Managers<br/>• Summaries<br/>• KPI monitoring<br/>• Strategic planning"]
        external_systems["DAC Migration DSS<br/>• Capacity aggregation<br/>• Migration coordination"]
    end

    %% Simulation engines work together during execution
    sim_engine --> analysis_engine

    %% Analysis engine generates result data in memory
    analysis_engine --> temporal_data
    analysis_engine --> aggregated_data

    %% Result data is formatted for output
    temporal_data --> formatting
    aggregated_data --> formatting
    formatting --> file_export

    %% Formatted data becomes output types
    formatting --> kpis
    formatting --> events
    formatting --> charts
    formatting --> summaries

    %% Real-time data flow via WebSocket
    temporal_data --> websocket
    aggregated_data --> websocket
    websocket --> web_dashboard
    
    %% Output types to delivery channels
    kpis --> file_exports
    kpis -.-> rest_api

    events --> file_exports

    charts --> file_exports

    summaries --> file_exports



    %% Delivery channels to end users
    web_dashboard --> planners
    web_dashboard --> analysts

    file_exports --> planners
    file_exports --> analysts
    file_exports --> managers
    
    %% REST API for future programmatic access
    rest_api -.->|"Future Use"| planners
    rest_api -.->|"Future Use"| analysts

    %% Future connections (marked as possibilities)
    rest_api -.->|"Future Integration"| external_systems

    classDef simulation fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef processing fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef output fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef delivery fill:#e3f2fd,stroke:#01579b,stroke-width:2px
    classDef users fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class sim_engine,analysis_engine simulation
    class temporal_data,aggregated_data data
    class formatting,file_export processing
    class kpis,events,charts,summaries output
    class web_dashboard,file_exports,rest_api,websocket delivery
    class planners,analysts,managers,external_systems users
```

## 3.4 Critical Dependencies Analysis

### 3.4.1 Current Critical Dependencies

| Dependency | Criticality | Failure Impact | Mitigation Strategy |
|------------|-------------|----------------|--------------------|
| **Python Runtime (3.13+)** | High | System inoperable | Containerization, version pinning, startup checks |
| **SimPy Library** | High | Simulation engine fails | Version pinning, fallback simulation modes, dependency monitoring |
| **NumPy/Pandas** | High | Analysis engine fails | Version compatibility testing, alternative calculation methods |
| **Web Browser (Modern)** | High | Users cannot access system | Progressive enhancement, browser testing, fallback UI |
| **Operating System (Windows/Linux/macOS)** | High | Cross-platform compatibility issues | OS-specific testing, path abstraction, permission handling |
| **File System Access** | High | Cannot save/load configurations or results | Backup strategies, redundant storage, recovery procedures |
| **File Path Handling** | High | Path separator issues, invalid characters | Cross-platform path libraries (pathlib), input sanitization |
| **Memory (8GB+ RAM)** | Medium | Performance degradation with large simulations | User manually monitors via OS task manager, simulation size warnings in UI |
| **Disk Space (1GB+ free)** | Medium | Cannot save large simulation results | Disk space checks, result compression, cleanup utilities |

### 3.4.2 Future Critical Dependencies (Implementation Phase - TBD)

| Dependency | Criticality | Failure Impact | Mitigation Strategy |
|------------|-------------|----------------|--------------------|
| **DAC Migration DSS** | TBD | TBD (integration may not be needed) | Manual export capabilities, file-based data sharing |
| **Railway Topology API** | TBD | Must use static topology data | Cached topology data, manual configuration updates |
| **Train Management API** | TBD | Cannot simulate dynamic arrivals | Use historical patterns, static scheduling data |

### 3.4.3 Dependency Categories

**Runtime Dependencies:**
- **Core Platform**: Python 3.13+, operating system (Windows/Linux/macOS)
- **Simulation Libraries**: SimPy, NumPy, Pandas
- **User Interface**: Modern web browser, localhost network interface

**System Resources:**
- **File System**: Read/write access, cross-platform path handling
- **Memory**: 8GB+ RAM recommended for large simulations
- **Storage**: 1GB+ free disk space for results

**Future Integration Dependencies:**
- **External APIs**: DAC Migration DSS, Railway Topology API, Train Management API (all TBD)
- **Data Formats**: API specifications and data exchange protocols (to be determined)

*Note: Risk analysis and mitigation strategies for these dependencies are detailed in [Chapter 11 - Risks and Technical Debt](11-technical-risks.md).*

**Navigation:**
[← Architecture and constraints](02-architecture-constraints.md)