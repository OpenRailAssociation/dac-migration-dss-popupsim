# CI/CD Pipeline Documentation

## Overview

The PopUp-Sim project uses GitHub Actions for continuous integration and deployment. The pipeline ensures code quality through automated formatting, linting, type checking, and testing.

## Workflow Structure

```mermaid
graph TD
    A[Pull Request/Push to main] --> B[Format Job]
    B --> C[Lint Jobs]
    B --> D[Security Scan]
    B --> E[Test Job]

    C --> F[Ruff Lint]
    C --> G[Pylint]
    C --> H[MyPy]

    D --> I[Syft SBOM]
    I --> J[Grype Scan]
    J --> K[Upload SARIF]

    E --> L[Pytest + Coverage]
    L --> M[Upload Coverage]

    style B fill:#e1f5fe
    style C fill:#f3e5f5
    style D fill:#ffebee
    style E fill:#e8f5e8
    style M fill:#fff3e0
```

## Jobs Description

### 1. Format Job
**Purpose:** Ensures code formatting consistency across the codebase.


**Steps:**
- Checkout code
- Setup uv with Python version
- Install dependencies with `uv sync --locked --all-extras --dev`
- Run `ruff format --check --diff .`

**Output:** Shows formatting differences if any exist

### 2. Lint Jobs (Parallel)
**Purpose:** Code quality analysis through multiple linters.

**Matrix:** 3 linters (ruff, pylint, mypy)

**Dependencies:** Requires format job to pass first

#### Ruff Linting
- **Command:** `uv run ruff check --output-format=github .`
- **Focus:** Code quality, unused imports, simplifications
- **Output:** GitHub annotations on PR lines

#### Pylint
- **Command:** `uv run pylint backend/src/ --output-format=colorized`
- **Focus:** Additional code quality checks
- **Output:** Colorized terminal output

#### MyPy Type Checking
- **Command:** `uv run mypy backend/src/ --show-error-codes`
- **Focus:** Static type analysis
- **Output:** Type errors with specific error codes

### 3. Security Scan Job
**Purpose:** Software Bill of Materials (SBOM) generation and vulnerability scanning.

**Dependencies:** Requires format job to pass first

**Tools:**
- **Syft:** Generates SBOM in SPDX-JSON format
- **Grype:** Scans SBOM for known vulnerabilities

**Steps:**
- Check if dependencies exist in `pyproject.toml`
- Generate SBOM with Syft (if dependencies exist)
- Scan vulnerabilities with Grype
- Upload SARIF results to GitHub Security tab
- Upload security reports as artifacts

**Output:**
- SBOM file (`sbom.spdx.json`)
- Vulnerability report (SARIF format)
- GitHub Security alerts for found vulnerabilities

**Note:** Scan is skipped if no dependencies are present. Vulnerabilities do not fail the build (`fail-build: false`).

### 4. Test Jobs (Parallel)
**Purpose:** Run test suite with coverage reporting.

**Dependencies:** Requires format job to pass first

**Steps:**
- Run `uv run pytest --tb=short`
- Upload coverage to Codecov

## Execution Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GH as GitHub
    participant CI as CI Pipeline
    participant CC as Codecov

    Dev->>GH: Push/PR to main
    GH->>CI: Trigger workflow

    CI->>CI: Format check (2 jobs)

    par Parallel execution after format
        CI->>CI: Lint jobs (3 jobs)
    and
        CI->>CI: Security scan (1 job)
    and
        CI->>CI: Test job (1 job)
    end

    CI->>CC: Upload coverage
    CI->>GH: Report results
    GH->>Dev: Show status + annotations
```

## Configuration Details

### Triggers
- **Pull Requests:** Any PR targeting `main` branch
- **Push Events:** Direct pushes to `main` branch

### Matrix Strategy
- **Total Jobs:** 6 (1 format + 3 lint + 1 security + 1 test)

### Dependencies
- Uses `uv.lock` file for reproducible builds
- All jobs use `--locked` flag for consistent dependency versions

### Caching
- uv cache enabled for faster dependency installation
- Automatic caching of Python packages and uv metadata

## Tools Configuration

### Ruff
- **Format:** 120 char lines, single quotes, tabs
- **Lint:** Focus on bugs, unused code, simplifications
- **Output:** GitHub annotations for PR integration

### Pylint
- **Config:** Uses `pyproject.toml` configuration
- **Target:** `backend/src/` directory only
- **Output:** Colorized for better readability

### MyPy
- **Config:** Strict type checking enabled
- **Target:** `backend/src/` and `backend/tests/`
- **Output:** Error codes for easier debugging

### Pytest
- **Config:** Coverage reporting with 90% threshold
- **Output:** Terminal, HTML, and XML reports
- **Upload:** Coverage data sent to Codecov

## Failure Scenarios

### Format Failures
- **Cause:** Code not properly formatted
- **Solution:** Run `uv run ruff format .` locally
- **Impact:** Blocks all other jobs

### Lint Failures
- **Cause:** Code quality issues, type errors
- **Solution:** Fix issues shown in GitHub annotations
- **Impact:** Independent failures, doesn't block tests

### Security Scan Failures
- **Cause:** Known vulnerabilities in dependencies
- **Solution:** Update vulnerable dependencies or review risk
- **Impact:** Does not fail build, creates GitHub Security alerts

### Test Failures
- **Cause:** Failing tests or coverage below threshold
- **Solution:** Fix tests or improve coverage
- **Impact:** Independent of linting and security jobs

## Local Development

To run the same checks locally:

```bash
# Format check
uv run ruff format --check --diff .

# Linting
uv run ruff check .
uv run pylint popupsim/backend/src/
uv run mypy

# Testing
uv run pytest

# Security scanning (requires Syft and Grype installed)
syft popupsim/backend/src -o spdx-json=sbom.spdx.json
grype sbom:sbom.spdx.json
```

## Performance Optimization

- **Parallel execution:** Lint and test jobs run simultaneously
- **Matrix optimization:** Each linter runs in separate job for better visibility
- **Caching:** uv cache reduces dependency installation time
- **Locked dependencies:** Faster installs, no resolution needed

## Security Scanning Details

### Syft (SBOM Generation)
- **Purpose:** Creates Software Bill of Materials
- **Format:** SPDX-JSON (industry standard)
- **Scope:** Scans `popupsim/backend/src` directory
- **Output:** `sbom.spdx.json` artifact

### Grype (Vulnerability Scanning)
- **Purpose:** Identifies known vulnerabilities in dependencies
- **Input:** SBOM from Syft
- **Database:** CVE and security advisory databases
- **Output:** SARIF format for GitHub Security integration
- **Behavior:** Non-blocking (does not fail build)

### Security Reports
- **GitHub Security Tab:** View vulnerability alerts
- **SARIF Upload:** Integrates with GitHub Advanced Security
- **Artifacts:** SBOM and vulnerability reports downloadable

## Monitoring

- **GitHub Actions tab:** View detailed logs and job status
- **PR annotations:** Inline code quality feedback
- **GitHub Security tab:** Vulnerability alerts and SBOM
- **Codecov dashboard:** Coverage trends and reports
- **Status checks:** Required checks before merge
