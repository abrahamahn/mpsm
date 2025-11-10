#!/bin/bash
# Development environment setup script for MPSM

set -e  # Exit on error

echo "========================================"
echo "MPSM Development Environment Setup"
echo "========================================"
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠ Warning: Not in a virtual environment"
    echo "  Recommended: python -m venv venv && source venv/Scripts/activate"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Installing MPSM with development dependencies..."
pip install -e .[dev]

echo ""
echo "Installing pre-commit hooks..."
pre-commit install

echo ""
echo "Running pre-commit on all files (first time may be slow)..."
pre-commit run --all-files || true

echo ""
echo "Running tests to verify setup..."
pytest tests/ -v --tb=short || true

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Quick commands:"
echo "  make test           - Run tests"
echo "  make format         - Format code"
echo "  make lint           - Run linters"
echo "  make dev            - Full development cycle"
echo ""
echo "See Makefile for more commands"
