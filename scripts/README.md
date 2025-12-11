# MPSM Development Scripts

Utility scripts for common development tasks.

## Scripts

### `setup-dev.sh`
**Purpose:** Complete development environment setup

**Usage:**
```bash
bash scripts/setup-dev.sh
```

**What it does:**
- Checks Python version
- Warns if not in virtual environment
- Installs MPSM with dev dependencies
- Installs pre-commit hooks
- Runs initial tests

### `run-tests.sh`
**Purpose:** Comprehensive test runner

**Usage:**
```bash
# Run all tests with coverage (default)
bash scripts/run-tests.sh

# Run only unit tests
bash scripts/run-tests.sh unit

# Run only integration tests
bash scripts/run-tests.sh integration

# Run tests without coverage
bash scripts/run-tests.sh all no
```

**Options:**
- Test type: `unit`, `integration`, `all` (default: all)
- Coverage: `yes`, `no` (default: yes)

### `check-quality.sh`
**Purpose:** Run all code quality checks

**Usage:**
```bash
bash scripts/check-quality.sh
```

**Checks:**
1. Black formatting
2. isort import sorting
3. flake8 linting
4. mypy type checking
5. bandit security scanning

**Exit codes:**
- 0: All checks passed
- 1: One or more checks failed

## Making Scripts Executable

```bash
chmod +x scripts/*.sh
```

## Windows Users

For Windows users without bash, use the equivalent Make commands:

```bash
# Instead of scripts/setup-dev.sh
make install-dev

# Instead of scripts/run-tests.sh
make test
make test-unit
make test-integration

# Instead of scripts/check-quality.sh
make ci
```

## Adding New Scripts

When adding new scripts:

1. Create the script in `scripts/` directory
2. Add shebang: `#!/bin/bash`
3. Add `set -e` for error handling
4. Make it executable: `chmod +x scripts/your-script.sh`
5. Document it in this README
6. Consider adding equivalent Make target

## See Also

- [Makefile](../Makefile) - Make targets for common tasks
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guidelines
- [docs/dev/](../docs/dev/) - Developer documentation
