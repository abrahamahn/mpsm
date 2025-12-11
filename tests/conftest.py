"""Pytest fixtures and configuration."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_plugin_path(temp_dir: Path) -> Path:
    """Create a sample plugin file for testing."""
    plugin_dir = temp_dir / "C:" / "Program Files" / "Native Instruments" / "Kontakt"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    plugin_file = plugin_dir / "kontakt.dll"
    plugin_file.write_bytes(b"MZ" + b"\x00" * 100 + b"VSTPluginMain" + b"\x00" * 100)

    return plugin_file


@pytest.fixture
def sample_config_yaml(temp_dir: Path) -> Path:
    """Create a sample config YAML file."""
    config_file = temp_dir / "test_config.yaml"
    config_content = """
version: '1.0'
root_path: 'C:\\MusicProduction'
scan:
  plugin_paths:
    - 'C:\\Program Files\\VSTPlugins'
  data_paths:
    - 'C:\\ProgramData'
  exclude_paths:
    - 'C:\\Windows'
  validation:
    check_vst2_exports: true
    min_plugin_size_mb: 0.1
    max_plugin_size_mb: 500
  parallel: true
  max_workers: 4
  max_depth: 5
logging:
  level: INFO
  log_to_console: true
  log_to_file: true
safety:
  dry_run: true
  backup_before_move: true
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_vendor_data() -> dict:
    """Mock vendor data for testing."""
    return {
        "vendors": {
            "native_instruments": {
                "name": "Native Instruments",
                "patterns": ["native instruments", "komplete", "kontakt"],
                "folders": ["Native Instruments", "NI Resources"],
                "executables": ["Native Access.exe"],
                "daw_executables": [],
                "standalone_executables": ["Kontakt*.exe"],
            },
            "waves": {
                "name": "Waves",
                "patterns": ["waves audio", "waves"],
                "folders": ["Waves Audio", "WavesData"],
                "executables": ["WavesCentral.exe"],
                "daw_executables": [],
                "standalone_executables": [],
            },
            "fl_studio": {
                "name": "Image-Line",
                "patterns": ["image-line", "fl studio", "flstudio"],
                "folders": ["Image-Line", "FL Studio"],
                "executables": [],
                "daw_executables": ["FL64.exe", "FL.exe"],
                "standalone_executables": [],
            },
        }
    }
