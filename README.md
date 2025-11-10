# MPSM - Music Production Software Manager

[![CI Status](https://github.com/abrahamahn/mpsm/workflows/CI/badge.svg)](https://github.com/abrahamahn/mpsm/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Automate scanning, organizing, and managing 450+ VST plugins, DAWs, and music production software on Windows 11**

---

## Overview

**MPSM** is a comprehensive Python-based CLI tool designed for music producers who need to manage large plugin collections. It automates the tedious tasks of:

- 🔍 **Scanning** your entire system for VST2, VST3, AAX plugins and DAWs
- 📊 **Cataloging** plugins with metadata extraction (version, publisher, format)
- 📁 **Organizing** files into a clean, centralized folder structure
- 🔧 **Updating** Windows registry paths after moving files
- 🎫 **Tracking** licenses and activations (iLok, proprietary)
- 📈 **Exporting** results to CSV/Excel for analysis

**Target Platform:** Windows 11 (primary), Windows 10 (supported)

---

## Features

### Core Functionality

| Feature | Status | Description |
|---------|--------|-------------|
| **Plugin Scanner** | ✅ Production | Scans VST2 (.dll), VST3 (.vst3), AAX plugins across all drives |
| **Metadata Extraction** | ✅ Production | Extracts version, publisher, format from PE headers |
| **Vendor Detection** | ✅ Production | Identifies 50+ major vendors (Native Instruments, Waves, etc.) |
| **Registry Management** | ✅ Production | Backs up, updates, validates Windows registry entries |
| **License Tracking** | ✅ Production | Scans and validates .lic, .key, iLok activations |
| **File Organization** | ✅ Beta | Centralizes plugins to custom directory structure |
| **CI/CD & Testing** | ✅ Production | 96 automated tests, GitHub Actions workflows |

### Advanced Features

- **Parallel Scanning**: Multi-threaded file system traversal
- **Type-Safe Architecture**: Generic base classes with Python type hints
- **Centralized Vendor Data**: YAML-based vendor registry (50+ vendors)
- **Comprehensive Testing**: 96 tests (90 passing, 6 documented bugs)
- **Modular Design**: Clean separation of CLI, core, scanners, models

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/abrahamahn/mpsm.git
cd mpsm

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows

# Install MPSM
pip install -e .

# Verify installation
mpsm --version
```

**Detailed instructions:** See [INSTALLATION.md](docs/INSTALLATION.md)

### Basic Usage

```bash
# Initialize configuration
mpsm init --auto-detect

# Scan your system
mpsm scan

# View results
type scan_results.csv  # Windows

# Organize files (dry run first!)
mpsm organize --dry-run

# Registry backup
mpsm registry backup

# Check licenses
mpsm license scan
```

---

## Project Structure

```
mpsm/
├── mpsm.py                     # Main CLI entry point (180 lines, 87% reduction)
├── config.yaml                 # User configuration (generated)
├── src/
│   ├── cli/                    # CLI command handlers
│   │   ├── scan_command.py     # Plugin/DAW scanning
│   │   ├── organize_command.py # File organization
│   │   ├── registry_commands.py # Windows registry management
│   │   └── license_commands.py # License tracking
│   ├── core/                   # Core utilities
│   │   ├── config.py           # Configuration management
│   │   ├── logger.py           # Logging setup
│   │   └── exceptions.py       # Custom exceptions
│   ├── scanner/                # Scanning infrastructure
│   │   ├── base_scanner.py     # Abstract base class (type-safe)
│   │   ├── folder_scanner.py   # Data folder scanner
│   │   ├── application_scanner.py # Plugin/DAW scanner
│   │   └── metadata/           # Metadata extraction
│   │       ├── extractor.py    # Main metadata extractor
│   │       ├── pe_parser.py    # PE header parsing
│   │       ├── vst_detector.py # VST signature detection
│   │       └── publisher_identifier.py # Publisher detection
│   ├── data/                   # Data files
│   │   └── vendor_registry.py  # Centralized vendor database (50+)
│   ├── models/                 # Data models
│   │   ├── plugin.py           # Plugin model
│   │   ├── application.py      # Application model
│   │   ├── folder.py           # Data folder model
│   │   └── license.py          # License model
│   ├── registry/               # Windows registry operations
│   ├── license/                # License management
│   └── organizer/              # File organization
├── tests/                      # Test suite (96 tests)
│   ├── unit/                   # Unit tests (52 tests)
│   ├── integration/            # Integration tests (14 tests)
│   └── conftest.py             # Shared test fixtures
├── docs/                       # Documentation
│   ├── INSTALLATION.md         # Installation guide
│   ├── BASESCANNER_ARCHITECTURE.md # Scanner architecture
│   ├── TESTING_SUMMARY.md      # Testing documentation
│   ├── REFACTORING_SUMMARY.md  # Refactoring history
│   └── FRAMEWORK.md            # Framework design
├── .github/workflows/          # CI/CD
│   ├── ci.yml                  # Main CI workflow
│   └── test-pr.yml             # Pull request tests
├── setup.py                    # Package setup (pip install)
├── pyproject.toml              # Modern Python project config
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

---

## Documentation

### User Manual (`docs/manual/`)
- **[Installation Guide](docs/manual/INSTALLATION.md)** - Complete setup instructions
- **[Configuration](docs/manual/CUSTOM_PATHS.md)** - Customizing scan paths
- **[Metadata Extraction](docs/manual/METADATA_EXTRACTION_GUIDE.md)** - How metadata works
- **[VST Protocol](docs/manual/JUCE_VST_HOST_PROTOCOL.md)** - Technical reference

### Developer Documentation (`docs/dev/`)
- **[Architecture](docs/dev/BASESCANNER_ARCHITECTURE.md)** - Scanner design patterns
- **[Framework](docs/dev/FRAMEWORK.md)** - Overall system design
- **[Testing](docs/dev/TESTING_SUMMARY.md)** - Test infrastructure (96 tests)
- **[Refactoring History](docs/dev/REFACTORING_SUMMARY.md)** - Code evolution
- **[Scalability](docs/dev/SCALABILITY_ANALYSIS.md)** - Performance analysis
- **[Improvements](docs/dev/IMPROVEMENTS.md)** - Roadmap and ideas

### Community
- **[Contributing](CONTRIBUTING.md)** - How to contribute
- **[Code of Conduct](CODE_OF_CONDUCT.md)** - Community standards
- **[Security](SECURITY.md)** - Security policy
- **[Changelog](CHANGELOG.md)** - Version history

---

## Development

### Setup Development Environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/abrahamahn/mpsm.git
cd mpsm
python -m venv venv
venv\Scripts\activate
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src --cov-report=html
start htmlcov/index.html

# Format code
black src/ tests/ mpsm.py

# Type check
mypy src/ --ignore-missing-imports

# Lint
pylint src/
```

### Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_vendor_registry.py -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing
```

**Current Test Status:**
- ✅ 90 tests passing
- ⚠️ 6 tests skipped (documented scanner bugs)
- 📊 Coverage: 13% overall, 92% on VendorRegistry, 74% on BaseScanner

---

## Architecture Highlights

### BaseScanner Pattern
MPSM uses an **Abstract Base Class with Generics** for type-safe scanner implementations:

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class BaseScanner(ABC, Generic[T]):
    """Type-safe scanner base class."""

    def __init__(self, config, max_workers):
        self.items: List[T] = []

    @abstractmethod
    def _get_default_scan_paths(self) -> List[str]:
        """Return default paths to scan."""
        pass

    @abstractmethod
    def _identify_item(self, path: Path) -> Optional[T]:
        """Identify and create item from path."""
        pass
```

**Benefits:**
- ✅ **110 lines of duplicate code eliminated**
- ✅ **Type safety** with Python generics
- ✅ **Consistent behavior** across all scanners
- ✅ **Easy extensibility** (implement 2 methods, inherit everything else)

**Details:** [BASESCANNER_ARCHITECTURE.md](docs/BASESCANNER_ARCHITECTURE.md)

### Centralized Vendor Registry
50+ music software vendors in YAML format:

```yaml
native_instruments:
  name: "Native Instruments"
  patterns:
    - "Native Instruments"
    - "NI Audio"
  folder_names:
    - "Native Instruments"
    - "NI"
  daw_executables: []
```

**Coverage:** Native Instruments, Waves, iZotope, FabFilter, Arturia, Spectrasonics, and 45+ more

---

## Testing Infrastructure

### Test Suite (96 Tests)

| Category | Tests | Status | Coverage |
|----------|-------|--------|----------|
| **VendorRegistry** | 21 | ✅ Passing | 92% |
| **Config** | 14 | ✅ Passing | 58% |
| **Publisher ID** | 17 | ✅ Passing | 100% |
| **Scanner Integration** | 14 | ✅ Passing | 74% BaseScanner |
| **FolderScanner** | 30 | 24 ✅, 6 ⚠️ | 73% |

**Total:** 90 passing, 6 skipped (documented bugs)

### CI/CD Workflows

**GitHub Actions:**
- ✅ **CI** - Runs on every push to main/develop/claude/** branches
- ✅ **PR Tests** - Quick tests + integration tests on pull requests
- ✅ **Code Quality** - Black, MyPy, Pylint checks
- ✅ **Coverage Upload** - Codecov integration

**Test on 3 Python versions:** 3.9, 3.10, 3.11

---

## Roadmap

### Phase 1: Foundation ✅ **COMPLETED**
- [x] Scanner infrastructure (BaseScanner pattern)
- [x] Vendor registry centralization
- [x] Config externalization
- [x] Testing infrastructure (96 tests)
- [x] CI/CD setup (GitHub Actions)

### Phase 2: Current Work 🚧
- [ ] Fix documented scanner bugs (FolderType enum, DataFolder model)
- [ ] Increase scanner test coverage to 75%+
- [ ] Add ApplicationScanner unit tests
- [ ] Performance optimization (large directories)

### Phase 3: Features (Next)
- [ ] Auto-update plugin versions
- [ ] Enhanced iLok integration
- [ ] Cloud storage support
- [ ] GUI (PyQt/Tkinter)

### Phase 4: Polish
- [ ] 80%+ overall test coverage
- [ ] Performance benchmarks
- [ ] Windows installer (.exe)
- [ ] Documentation website

---

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) (coming soon).

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/`)
5. Format code (`black src/ tests/`)
6. Commit (`git commit -m 'Add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines
- Follow Black code style (100 char line length)
- Write tests for new features
- Update documentation
- Ensure all CI checks pass

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

### Getting Help
- 📖 **Documentation**: [docs/](docs/)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/abrahamahn/mpsm/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/abrahamahn/mpsm/discussions)

### Author
**Abraham Ahn**
- GitHub: [@abrahamahn](https://github.com/abrahamahn)

---

## Acknowledgments

- **pefile** - PE file format parsing
- **Click** - Command-line interface framework
- **Rich** - Terminal formatting and tables
- **pytest** - Testing framework

---

## Statistics

**Project Metrics:**
- **Lines of Code**: 4,535 (excluding tests)
- **Test Lines**: 1,464
- **Test Coverage**: 13% overall, 92% on critical modules
- **Main CLI Size**: 180 lines (87% reduction from 1,400 lines)
- **Code Quality**: 110 lines of duplicate code eliminated

**Refactoring Impact:**
- ✅ 87% reduction in main file size
- ✅ 100% elimination of code duplication
- ✅ 45% increase in test count (66 → 96 tests)
- ✅ Professional structure with industry-standard patterns

---

**Made with ❤️ for music producers who love clean, organized systems**
