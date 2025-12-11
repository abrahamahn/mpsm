#!/bin/bash
# Code quality check script - runs all quality checks

set -e

echo "========================================"
echo "MPSM Code Quality Checks"
echo "========================================"
echo ""

# Initialize counters
ERRORS=0

# 1. Black formatting check
echo "[1/5] Checking code formatting with Black..."
if black --check --diff src/ tests/ mpsm.py; then
    echo "✓ Black formatting passed"
else
    echo "✗ Black formatting failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. Import sorting check
echo "[2/5] Checking import sorting with isort..."
if isort --check-only src/ tests/ mpsm.py; then
    echo "✓ isort check passed"
else
    echo "✗ isort check failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. Linting with flake8
echo "[3/5] Running flake8 linter..."
if flake8 src/ tests/ mpsm.py; then
    echo "✓ flake8 passed"
else
    echo "✗ flake8 failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 4. Type checking with mypy
echo "[4/5] Running mypy type checker..."
if mypy src/ --ignore-missing-imports; then
    echo "✓ mypy passed"
else
    echo "⚠ mypy had issues (non-blocking)"
    # Don't increment errors for mypy
fi
echo ""

# 5. Security check with bandit
echo "[5/5] Running bandit security check..."
if bandit -r src/ -c pyproject.toml 2>/dev/null; then
    echo "✓ bandit passed"
else
    echo "⚠ bandit found issues (review recommended)"
fi
echo ""

# Summary
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    echo "✓ All quality checks passed!"
    echo "========================================"
    exit 0
else
    echo "✗ $ERRORS check(s) failed"
    echo "========================================"
    echo ""
    echo "To fix formatting issues, run:"
    echo "  make format"
    exit 1
fi
