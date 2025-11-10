#!/bin/bash
# Comprehensive test runner script

set -e

echo "========================================"
echo "MPSM Test Suite Runner"
echo "========================================"
echo ""

# Parse command line arguments
TEST_TYPE=${1:-all}
COVERAGE=${2:-yes}

run_unit_tests() {
    echo "Running unit tests..."
    if [ "$COVERAGE" = "yes" ]; then
        pytest tests/unit/ -v --cov=src --cov-report=term-missing
    else
        pytest tests/unit/ -v
    fi
}

run_integration_tests() {
    echo "Running integration tests..."
    pytest tests/integration/ -v
}

run_all_tests() {
    echo "Running all tests..."
    if [ "$COVERAGE" = "yes" ]; then
        pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
        echo ""
        echo "Coverage report generated: htmlcov/index.html"
    else
        pytest tests/ -v
    fi
}

case $TEST_TYPE in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    all)
        run_all_tests
        ;;
    *)
        echo "Usage: $0 {unit|integration|all} [yes|no]"
        echo "  Test type: unit, integration, or all (default: all)"
        echo "  Coverage: yes or no (default: yes)"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "Tests Complete!"
echo "========================================"
