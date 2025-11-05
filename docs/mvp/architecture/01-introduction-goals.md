# 1. Introduction and Goals

## 1.1 Task Description

PopUpSim is a microscopic simulation system for optimizing Pop-Up retrofitting sites during the DAC (Digital Automatic Coupling) "Big Bang" migration phase.
The DAC migration involves retrofitting approximately 500,000 freight wagons across Europe (2029-2034) using the "DAC-Ready" method as describen in [[1]](13-bibliography.md). This two-phase approach first pre-equips wagons over 4 years while maintaining screw couplings, then performs rapid final conversion during a critical 3-week "Big Bang" period. PopUpSim focuses specifically on this three week period optimizing temporary Pop-Up workshops that handle the time-critical "Big Bang" conversions without disrupting regular railway operations.

PopUpSim focuses on individual Pop-Up site simulation rather than modeling the entire 500,000 wagon migration. The system uses microscopic modeling to track individual wagons and resources as they move through workshop layouts, enabling iterative testing of different configurations to optimize throughput and identify bottlenecks. This approach supports all migration phases from strategic planning through implementation.

The system consists of three main components working together to provide comprehensive simulation capabilities. The scenario setup component handles infrastructure and parameter configuration, allowing users to define track topology, allocate resources, set timing parameters, and establish operational rules. The simulation engine performs microscopic wagon movement simulation, tracking individual wagons through their journey while managing resource utilization, queue dynamics, and processing workflows. Finally, the analysis and visualization component processes simulation results to generate throughput metrics, utilization statistics, and bottleneck analysis, presenting findings through interactive charts and "film" playback of the simulation process.

PopUpSim is developed as open source software under the Apache 2.0 license [[5]](13-bibliography.md) to ensure transparency and enable cross-company collaboration across the European railway industry. The project is hosted at GitHub [[3]](13-bibliography.md) under the umbrella of the Open Rail Association [[6]](13-bibliography.md), facilitating cooperation between railway companies and supporting the development of a shared solution for the DAC migration challenge. This community-driven approach allows individual railway companies to adapt and extend the system for their specific requirements while contributing improvements back to the broader community. The development builds upon a successful prototype created during the 3-Länderhack 2024 hackathon [[4]](13-bibliography.md), demonstrating the feasibility of the core simulation concepts.

## 1.2 Quality Goals

| Priority | Quality Goal | Scenario | Stakeholder |
|----------|--------------|----------|-------------|
| 1 | **Rapid development** | MVP can be developend in 5 weeks | PopUpSim team |
| 2 | **Simulation Accuracy & Reliability** | Simulation results are accurate and reliable for layout optimization decisions | Strategic Migration Planner, Company Planner |
| 3 | **Usability & Accessibility** | Users can import infrastructure data, configure Pop-Up layouts, and run simulations efficiently | Company Planner, Dispatcher |
| 4 | **Simple installation** | PopUpSim can be easily installed on hardware like laptops | All users |
| 5 | **Testability** | The domain logic is testable | Software Developers |

## 1.3 Stakeholders

| Role | Contact | Expectations |
|------|---------|--------------|
| Strategic Migration Planner | DB Cargo Migration Team | Develop standardized Pop-Up workshop designs, estimate workshop throughput capacity, validate migration strategies |
| Company Planner | Railway Undertakings (e.g. DB, SBB, ÖBB) | Import infrastructure data easily, assess workshop capacity , get clear graphical/tabular output for internal planning |
| Deployment Manager | European Migration Coordination | Validate company plans fit together, monitor implementation progress, ensure Big Bang timeline (2029-2034) is achievable |
| Dispatcher | Pop-Up Workshop Operations | Get recommendations for next wagon assignments, support operational disposition decisions during 3-week Big Bang windows |
| Open Rail Association | Project Governance | Ensure open source transparency, coordinate cross-company collaboration, maintain Apache 2.0 licensing compliance |
| Open Rail Association Members | e.g SNCF, SBB, ÖBB | Possible contacts to other migration teams in other railway companies |
| Software Developers | Open Source Community | Understand system architecture, contribute enhancements, adapt for company-specific DAC migration requirements |
| Skydeck Accelarator | DB Systel GmbH | Demonstatration of results|

> [!NOTE]
> Harmonize with Stakeholder list.

---
## 1.4 MVP Scope

PopUpSim MVP focuses on **4 priority use cases** to validate the simulation approach:

**Strategic Phase:**
- [US-001](../../requirements/use-cases.md#us-001-standardisierte-pop-up-werkstatten-entwickeln): Develop standardized Pop-Up workshops
- [US-002](../../requirements/use-cases.md#us-002-durchsatz-abschatzung-fur-werkstatt-layouts): Estimate throughput for workshop layouts

**Detail Planning Phase:**
- [US-003](../../requirements/use-cases.md#us-003-infrastrukturdaten-importieren): Import infrastructure data
- [US-004](../../requirements/use-cases.md#us-004-kapazitatsabschatzung-fur-geplante-werkstatt): Assess capacity for planned workshop

**Complete requirements:** [requirements/use-cases.md](../../requirements/use-cases.md) (8 use cases total)

**MVP Implementation:**
- File-based configuration (JSON/CSV)
- SimPy discrete event simulation
- CSV export + Matplotlib visualization

**Scope Reductions vs. Full Version:**
The scope is reduced compared to the full version:
- **Use Cases**: 4 priority use cases (vs. 8 total)
- **Architecture**: Simplified context design. (vs. 7 contexts with event-driven architecture)
- **UI**: Matplotlib charts (vs. web interface)
- **Data**: File-based (vs. web interface)
- **Integration**: Direct service calls (vs. event-driven messaging)
- **Deployment**: Desktop only (vs. cloud-ready)


