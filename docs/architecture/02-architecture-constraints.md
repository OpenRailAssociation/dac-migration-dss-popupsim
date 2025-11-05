# 2. Architecture Constraints

## 2.1 Organizational and Political Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Open Source License** | Must use Apache 2.0 license under Open Rail Association | All code must be publicly available and transparent |
| **Multi-Company Collaboration** | Different European railway companies (DB, SBB, ÖBB, etc.) might use PopUpSim | Architecture must be adaptable to different company requirements |
| **DAC Migration DSS Integration** | Might function as separate module within larger DAC Migration DSS | Possible interface and data exchange with parent system |
| **European Regulatory Compliance** | Must comply with European rail regulations and GDPR | Data handling and system transparency requirements |

## 2.2 Business and Domain Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Big Bang Timeline** | Must support simulation of 3-week Big Bang conversion periods (2029-2034) | Performance and scalability requirements for time-critical operations |
| **Single Site Simulation Scope** | Must simulate one Pop-Up site with one layout at a time, supporting easy comparison of different layouts for different sites | Architecture focused on single-site simulation efficiency rather than multi-site concurrent processing |
| **Multi-Phase Support** | Must support Strategic Planning, Detail Planning, and Implementation phases | Architecture must accommodate different usage patterns and data requirements |
| **Real-time Extension Capability** | Must be extensible for real-time data in implementation phase | Architecture must support future real-time data integration |
| **Microscopic Simulation Approach** | Must use microscopic (individual cars/resources) modeling | Cannot use macroscopic or aggregate modeling approaches |
| **Workshop Operations Focus** | Must focus on Pop-Up workshop operations only | Cannot include general railway operations simulation |

## 2.3 General Technical Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Operating System Support** | Must support Windows, Linux, and macOS | Cross-platform compatibility requirements for deployment and development |
| **Multi-Language Support** | Must support internationalization for European railway company planners (e.g. german, english, french) | UI architecture must support localization while keeping code and technical documentation in English |
| **GitHub Repository** | Development must use GitHub repository: https://github.com/OpenRailAssociation/dac-migration-dss-popupsim | Version control and collaboration platform fixed |
| **Prototype Foundation** | Should reuse suitable technologies, code, components, and design from existing PopUpSim prototype from 3-Länderhack 2024 | Leverage proven approaches while maintaining freedom to redesign unsuitable parts |
| **Versioning** | Git with [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) | Commit message format and version control workflow |
| **Documentation Format** | Markdown for all documentation | Documentation toolchain and format standards |
| **Architecture Decision Records** | Must document significant architectural decisions using ADRs | Maintains decision history and rationale for future reference |
| **Code Review Requirement** | All pull requests must be reviewed and approved before merging | Ensures code quality and knowledge sharing across team |
| **Test Coverage Requirement** | Must maintain minimum 90% code coverage for all modules | Comprehensive testing requirements and quality assurance |
| **Dependency Management** | Must use secure dependency management with pinned versions and vulnerability scanning | Restricts dependency selection and update processes |
| **License Compatibility** | All third-party dependencies must be compatible with Apache 2.0 license | Limits choice of libraries and frameworks |
| **Security Standards** | Must follow secure coding practices and vulnerability scanning | Code architecture and development practices constrained by security requirements |
| **OpenSSF Scorecard Compliance** | Must maintain compliance with OpenSSF Scorecard for Open Rail Association project maturity | Development processes, security practices, and project governance must meet OpenSSF standards |
| **Automated Testing Pipeline** | Must run automated tests on all supported platforms (Windows, Linux, macOS) for every pull request | CI/CD pipeline must support cross-platform testing and validation |
| **Automated Static Analysis** | Must run static analysis tools automatically on every pull request | Code quality and security issues detected before merge |
| **Automated Security Scanning** | Must include automated vulnerability scanning for code and dependencies in CI/CD pipeline | Security validation integrated into development workflow |
| **Automated Dependency Checks** | Must automatically scan dependencies for known vulnerabilities and license compatibility | Dependency security and compliance validation |
| **Build Automation** | Must support automated builds and packaging for all target platforms | Consistent and reproducible build processes |
| **Deployment Automation** | Must support automated deployment to staging and production environments | Streamlined release process and reduced manual errors |

