# MPSM Installation Guide

**Date:** 2025-11-10
**Version:** 1.0.0

---

## Overview

Complete installation guide for MPSM (Music Production Software Manager) - a Python-based CLI tool for automating VST plugin and DAW management on Windows 11.

---

## System Requirements

### Operating System
- **Windows 11** (primary target)
- **Windows 10** (supported)

### Python
- **Python 3.9+** (recommended: 3.11)
- **pip** (Python package installer)

### Disk Space
- Minimum: 100 MB for MPSM + dependencies
- Recommended: 500 MB+ for scan results and backups

### Permissions
- **Administrator rights** (for registry operations)
- **Read/Write access** to scan directories

---

## Installation Methods

### Method 1: User Installation (Recommended)

For end users who want to use MPSM as a tool:

```bash
# 1. Clone or download the repository
git clone https://github.com/abrahamahn/mpsm.git
cd mpsm

# 2. Create virtual environment (recommended)
python -m venv venv

# 3. Activate virtual environment
# On Windows Command Prompt:
venv\Scripts\activate.bat
# On Windows PowerShell:
venv\Scripts\Activate.ps1
# On Git Bash:
source venv/Scripts/activate

# 4. Install MPSM and dependencies
pip install -e .

# 5. Verify installation
mpsm --version
```

### Method 2: Development Installation

For developers who want to contribute or modify MPSM:

```bash
# 1. Clone the repository
git clone https://github.com/abrahamahn/mpsm.git
cd mpsm

# 2. Create virtual environment
python -m venv venv
source venv/Scripts/activate  # or venv\Scripts\activate on Windows

# 3. Install with development dependencies
pip install -e .[dev]

# 4. Verify installation
mpsm --version
pytest --version
black --version
mypy --version
```

### Method 3: Quick Install (Dependencies Only)

If you only want to run from source without installing:

```bash
# 1. Clone repository
git clone https://github.com/abrahamahn/mpsm.git
cd mpsm

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run directly
python mpsm.py --version
```

---

## Post-Installation Setup

### 1. Initialize Configuration

Create your MPSM configuration file:

```bash
# Initialize with default settings
mpsm init

# Or specify a custom path
mpsm init --path "C:\MyConfig"

# Auto-detect common music production paths
mpsm init --auto-detect
```

This creates `config.yaml` with default settings. The file will be created in:
- Current directory (default)
- Specified path (with `--path`)
- Auto-detected based on your system (with `--auto-detect`)

### 2. Review Configuration

Open `config.yaml` in your favorite editor and customize:

```yaml
version: '1.0'

# Root paths for organizing files
paths:
  root: 'C:\MusicProduction'
  vst2: 'Plugins\VST2'
  vst3: 'Plugins\VST3'
  daws: 'DAWs'
  libraries: 'Libraries'
  licenses: 'Licenses'

# Scanning options
scan:
  parallel_workers: 4
  exclude_patterns:
    - 'Windows'
    - 'System32'
    - 'AppData\Local\Temp'

# Registry operations
registry:
  backup_enabled: true
  backup_path: 'backups\registry'

# Logging
logging:
  level: 'INFO'
  file: 'logs\mpsm.log'
```

### 3. Verify Setup

Run the status command to verify your configuration:

```bash
mpsm status
```

This shows:
- ✅ Configuration file path
- ✅ Configured paths
- ✅ System information
- ✅ Installed dependencies

---

## First Scan

### Run Your First Scan

```bash
# Scan with default settings
mpsm scan

# Scan with verbose output
mpsm scan --verbose

# Dry run (don't save results)
mpsm scan --dry-run

# Scan specific paths
mpsm scan --paths "C:\Program Files\VST" "C:\VSTPlugins"
```

### View Results

Scan results are saved to:
- **CSV**: `scan_results.csv`
- **Excel**: `scan_results.xlsx` (if openpyxl installed)
- **Console**: Real-time progress and summary

---

## Troubleshooting

### Common Issues

#### Issue: `pip install` fails

**Solution:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip setuptools wheel

# Then retry
pip install -e .
```

#### Issue: Permission errors during scan

**Solution:**
```bash
# Run as Administrator
# Right-click Command Prompt → "Run as Administrator"
mpsm scan
```

#### Issue: `mpsm` command not found

**Solution 1:** Ensure virtual environment is activated
```bash
# Check if venv is active (you should see (venv) in prompt)
venv\Scripts\activate
```

**Solution 2:** Run directly with Python
```bash
python mpsm.py --version
```

**Solution 3:** Add to PATH (Windows)
```bash
# Add Python Scripts directory to PATH
set PATH=%PATH%;C:\Path\To\venv\Scripts
```

#### Issue: Module import errors

**Solution:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Verify installation
pip list | findstr mpsm
```

