# Contributing to MPSM

Thank you for your interest in contributing to the Music Production Software Manager!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/mpsm.git
   cd mpsm
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```
4. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

```
mpsm/
├── mpsm.py                 # Main CLI interface
├── config.yaml             # Configuration template
├── requirements.txt        # Python dependencies
├── modules/
│   ├── scanner.py         # System scanning logic
│   ├── registry_manager.py # Registry operations
│   ├── updater.py         # Update checking
│   ├── license_tracker.py # License management
│   └── installer.py       # Custom installation
├── backups/               # Automatic backups
├── logs/                  # Operation logs
└── data/                  # Scan results
```

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported
2. Open a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (Windows version, Python version)
   - Log files from `logs/` directory

### Suggesting Features

1. Open an issue describing:
   - The feature and its benefits
   - Potential implementation approach
   - Any concerns or edge cases

### Code Contributions

1. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow coding standards**:
   - Use meaningful variable and function names
   - Add docstrings to all functions and classes
   - Follow PEP 8 style guide
   - Add type hints where appropriate

3. **Write tests** (when available):
   ```python
   # Example test structure
   def test_scanner_finds_vst3():
       scanner = PluginScanner(config)
       results = scanner.scan_files("test_data/")
       assert len(results) > 0
   ```

4. **Document your changes**:
   - Update README.md if needed
   - Add comments for complex logic
   - Update COMPREHENSIVE_PLAN.md for major features

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description of feature"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**:
   - Describe what your PR does
   - Reference any related issues
   - Include screenshots/logs if relevant

## Coding Standards

### Python Style

- Follow PEP 8
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names

### Docstring Format

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
    pass
```

### Logging

Use appropriate log levels:
```python
self.logger.debug("Detailed debug information")
self.logger.info("General information")
self.logger.warning("Warning message")
self.logger.error("Error message")
self.logger.critical("Critical error")
```

## Priority Areas for Contribution

### High Priority
- [ ] Scanner module implementation
- [ ] Registry manager Windows API integration
- [ ] License tracking logic

### Medium Priority
- [ ] Auto-updater vendor scrapers
- [ ] Custom installer path enforcement
- [ ] GUI interface (future)

### Low Priority
- [ ] Additional DAW support
- [ ] Cloud backup integration
- [ ] Plugin usage analytics

## Testing Guidelines

1. Test on Windows 11 (primary target)
2. Test with real VST plugins (use free plugins)
3. Always test in dry-run mode first
4. Verify registry changes don't break DAWs
5. Check that backups are created correctly

## Safety Considerations

When contributing code that:
- Modifies the registry
- Moves files
- Runs installers

Please ensure:
- Dry-run mode is respected
- Backups are created first
- Rollback functionality works
- Errors are logged properly

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion
- Reach out to maintainers

Thank you for contributing to MPSM! 🎵
