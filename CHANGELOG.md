# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows (ci.yml, test-pr.yml)
- Comprehensive installation infrastructure (setup.py, pyproject.toml)
- Installation guide (docs/INSTALLATION.md)
- BaseScanner architecture documentation
- Contributing guidelines (CONTRIBUTING.md)
- Code of Conduct
- 96 automated tests (90 passing, 6 documented bugs)

### Changed
- Refactored scanners to use BaseScanner abstract class
- Centralized vendor data in vendors.yaml (50+ vendors)
- Externalized configuration to config/defaults.yaml
- Reduced main CLI from 1,400 to 180 lines (87% reduction)

### Fixed
- Scanner parallel execution stability
- Vendor detection case sensitivity
- Configuration template generation

## [1.0.0] - 2025-11-10

### Added
- Initial release
- VST2, VST3, AAX plugin scanning
- Windows registry backup and restore
- License tracking (iLok, proprietary)
- File organization system
- Metadata extraction (PE headers, VST signatures)
- Multi-threaded scanning with progress bars
- CSV/Excel export functionality

### Features
- **Scanner Infrastructure**
  - BaseScanner abstract class with generics
  - FolderScanner for data folders
  - ApplicationScanner for plugins/DAWs
  - Parallel scanning with ThreadPoolExecutor

- **Vendor Registry**
  - 50+ major vendors (Native Instruments, Waves, iZotope, etc.)
  - YAML-based centralized database
  - Pattern matching for paths and folders

- **Registry Management**
  - Backup registry keys
  - Update plugin paths
  - Validate registry entries
  - Restore from backup

- **License Management**
  - Scan for .lic, .key, iLok files
  - Validate activation status
  - Centralize license files

- **Testing**
  - 96 automated tests
  - 92% coverage on VendorRegistry
  - 74% coverage on BaseScanner
  - Integration test suite

- **CI/CD**
  - GitHub Actions workflows
  - Multi-version Python testing (3.9, 3.10, 3.11)
  - Code quality checks (Black, MyPy, Pylint)
  - Coverage tracking with Codecov

### Documentation
- README.md with badges and quick start
- Installation guide (docs/INSTALLATION.md)
- Architecture documentation (docs/BASESCANNER_ARCHITECTURE.md)
- Testing summary (docs/TESTING_SUMMARY.md)
- Refactoring history (docs/REFACTORING_SUMMARY.md)
- Framework design (docs/FRAMEWORK.md)

### Technical Improvements
- 110 lines of duplicate code eliminated
- Type-safe scanner implementations
- Consistent error handling
- Professional project structure

---

## Version History

### [1.0.0] - 2025-11-10
First production release with complete feature set, testing, and documentation.

---

## Release Notes Template

```markdown
## [Version] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Features that will be removed

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security fixes
```

---

[Unreleased]: https://github.com/abrahamahn/mpsm/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/abrahamahn/mpsm/releases/tag/v1.0.0