#### Issue: Tests fail to run

**Solution:**
```bash
# Install dev dependencies
pip install pytest pytest-cov pytest-mock

# Run tests with verbose output
pytest tests/ -v
```

---

## Updating MPSM

### Update to Latest Version

```bash
# 1. Pull latest changes
git pull origin main

# 2. Reinstall (picks up new dependencies)
pip install -e .

# 3. Verify version
mpsm --version
```

### Update Dependencies Only

```bash
# Update all dependencies
pip install --upgrade -r requirements.txt

# Or update specific package
pip install --upgrade pandas
```

---

## Uninstallation

### Remove MPSM

```bash
# 1. Uninstall package
pip uninstall mpsm

# 2. Deactivate virtual environment
deactivate

# 3. Remove directory (optional)
cd ..
rmdir /s /q mpsm
```

### Clean Uninstall (Everything)

```bash
# 1. Remove all MPSM files
cd mpsm
pip uninstall mpsm -y
deactivate

# 2. Remove virtual environment
rmdir /s /q venv

# 3. Remove user data (optional)
del config.yaml
rmdir /s /q backups
rmdir /s /q logs
rmdir /s /q data
```

---

## Development Setup

### Setting Up Development Environment

```bash
# 1. Clone and install with dev dependencies
git clone https://github.com/abrahamahn/mpsm.git
cd mpsm
python -m venv venv
source venv/Scripts/activate
pip install -e .[dev]

# 2. Install pre-commit hooks (recommended)
pip install pre-commit
pre-commit install

# 3. Run tests to verify setup
pytest tests/ -v

# 4. Check code quality
black --check src/ tests/
mypy src/
pylint src/
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_vendor_registry.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Open coverage report
start htmlcov/index.html  # Windows
```

### Code Formatting

```bash
# Format code with Black
black src/ tests/ mpsm.py

# Check formatting without changes
black --check --diff src/

# Format specific file
black src/core/config.py
```

### Type Checking

```bash
# Run type checker
mypy src/

# Check specific file
mypy src/scanner/base_scanner.py

# Generate type stub files
stubgen -p src -o stubs
```

---

## Virtual Environment Management

### Creating Virtual Environment

```bash
# Create venv
python -m venv venv

# Create with specific Python version
py -3.11 -m venv venv

# Create in custom location
python -m venv C:\MyVenvs\mpsm-venv
```

### Activating/Deactivating

```bash
# Activate
venv\Scripts\activate        # Command Prompt
venv\Scripts\Activate.ps1    # PowerShell
source venv/Scripts/activate # Git Bash

# Deactivate
deactivate
```

### Managing Dependencies

```bash
# List installed packages
pip list

# Show package details
pip show mpsm

# Check outdated packages
pip list --outdated

# Freeze current dependencies
pip freeze > requirements-frozen.txt

# Install from frozen requirements
pip install -r requirements-frozen.txt
```

---

## Next Steps

After successful installation:

1. **Configure paths** - Edit `config.yaml` for your system
2. **Run first scan** - `mpsm scan` to discover plugins
3. **Review results** - Check `scan_results.csv`
4. **Organize files** - `mpsm organize` (use `--dry-run` first!)
5. **Explore features** - `mpsm --help` to see all commands

---

## Getting Help

### Documentation
- **Architecture**: `docs/BASESCANNER_ARCHITECTURE.md`
- **Testing**: `docs/TESTING_SUMMARY.md`
- **Refactoring**: `docs/REFACTORING_SUMMARY.md`
- **Framework**: `docs/FRAMEWORK.md`

### Commands
```bash
# Show all commands
mpsm --help

# Show help for specific command
mpsm scan --help
mpsm organize --help
mpsm registry --help
```

### Support
- **GitHub Issues**: https://github.com/abrahamahn/mpsm/issues
- **Discussions**: https://github.com/abrahamahn/mpsm/discussions

---

## Checklist

Installation complete when all items are checked:

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] MPSM installed (`pip install -e .`)
- [ ] Configuration initialized (`mpsm init`)
- [ ] Config file customized (`config.yaml`)
- [ ] Status verified (`mpsm status`)
- [ ] First scan completed (`mpsm scan`)
- [ ] Results reviewed (`scan_results.csv`)

**Congratulations!** MPSM is ready to manage your music production software.
