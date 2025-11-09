# Music Production Software Manager (MPSM)

> A Python-based CLI tool for automating the management of VST plugins, DAWs, and licenses on Windows 11

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**MPSM** is a comprehensive automation tool designed to scan, organize, relocate, update, and manage 450+ VST plugins, DAWs (FL Studio, Ableton), plugin managers, and licenses with zero clutter and full registry control.

### Key Features

- **System Scanner**: Automatically scans your entire drive for music production files (VST2, VST3, AAX plugins)
- **Smart Organization**: Centralizes everything into a clean, logical folder structure
- **Registry Management**: Automatically fixes broken registry paths after moving files
- **Auto-Updates**: Detects and applies plugin updates from vendor sites
- **License Tracking**: Tracks and verifies licenses (.lic, .key, iLok)
- **Custom Installation**: Enforces custom installation paths for new plugins

## Target Environment

- **Platform**: Windows 11
- **Target Device**: ASUS ROG Zephyrus G14
- **Use Case**: Music production workstation management

## Project Structure

```
C:\MPSM\
├── mpsm.py                      # Main CLI script
├── config.yaml                  # User settings
├── requirements.txt             # Python dependencies
├── modules\
│   ├── scanner.py              # System scanner module
│   ├── registry_manager.py     # Registry updater
│   ├── updater.py              # Version control & updates
│   ├── license_tracker.py      # License tracking
│   └── installer.py            # Custom installer
├── backups\                     # Registry + file backups
├── logs\                        # Scan/update logs
└── data\                        # Exported tables (CSV/Excel)
```

## Target Folder Structure

MPSM enforces the following clean folder structure:

```
C:\MusicProduction\
├── DAWs\
│   ├── FLStudio\
│   └── Ableton\
├── Plugins\
│   ├── VST2\
│   ├── VST3\
│   ├── AAX\
│   └── Managers\
├── Libraries\
├── Licenses\
└── Temp\
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows 11
- Administrator privileges (for registry operations)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/mpsm.git
cd mpsm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize MPSM:
```bash
python mpsm.py init
```

This will create the configuration file and required directories.

## Usage

### Basic Commands

```bash
# Initialize configuration and folders
python mpsm.py init

# Scan your system for music production files
python mpsm.py scan

# Organize files and fix registry paths
python mpsm.py organize

# Check for plugin updates
python mpsm.py update

# Verify all licenses
python mpsm.py license-check

# Install a new plugin with custom path
python mpsm.py install --plugin "Ozone 11" --type vst3

# Run full automation cycle
python mpsm.py run-all
```

### Configuration

Edit `config.yaml` to customize your setup:

```yaml
root_path: C:\MusicProduction
custom_paths:
  vst2: Plugins\VST2
  vst3: Plugins\VST3
  daw_fl: DAWs\FLStudio
  daw_ableton: DAWs\Ableton
auto_update: true
auto_update_time: "02:00"
dry_run: true
backup_enabled: true
```

## Safety Features

- **Dry-run mode**: Simulates all actions without making changes (enabled by default)
- **Automatic Backups**: Creates registry and file backups before modifications
- **Detailed Logging**: All operations logged to `logs/mpsm_YYYYMMDD.log`
- **Rollback Support**: Restore from backup if issues occur

## Roadmap

- [x] Project structure and documentation
- [ ] Scanner module implementation
- [ ] Registry manager implementation
- [ ] License tracker implementation
- [ ] Auto-updater implementation
- [ ] Custom installer implementation
- [ ] Windows Task Scheduler integration
- [ ] PyInstaller packaging for .exe distribution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built for music producers who need a clean, organized, and automated plugin management system.

---

**Status**: 🚧 In Development

For detailed technical specifications, see [COMPREHENSIVE_PLAN.md](COMPREHENSIVE_PLAN.md)
