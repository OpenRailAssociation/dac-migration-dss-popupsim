# 2. Architecture Constraints (MVP)

## 2.1 Organizational and Business Constraints

| Constraint | Description | MVP Impact |
|------------|-------------|------------|
| **Open Source License** | Apache 2.0 license under Open Rail Association | All code publicly available and transparent |
| **License Compatibility** | All third-party dependencies must be compatible with Apache 2.0 | Limits choice of libraries and frameworks |
| **Development Timeline** | Maximum 5 weeks development time | Simplified 3-context architecture instead of more specialized contexts |
| **Team Size** | 3 backend developers | No frontend developer, file-based UI only |
| **Multi-Company Collaboration** | European railway companies (DB, SBB, ÖBB) might use PopUpSim | Architecture must be adaptable to different requirements |
| **Big Bang Timeline Support** | Must simulate 3-week Big Bang conversion periods | Performance requirements for time-critical operations |
| **Single Site Simulation** | One Pop-Up site with one layout at a time | Architecture focused on single-site efficiency |
| **Microscopic Simulation** | Individual wagons/resources modeling | Cannot use macroscopic or aggregate approaches |
| **Workshop Operations Focus** | Pop-Up workshop operations only | Cannot include general railway operations |
| **Prototype Foundation** | Reuse suitable components from 3-Länderhack 2024 prototype | Leverage proven SimPy approach |

## 2.2 Technical Constraints

| Constraint | Description | MVP Impact |
|------------|-------------|------------|
| **Operating System Support** | Windows, Linux, macOS | Cross-platform Python compatibility |
| **GitHub Repository** | https://github.com/OpenRailAssociation/dac-migration-dss-popupsim | Version control and collaboration platform |
| **Python Backend** | Python 3.13+ for backend development | Backend limited to Python ecosystem |
| **SimPy Framework** | Discrete event simulation engine | Event-driven simulation paradigm required |
| **Deterministic Simulation** | Reproducible results required | Enables reliable testing and layout comparison |
| **File-Based Data** | CSV/JSON input/output only | No database installation required |
| **Matplotlib Visualization** | Charts and graphs output | No web frontend in MVP |
| **No Admin Rights** | Installation without administrator privileges | Lightweight, self-contained architecture |
| **Laptop Hardware** | Must run on standard laptops (4GB RAM minimum) | Memory and computational complexity constraints |
| **Offline Operation** | Core functionality works without internet | Self-contained operation |
| **Simulation Scale** | Must handle up to 1,000 wagons | Memory management and algorithm efficiency |
| **Code Format** | PEP-8 with type hints, Ruff formatting | Python coding standards |
| **Type Checking** | MyPy type checking required | Code quality and maintainability |
| **Testing Framework** | pytest for all tests | Standardized testing approach |
| **Documentation Format** | Markdown for all documentation | Documentation toolchain standard |
| **Architecture Documentation** | Must use arc42 template | Standardized architecture documentation structure |
| **Architecture Decision Records** | Must document significant architectural decisions using ADRs | Maintains decision history and rationale |

---


