# MPSM Documentation

Welcome to the MPSM documentation! This directory contains all project documentation organized by purpose.

## Directory Structure

```
docs/
├── manual/          # User-facing documentation
├── dev/             # Developer/codebase documentation
└── COMPREHENSIVE_PLAN.md  # Original project plan
```

## User Documentation (`manual/`)

For users who want to **install and use** MPSM:

- **[INSTALLATION.md](manual/INSTALLATION.md)** - Complete installation guide
  - Installation methods (user, dev, quick)
  - Post-installation setup
  - Troubleshooting
  - First scan walkthrough

- **[CUSTOM_PATHS.md](manual/CUSTOM_PATHS.md)** - Customizing scan paths
  - Adding custom scan locations
  - Excluding directories
  - Path configuration

- **[METADATA_EXTRACTION_GUIDE.md](manual/METADATA_EXTRACTION_GUIDE.md)** - Understanding metadata
  - How MPSM extracts plugin information
  - PE header parsing
  - VST signature detection

- **[JUCE_VST_HOST_PROTOCOL.md](manual/JUCE_VST_HOST_PROTOCOL.md)** - Technical reference
  - VST hosting implementation details
  - JUCE framework integration

## Developer Documentation (`dev/`)

For developers who want to **understand and contribute** to MPSM:

### Architecture & Design

- **[BASESCANNER_ARCHITECTURE.md](dev/BASESCANNER_ARCHITECTURE.md)** - Scanner architecture
  - Abstract Base Class pattern
  - Generic type implementation
  - Code reduction metrics
  - Usage examples

- **[FRAMEWORK.md](dev/FRAMEWORK.md)** - Overall framework design
  - Data models
  - CLI structure
  - Module organization

### Development Process

- **[REFACTORING_SUMMARY.md](dev/REFACTORING_SUMMARY.md)** - Refactoring history
  - Phase 1: Initial restructuring
  - Phase 2: BaseScanner implementation
  - Code quality improvements

- **[TESTING_SUMMARY.md](dev/TESTING_SUMMARY.md)** - Testing infrastructure
  - Test suite overview (96 tests)
  - Coverage reports
  - Testing guidelines

- **[SCALABILITY_ANALYSIS.md](dev/SCALABILITY_ANALYSIS.md)** - Scalability considerations
  - Performance analysis
  - Optimization opportunities
  - Future improvements

- **[IMPROVEMENTS.md](dev/IMPROVEMENTS.md)** - Improvement roadmap
  - Planned features
  - Known issues
  - Enhancement ideas

- **[BRANCH_INFO.md](dev/BRANCH_INFO.md)** - Git branching strategy
  - Branch naming conventions
  - Development workflow

## Quick Links

### For Users
1. Start here: [INSTALLATION.md](manual/INSTALLATION.md)
2. Customize paths: [CUSTOM_PATHS.md](manual/CUSTOM_PATHS.md)
3. Main README: [../README.md](../README.md)

### For Developers
1. Start here: [FRAMEWORK.md](dev/FRAMEWORK.md)
2. Architecture: [BASESCANNER_ARCHITECTURE.md](dev/BASESCANNER_ARCHITECTURE.md)
3. Contributing: [../CONTRIBUTING.md](../CONTRIBUTING.md)
4. Testing: [TESTING_SUMMARY.md](dev/TESTING_SUMMARY.md)

## Documentation Standards

When adding new documentation:

1. **User docs** → `docs/manual/`
   - Installation guides
   - Usage instructions
   - Troubleshooting
   - Configuration guides

2. **Developer docs** → `docs/dev/`
   - Architecture decisions
   - Code organization
   - Testing strategies
   - Refactoring notes

3. **Community docs** → Root directory
   - CONTRIBUTING.md
   - CODE_OF_CONDUCT.md
   - SECURITY.md
   - CHANGELOG.md

## Contributing to Documentation

- Use Markdown format
- Include code examples
- Add table of contents for long docs
- Keep line length under 100 characters
- Include screenshots where helpful
- Update this README when adding new docs

## Questions?

- Check existing docs first
- Open an issue with `documentation` label
- See [CONTRIBUTING.md](../CONTRIBUTING.md)