## 2.4 Backend Development Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Backend Technology** | Uses Python for backend development (proven in 3-Länderhack prototype) | Backend architecture, libraries, and frameworks limited to Python ecosystem |
| **Code Format** | PEP-8 with 120 characters per line | Python coding standards |
| **Type Hints** | MyPy type checking required | Code quality and maintainability standards |
| **Backend Documentation** | Must use NumPy-style docstrings for all Python functions and classes | Standardized API documentation and code readability |
| **Backend Testing Framework** | Must use pytest for Python backend testing | Standardized testing approach and toolchain |
| **Backend Static Analysis** | Must use MyPy, Pylint, and Ruff with security rules for Python code | Automated code quality, type checking, and security vulnerability detection |
| **Simulation Engine** | Must use SimPy for discrete event simulation (subject to evaluation and potential replacement) | Discrete event simulation framework for workshop operations modeling |
| **Deterministic Simulation** | Must produce deterministic and reproducible results (user requirements may add stochastic elements later) | Enables reliable testing, debugging, and layout comparison with consistent results |
| **Event-Driven Architecture** | Must use event-driven simulation paradigm for workshop operations (SimPy handles event scheduling, state management, and time progression) | Domain models must be designed as SimPy processes and resources with generator functions |

## 2.5 Frontend Development Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Browser Compatibility** | Must support all widely used browsers (Chrome, Firefox, Safari, Edge) | Frontend technology choices must ensure broad browser compatibility |
| **Frontend Testing Framework** | Frontend testing framework to be determined based on chosen technology | Testing strategy depends on frontend technology selection |
| **Accessibility Compliance** | Must meet basic web accessibility standards for European users | WCAG compliance requirements for public sector usage |
| **MVP-Level UI Acceptable** | Initial version can have basic UI focused on functionality over polish | Prioritize core features over advanced UI/UX design |
| **Visualization Requirements** | Must provide "film" playback and statistical charts for results | Specific visualization components and rendering capabilities |
| **Limited Initial User Base** | Designed for experienced technical users initially | Can assume technical competence, less focus on beginner-friendly design |

## 2.6 Deployment Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Local Laptop Deployment** | Must run efficiently on standard laptops without manual installation of additonal dependencies | Architecture must be lightweight and self-contained |
| **No Admin Rights Required** | Installation and operation must not require administrator privileges | Limits system-level integrations and installation methods |
| **Future Cloud Deployment** | Architecture must support future migration to cloud platforms | Design must be cloud-ready with containerization support |
| **Container Support** | Future support Docker containerization for consistent deployment | Architecture must be containerizable with proper separation of concerns |
| **Simple Installation** | Installation process must be straightforward for non-technical users | Packaging and distribution strategy constraints |

## 2.7 Performance and Scalability Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Simulation Scale** | Must handle approximately 10,000 wagons in a single simulation | Memory management and algorithm efficiency requirements |
| **Interactive Response Time** | UI interactions must respond in reasonable time for a good user experience | Real-time processing and caching strategy requirements |
| **Laptop Hardware Limitations** | Must run on typical business laptops (8GB RAM, standard CPU) | Memory usage and computational complexity constraints |
| **Iterative Testing Support** | Must support multiple simulation runs for layout comparison | Efficient simulation reset and parameter adjustment capabilities |

## 2.8 Data and Integration Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Initial File-Based Data** | The MVP must support CSV/JSON file input for configuration (formats under specification) | Simple file parsing and validation requirements |
| **Future API Integration** | Architecture must support future REST API data sources | Extensible data layer design with abstraction |
| **Cross-Company Data Privacy** | Data handling must respect company confidentiality requirements | Data isolation and anonymization capabilities might become necessary|
| **No External Dependencies** | Core functionality must work offline without internet connectivity | Self-contained operation with optional online features |
| **Data Format Evolution** | Must support schema evolution without breaking existing configurations | Backward compatibility and migration strategy requirements |




---

**Navigation:** [← Introduction and goals](01-introduction-and-goals.md) | [System scope and context →](03-system-scope-and-context.md)