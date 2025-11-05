# PopUpSim MVP - Deployment

## Übersicht

Diese Datei beschreibt Installation, Deployment und Betrieb des MVP.

---

## System Requirements

### Minimum Requirements
- **OS:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **Python:** 3.13
- **RAM:** 2 GB
- **Disk:** 500 MB
- **CPU:** 2 Cores

### Recommended Requirements
- **OS:** Windows 11, Linux (Ubuntu 22.04+), macOS 13+
- **Python:** 3.13
- **RAM:** 4 GB
- **Disk:** 1 GB
- **CPU:** 4 Cores

---

## Installation

### 1. Python Installation

#### Windows
```powershell
# Download Python 3.13 von python.org
# Oder via winget:
winget install Python.Python.3.13

# Verify
python --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.13 python3.13-venv python3-pip
python3.13 --version
```

#### macOS
```bash
# Via Homebrew
brew install python@3.13
python3.13 --version
```

---

### 2. uv Installation

#### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Linux/macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Verify
```bash
uv --version
```

---

### 3. Project Setup

```bash
# 1. Clone Repository
git clone https://github.com/your-org/popupsim-mvp.git
cd popupsim-mvp

# 2. Install Dependencies
uv sync

# 3. Activate Virtual Environment
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 4. Verify Installation
uv run pytest
```

---

## Configuration

### Environment Variables

```bash
# .env (optional)
POPUPSIM_LOG_LEVEL=INFO
POPUPSIM_OUTPUT_DIR=results
POPUPSIM_CONFIG_DIR=config
```

### Logging Configuration

```python
# src/logging_config.py
import logging
import os

LOG_LEVEL = os.getenv("POPUPSIM_LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("popupsim.log"),
        logging.StreamHandler()
    ]
)
```

---

## Usage

### Command Line Interface

```bash
# Basic Usage
uv run python src/main.py --config config/examples/small_scenario --output results/

# With Options
uv run python src/main.py \
    --config config/examples/medium_scenario \
    --output results/medium_run_001 \
    --log-level DEBUG \
    --no-charts

# Help
uv run python src/main.py --help
```

### CLI Arguments

```python
# src/main.py
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description="PopUpSim MVP - Werkstatt Simulation"
    )

    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to configuration directory"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Output directory for results (default: results)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart generation"
    )

    return parser.parse_args()
```

---

## Deployment Scenarios

### Scenario 1: Local Development

```bash
# 1. Setup
git clone <repo>
cd popupsim-mvp
uv sync

# 2. Run Tests
uv run pytest

# 3. Run Simulation
uv run python src/main.py --config config/examples/small_scenario --output results/

# 4. View Results
# Windows
start results/charts/throughput.png

# Linux
xdg-open results/charts/throughput.png

# macOS
open results/charts/throughput.png
```

---

### Scenario 2: Batch Processing

```bash
# run_batch.sh
#!/bin/bash

SCENARIOS=("small_scenario" "medium_scenario" "large_scenario")

for scenario in "${SCENARIOS[@]}"; do
    echo "Running $scenario..."
    uv run python src/main.py \
        --config "config/examples/$scenario" \
        --output "results/$scenario/$(date +%Y%m%d_%H%M%S)"
done

echo "All scenarios completed!"
```

**Windows (PowerShell):**
```powershell
# run_batch.ps1
$scenarios = @("small_scenario", "medium_scenario", "large_scenario")

foreach ($scenario in $scenarios) {
    Write-Host "Running $scenario..."
    uv run python src/main.py `
        --config "config/examples/$scenario" `
        --output "results/$scenario/$(Get-Date -Format 'yyyyMMdd_HHmmss')"
}

Write-Host "All scenarios completed!"
```

---

### Scenario 3: Server Deployment

```bash
# 1. Setup auf Server
ssh user@server
git clone <repo>
cd popupsim-mvp
uv sync

# 2. Erstelle Service (systemd)
sudo nano /etc/systemd/system/popupsim.service
```

```ini
[Unit]
Description=PopUpSim Simulation Service
After=network.target

[Service]
Type=simple
User=popupsim
WorkingDirectory=/opt/popupsim-mvp
Environment="PATH=/opt/popupsim-mvp/.venv/bin"
ExecStart=/opt/popupsim-mvp/.venv/bin/python src/main.py --config /etc/popupsim/config --output /var/popupsim/results
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# 3. Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable popupsim
sudo systemctl start popupsim

# 4. Status prüfen
sudo systemctl status popupsim

# 5. Logs anzeigen
sudo journalctl -u popupsim -f
```

---

### Scenario 4: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.13-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY config/ ./config/

# Install dependencies
RUN uv sync --frozen

# Create output directory
RUN mkdir -p /app/results

# Set entrypoint
ENTRYPOINT ["uv", "run", "python", "src/main.py"]
CMD ["--config", "config/examples/small_scenario", "--output", "results"]
```

```bash
# Build
docker build -t popupsim-mvp:latest .

