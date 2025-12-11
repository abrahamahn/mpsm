# Contributing to MPSM

First off, thank you for considering contributing to MPSM! It's people like you that make MPSM such a great tool for music producers.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How Can I Contribute?](#how-can-i-contribute)
- [Style Guidelines](#style-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)

---

## Code of Conduct

This project and everyone participating in it is governed by the [MPSM Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## Getting Started

### Prerequisites

- **Python 3.9+** (3.11 recommended)
- **Git**
- **Virtual environment** (venv or conda)
- **Windows 11/10** (for full testing - project is Windows-specific)

### Quick Start

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mpsm.git
cd mpsm

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install with dev dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest tests/ -v
```

---

## Development Setup

### 1. Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally
3. Add the upstream repository as a remote:

```bash
git remote add upstream https://github.com/abrahamahn/mpsm.git
```

### 2. Create a Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

**Branch Naming Conventions:**
- `feature/description` - New features
- `fix/issue-number-description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/improvements

### 3. Install Development Tools

```bash
# Install all dev dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Verify installation
black --version
mypy --version
pytest --version
```

---

## How Can I Contribute?

### Reporting Bugs

**Before submitting a bug report:**
- Check the [existing issues](https://github.com/abrahamahn/mpsm/issues) to avoid duplicates
- Collect relevant information (Python version, OS version, error messages)
- Create a minimal reproduction case

**When reporting bugs, include:**
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Screenshots (if applicable)
- Your environment details
- Relevant logs or error messages

**Use the bug report template** when creating an issue.

### Suggesting Enhancements

We welcome feature suggestions! Before suggesting:
- Check if it's already been suggested
- Consider if it fits the project scope (Windows music production management)
- Think about how it would benefit most users

**Use the feature request template** when creating an enhancement issue.

### Your First Code Contribution

Not sure where to start? Look for issues labeled:
- `good first issue` - Simple issues for newcomers
- `help wanted` - Issues where we need community help
- `documentation` - Documentation improvements

### Pull Requests

We actively welcome pull requests:

1. **Small Changes**: Minor fixes can be submitted directly
2. **Larger Changes**: Open an issue first to discuss the approach
3. **Breaking Changes**: Must be discussed and approved before implementation

---

## Style Guidelines

### Python Code Style

We use **Black** for code formatting with these standards:

```python
# Line length: 100 characters
# String quotes: Double quotes preferred
# Import sorting: isort (automatic with pre-commit)
```

**Run formatters:**
```bash
# Format code
black src/ tests/ mpsm.py

# Check formatting without changes
black --check --diff src/
```

### Code Standards

- **Type hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings for public APIs
- **Comments**: Explain "why", not "what"
- **Variable names**: Descriptive, not abbreviated (except common ones like `df`, `i`)

**Example:**
```python
from typing import List, Optional
from pathlib import Path

def scan_plugins(
    paths: List[str],
    max_workers: int = 4,
    exclude_patterns: Optional[List[str]] = None
) -> List[Plugin]:
    """
    Scan specified paths for VST plugins.

    Args:
        paths: List of directory paths to scan
        max_workers: Number of parallel workers (default: 4)
        exclude_patterns: Optional patterns to exclude from scan

    Returns:
        List of discovered Plugin objects

    Raises:
        ValueError: If paths list is empty
        PermissionError: If directories are not accessible
    """
    if not paths:
        raise ValueError("At least one path must be provided")

    # Implementation...
```

### Testing Standards

- **Test coverage**: Aim for 80%+ on new code
- **Test naming**: `test_<method>_<scenario>_<expected_result>`
- **Test organization**: Group related tests in classes
- **Fixtures**: Use fixtures for common setup
- **Markers**: Use pytest markers (unit, integration, slow)

**Example:**
```python
class TestPluginScanner:
    """Test PluginScanner functionality."""

    def test_scan_finds_vst2_plugins(self, temp_plugin_dir):
        """Test that scanner finds VST2 .dll files."""
        # Arrange
        plugin_file = temp_plugin_dir / "test.dll"
        plugin_file.write_bytes(b"MZ" + b"VSTPluginMain")
        scanner = PluginScanner()

        # Act
        results = scanner.scan([str(temp_plugin_dir)])

        # Assert
        assert len(results) == 1
        assert results[0].format == "VST2"
```

---

## Commit Guidelines

We follow the **Conventional Commits** specification:

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```bash
# Good commit messages
feat(scanner): add support for VST3 scanning
fix(registry): handle missing registry keys gracefully
docs(readme): update installation instructions
test(scanner): add unit tests for BaseScanner
refactor(vendor): centralize vendor data in YAML

# Bad commit messages
fixed bug
updated code
changes
asdf
WIP
```

### Commit Message Details

**Subject line:**
- Use imperative mood ("add" not "added")
- No period at the end
- Max 72 characters
- Lowercase after type

**Body (optional):**
- Explain what and why, not how
- Wrap at 72 characters

**Footer (optional):**
- Reference issues: `Fixes #123`
- Breaking changes: `BREAKING CHANGE: description`

---

## Pull Request Process

### Before Submitting

1. **Update from upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run quality checks:**
   ```bash
   # Format code
   black src/ tests/ mpsm.py

   # Run tests
   pytest tests/ -v

   # Check coverage
   pytest tests/ --cov=src --cov-report=term-missing

   # Type check
   mypy src/ --ignore-missing-imports

   # Lint (fix automatically if possible)
   pylint src/
   ```

3. **Update documentation** if needed

4. **Add tests** for new functionality

### Submitting a PR

1. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request on GitHub**

3. **Fill out the PR template** completely

4. **Link related issues** using keywords:
   - `Fixes #123`
   - `Closes #456`
   - `Related to #789`

### PR Requirements

Your PR must:
- [ ] Pass all CI checks (tests, linting, formatting)
- [ ] Include tests for new functionality
- [ ] Update documentation if needed
- [ ] Have a clear description of changes
- [ ] Reference related issues
- [ ] Be rebased on latest `main`

### Review Process

1. **Automated checks** run first (CI/CD)
2. **Code review** by maintainers
3. **Address feedback** by pushing new commits
4. **Approval** from at least one maintainer
5. **Merge** (squash and merge by default)

### After Merge

1. Delete your branch (both local and remote)
2. Pull the latest main
3. Start a new branch for your next contribution

---

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                 # Fast, isolated tests
│   ├── test_scanner.py
│   └── test_registry.py
├── integration/          # Component integration tests
│   └── test_workflows.py
└── conftest.py          # Shared fixtures
```

### Writing Tests

**DO:**
- Test one thing per test function
- Use descriptive test names
- Use fixtures for setup
- Test edge cases and error conditions
- Aim for 80%+ coverage on new code

**DON'T:**
- Test implementation details
- Write flaky tests
- Skip writing tests (except documented bugs)
- Use hardcoded paths
- Leave commented-out test code

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/unit/test_scanner.py -v

# Specific test
pytest tests/unit/test_scanner.py::TestScanner::test_scan_vst2 -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Only unit tests
pytest tests/unit/

# Only integration tests
pytest tests/integration/

# Skip slow tests
pytest tests/ -m "not slow"

# Run with verbose output
pytest tests/ -vv --tb=short
```

---

## Documentation Guidelines

### Code Documentation

- **Public APIs**: Full docstrings required
- **Private methods**: Brief docstrings optional
- **Complex logic**: Inline comments explaining why
- **Type hints**: Always use for function signatures

### User Documentation

- **README.md**: Keep it current with features
- **INSTALLATION.md**: Update for new dependencies
- **API docs**: Auto-generated from docstrings
- **Examples**: Add to `examples/` directory

### Documentation Style

- Use **Markdown** for all docs
- Use **code blocks** with language hints
- Include **examples** for complex features
- Add **diagrams** where helpful (ASCII or images)
- Keep line length **<100 characters**

---

## Questions?

- Open an issue with the `question` label
- Join discussions in GitHub Discussions
- Check existing documentation in `docs/`

---

## Recognition

Contributors are recognized in:
- Git history (commits)
- Release notes (CHANGELOG.md)
- Contributors section (README.md)

---

**Thank you for contributing to MPSM!** 🎵

Every contribution, no matter how small, helps make music production software management better for everyone.
