# Installation Guide

This guide covers different ways to install PopUpSim and its dependencies, including scenarios where you don't have administrative rights.

## Overview

**Good news:** You only need to install **uv** - it will automatically manage Python for you!

uv is a fast Python package manager that can:
- Install and manage Python versions automatically
- Create isolated virtual environments
- Install project dependencies
- Run Python scripts

## Prerequisites

- **uv package manager** - Installation methods covered below
- **Python 3.13+** - uv will install this automatically if needed

## Step 1: Install uv Package Manager

uv is a fast Python package manager. Choose the installation method that works for your system.

### Option 1: PowerShell (Windows - Recommended)
If donwload of uv fails it selbst to deactivate your VPN connection (if you use one).

Open the commandline or a powershel:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
to install uv. If you run in administrative mode the installation of uv is done
system-wide. Otherwise uv will be installed in your user directory (`%USERPROFILE%\.cargo\bin\`).

**Add to PATH (if needed):**

In most cases this is not necessary since uv will automatically adjust the PATH variable.

If `uv` command is not found after installation:

1. Open System Properties → Environment Variables
2. Under "User variables", find or create `Path`
3. Add: `%USERPROFILE%\.cargo\bin`
4. Restart your terminal

### Option 2: Using pipx (Cross-Platform)

**Recommended for users without admin rights.**

First, install pipx if you don't have it:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

Then install uv:

```bash
pipx install uv
```

**Advantages:**
- No admin rights required
- Installs in user directory
- Isolated from system Python
- Works on Windows, Linux, and macOS

### Option 3: Using pip (Cross-Platform)

**Simple but less isolated:**

```bash
pip install --user uv
```

**Note:** This installs uv in your user Python packages directory.

### Option 4: Standalone Installer (Linux/macOS)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This installs uv in `~/.cargo/bin/`.

**Add to PATH (if needed):**

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

Then reload:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Option 5: Manual Download (Windows - No Admin)

1. Download uv from [GitHub releases](https://github.com/astral-sh/uv/releases)
2. Extract to a folder in your user directory (e.g., `C:\Users\YourName\uv\`)
3. Add that folder to your user PATH:
   - Search for "Environment Variables" in Windows
   - Edit "Path" under "User variables"
   - Add your uv folder path
   - Restart terminal

### Verify uv Installation

After installation, verify uv is working:

```bash
uv --version
```

You should see something like `uv 0.x.x`.

## Step 2: Get PopUpSim

### Option A: Using Git (Recommended)

If you have git installed:

```bash
git clone https://github.com/open-rail-association/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim
```

### Option B: Download ZIP (No Git Required)

1. Visit: https://github.com/OpenRailAssociation/dac-migration-dss-popupsim/archive/refs/heads/main.zipp
2. Extract the ZIP file to your desired location
3. Open terminal and navigate to the extracted folder:

```bash
cd dac-migration-dss-popupsim-main
```

## Step 3: Install PopUpSim Dependencies

Navigate to the PopUpSim directory and run:

```bash
uv sync
```

This command:
- **Automatically installs Python 3.13+ if not present** (no manual Python installation needed!)
- Creates a virtual environment
- Installs all required dependencies
- Sets up the project for use

**Note:** This does NOT require administrative rights - everything is installed in the project directory.

## Step 4: Verify Installation

Run a test simulation:

```bash
uv run python popupsim/backend/src/main.py --scenario Data/examples/demo/ --output output/test/
```

If the simulation runs successfully, you're all set!

### Optional: Start the Dashboard

View results in the web-based dashboard (run in a separate terminal):

**Windows:**
```bash
run_dashboard.bat
```

**Linux/macOS:**
```bash
uv run streamlit run popupsim/frontend/streamlit_dashboard.py
```

On the first run it will ask you to enter your E-Mail. Leave empty and just press return/enter.

A browser window (of your default browser) will open and pointing at the adress:
 http://localhost:8501

## Troubleshooting

### "uv: command not found"

**Problem:** uv is not in your PATH.

**Solution:**

**Windows:**
1. Find where uv was installed (usually `%USERPROFILE%\.cargo\bin\`)
2. Add to user PATH environment variable
3. Restart terminal

**Linux/macOS:**
```bash
export PATH="$HOME/.cargo/bin:$PATH"
source ~/.bashrc  # or ~/.zshrc
```

### "Python version too old" or "No Python found"

**Problem:** uv needs to install Python but can't.

**Solution:**

uv will automatically download and install Python 3.13+ when you run `uv sync`. If this fails:

```bash
# Explicitly tell uv to install Python 3.13
uv python install 3.13

# Then run sync
uv sync
```

**Alternative:** If you already have Python installed but it's too old:
```bash
# Use uv's managed Python
uv sync --python 3.13
```

### "Permission denied" during installation

**Problem:** Trying to install in system directories without admin rights.

**Solution:**
- Use `--user` flag with pip: `pip install --user uv`
- Or use pipx (recommended): `pipx install uv`
- Or use PowerShell method (installs in user directory)

### "SSL Certificate Error"

**Problem:** Corporate firewall or proxy blocking downloads.

**Solution:**
1. Contact your IT department for proxy settings
2. Or download files manually and install offline
3. Or use `--trusted-host` flag (not recommended for security)

### uv sync fails with "No Python interpreter found"

**Problem:** uv can't find or install Python.

**Solution:**

```bash
# Let uv install Python 3.13 automatically
uv python install 3.13

# Then sync
uv sync
```

**If you have Python installed manually:**
```bash
# Point uv to your Python installation
uv sync --python python3.13

# Or specify full path
uv sync --python C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe
```

### Virtual environment issues

**Problem:** Conflicts with existing virtual environments.

**Solution:**
1. Delete `.venv` folder in project directory
2. Run `uv sync` again

## Installation for Different Scenarios

### Scenario 1: Corporate Windows PC (No Admin Rights)

```powershell
# Install uv using PowerShell (user install)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Add to PATH if needed
$env:Path += ";$env:USERPROFILE\.cargo\bin"

# Download PopUpSim ZIP
# Extract to C:\Users\YourName\Documents\PopUpSim

# Navigate and install
cd C:\Users\YourName\Documents\PopUpSim
uv sync

# Run test
uv run python popupsim/backend/src/main.py --scenario Data/examples/demo/ --output output/
```

### Scenario 2: Linux Server (No Root Access)

```bash
# Install uv in user directory
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Clone PopUpSim
git clone https://github.com/open-rail-association/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim

# Install dependencies
uv sync

# Run test
uv run python popupsim/backend/src/main.py --scenario Data/examples/demo/ --output output/
```

### Scenario 3: Shared Computer (Multiple Users)

Each user should:

```bash
# Install uv in their own user directory
pipx install uv

# Clone PopUpSim to their home directory
cd ~
git clone https://github.com/open-rail-association/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim

# Install dependencies (creates .venv in project folder)
uv sync

# Run simulations
uv run python popupsim/backend/src/main.py --scenario Data/examples/demo/ --output output/
```

### Scenario 4: Air-Gapped System (No Internet)

1. **On a connected computer:**
   - Download uv installer for your OS from [GitHub releases](https://github.com/astral-sh/uv/releases)
   - Download PopUpSim ZIP from GitHub
   - Download Python 3.13+ standalone installer from [python.org](https://www.python.org/downloads/) (optional - uv can use it)

2. **Transfer files to air-gapped system**

3. **On air-gapped system:**
   - Install uv manually
   - Extract PopUpSim
   - If you have Python installer, install it first
   - Run `uv sync` (uv will use installed Python or you may need to cache dependencies)

## Next Steps

After successful installation:

1. **Run example scenarios** - See [Getting Started](../README.md) for commands
2. **Follow the tutorial** - Start with [Tutorial Overview](README.md)
3. **Create your own scenarios** - Modify example configurations

## Getting Help

If you encounter issues:

1. Check [GitHub Issues](https://github.com/open-rail-association/dac-migration-dss-popupsim/issues)
2. Review [uv documentation](https://docs.astral.sh/uv/)
3. Ask in project discussions

## Summary of Installation Methods

| Method | Admin Required | Best For | Difficulty |
|--------|----------------|----------|------------|
| PowerShell (Windows) | No | Windows users | Easy |
| pipx | No | All platforms, no admin | Easy |
| pip --user | No | Simple install | Easy |
| Standalone installer | No | Linux/macOS | Medium |
| Manual download | No | Restricted environments | Medium |

**Recommendation:** Use pipx for maximum compatibility and isolation, especially if you don't have admin rights.