# Run
docker run -v $(pwd)/results:/app/results popupsim-mvp:latest \
    --config config/examples/medium_scenario \
    --output results

# Run with custom config
docker run \
    -v $(pwd)/my_config:/app/my_config \
    -v $(pwd)/results:/app/results \
    popupsim-mvp:latest \
    --config /app/my_config \
    --output /app/results
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  popupsim:
    build: .
    volumes:
      - ./config:/app/config
      - ./results:/app/results
    command: --config config/examples/medium_scenario --output results
    environment:
      - POPUPSIM_LOG_LEVEL=INFO
```

```bash
# Run with docker-compose
docker-compose up
```

---

## Monitoring

### Log Files

```bash
# Application Log
tail -f popupsim.log

# Filter by level
grep "ERROR" popupsim.log
grep "WARNING" popupsim.log

# Last 100 lines
tail -n 100 popupsim.log
```

### Progress Monitoring

```python
# src/simulation/service.py
import logging

logger = logging.getLogger(__name__)

class SimulationService:
    def run(self) -> SimulationResults:
        logger.info("Starting simulation...")
        logger.info(f"Duration: {self.config.duration_hours} hours")
        logger.info(f"Tracks: {len(self.config.workshop.tracks)}")

        # Run simulation
        env.run(until=duration_minutes)

        logger.info(f"Simulation completed. Processed {len(wagons)} wagons")
        logger.info("Calculating KPIs...")

        results = self._collect_results()

        logger.info(f"Throughput: {results.throughput_per_hour:.2f} wagons/hour")
        logger.info(f"Utilization: {results.track_utilization:.2%}")

        return results
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Python Version
```bash
# Error: Python 3.13 required
python --version

# Solution: Install Python 3.13
# Windows: winget install Python.Python.3.13
# Linux: sudo apt install python3.13
# macOS: brew install python@3.13
```

#### Issue 2: uv not found
```bash
# Error: uv: command not found

# Solution: Install uv
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"
```

#### Issue 3: Dependencies not installed
```bash
# Error: ModuleNotFoundError: No module named 'pydantic'

# Solution: Install dependencies
uv sync

# Or reinstall
rm -rf .venv
uv sync
```

#### Issue 4: Configuration file not found
```bash
# Error: FileNotFoundError: config/scenario.json

# Solution: Check path
ls -la config/

# Use absolute path
uv run python src/main.py --config /absolute/path/to/config --output results/
```

#### Issue 5: Permission denied (Linux/macOS)
```bash
# Error: PermissionError: [Errno 13] Permission denied: 'results/'

# Solution: Create directory with correct permissions
mkdir -p results
chmod 755 results

# Or run with sudo (not recommended)
sudo uv run python src/main.py ...
```

#### Issue 6: Out of memory
```bash
# Error: MemoryError

# Solution 1: Reduce scenario size
# Edit config/scenario.json: reduce duration_hours or wagons_per_train

# Solution 2: Increase system memory
# Add swap space (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Performance Tuning

### Configuration Optimization

```json
{
  "duration_hours": 8,
  "workshop": {
    "tracks": [
      {
        "id": "TRACK01",
        "capacity": 5,
        "retrofit_time_min": 30
      }
    ]
  },
  "trains": {
    "arrival_interval_minutes": 60,
    "wagons_per_train": 10
  }
}
```

**Tipps:**
- Kleinere `duration_hours` für schnellere Tests
- Weniger Tracks für einfachere Szenarien
- Größere `arrival_interval_minutes` für weniger Events

### Python Optimization

```bash
# Use PyPy for better performance (optional)
pypy3.11 -m pip install uv
pypy3.11 -m uv sync
pypy3.11 src/main.py --config config/examples/medium_scenario --output results/
```

---

## Backup & Recovery

### Backup Configuration

```bash
# Backup config
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# Backup results
tar -czf results_backup_$(date +%Y%m%d).tar.gz results/
```

### Recovery

```bash
# Restore config
tar -xzf config_backup_20240115.tar.gz

# Restore results
tar -xzf results_backup_20240115.tar.gz
```

---

## Uninstallation

```bash
# 1. Deactivate virtual environment
deactivate

# 2. Remove project directory
cd ..
rm -rf popupsim-mvp

# 3. Remove uv (optional)
# Windows: Remove from PATH
# Linux/macOS: rm ~/.cargo/bin/uv
```

---

## Support

### Documentation
- README.md: Quick Start Guide
- docs/: Detailed Documentation
- examples/: Example Configurations

### Logs
- popupsim.log: Application logs
- results/: Simulation results

### Contact
- GitHub Issues: https://github.com/your-org/popupsim-mvp/issues
- Email: support@example.com

---

**Navigation:** [← Testing Strategy](08-mvp-testing-strategy.md) | [Migration Path →](10-mvp-migration-path.md)
