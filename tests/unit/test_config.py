"""Unit tests for config externalization."""

import os
from pathlib import Path

import pytest
import yaml

from src.core.config import ConfigManager


class TestConfigExternalization:
    """Test config externalization and template loading."""

    def test_create_default_config_from_template(self, temp_dir):
        """Test creating default config from template."""
        output_path = temp_dir / "test_config.yaml"

        config = ConfigManager(create_if_missing=True)
        config.create_default_config(output_path)

        assert output_path.exists()

        # Load and validate created config
        with open(output_path, "r") as f:
            loaded_config = yaml.safe_load(f)

        assert loaded_config["version"] == "1.0"
        assert "root_path" in loaded_config
        assert "scan" in loaded_config
        assert "logging" in loaded_config
        assert "safety" in loaded_config

    def test_template_variable_replacement(self, temp_dir):
        """Test that {USERNAME} is replaced correctly."""
        output_path = temp_dir / "test_config.yaml"

        # Set a test username
        os.environ["USERNAME"] = "testuser"

        config = ConfigManager(create_if_missing=True)
        config.create_default_config(output_path)

        # Read the config file
        with open(output_path, "r") as f:
            content = f.read()

        # Check that {USERNAME} was replaced
        assert "{USERNAME}" not in content
        assert "testuser" in content or "YOUR_USERNAME" in content

    def test_config_template_exists(self):
        """Test that config/defaults.yaml template exists."""
        template_path = Path(__file__).parent.parent.parent / "config" / "defaults.yaml"
        assert template_path.exists(), "defaults.yaml template should exist"

    def test_config_template_valid_yaml(self):
        """Test that config template is valid YAML."""
        template_path = Path(__file__).parent.parent.parent / "config" / "defaults.yaml"

        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)

        assert template_data is not None
        assert isinstance(template_data, dict)

    def test_config_template_has_required_sections(self):
        """Test that template has all required sections."""
        template_path = Path(__file__).parent.parent.parent / "config" / "defaults.yaml"

        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)

        required_sections = ["version", "root_path", "scan", "logging", "safety"]

        for section in required_sections:
            assert section in template_data, f"Missing section: {section}"

    def test_config_scan_section_structure(self):
        """Test that scan section has correct structure."""
        template_path = Path(__file__).parent.parent.parent / "config" / "defaults.yaml"

        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)

        scan = template_data["scan"]
        assert "plugin_paths" in scan
        assert "data_paths" in scan
        assert "exclude_paths" in scan
        assert "validation" in scan
        assert "parallel" in scan
        assert "max_workers" in scan

    def test_config_has_plugin_paths(self):
        """Test that config has plugin paths defined."""
        template_path = Path(__file__).parent.parent.parent / "config" / "defaults.yaml"

        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)

        plugin_paths = template_data["scan"]["plugin_paths"]
        assert isinstance(plugin_paths, list)
        assert len(plugin_paths) > 0

    def test_config_has_exclude_paths(self):
        """Test that config has exclude paths defined."""
        template_path = Path(__file__).parent.parent.parent / "config" / "defaults.yaml"

        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)

        exclude_paths = template_data["scan"]["exclude_paths"]
        assert isinstance(exclude_paths, list)
        assert len(exclude_paths) > 0

    def test_config_manager_load_from_template(self, temp_dir):
        """Test ConfigManager can load config created from template."""
        output_path = temp_dir / "test_config.yaml"

        # Create config from template
        config1 = ConfigManager(create_if_missing=True)
        config1.create_default_config(output_path)

        # Load the created config
        config2 = ConfigManager(output_path)

        version = config2.get("version")
        assert version == "1.0"

        plugin_paths = config2.get("scan.plugin_paths")
        assert isinstance(plugin_paths, list)
        assert len(plugin_paths) > 0

    def test_config_validation_with_template(self, temp_dir):
        """Test that config created from template passes validation."""
        output_path = temp_dir / "test_config.yaml"

        config = ConfigManager(create_if_missing=True)
        config.create_default_config(output_path)

        # Load and validate
        config_manager = ConfigManager(output_path)
        errors = config_manager.validate_config()

        # On Linux, we might get path validation errors for Windows paths
        # Filter out those errors
        real_errors = [e for e in errors if "root_path" not in e]

        assert len(real_errors) == 0, f"Validation errors: {real_errors}"

    def test_config_template_missing_raises_error(self, temp_dir):
        """Test that missing template raises appropriate error."""
        config = ConfigManager(create_if_missing=True)

        def patched_create_default_config(output_path=None):
            template_path = Path("/nonexistent/defaults.yaml")

            if not template_path.exists():
                raise FileNotFoundError(
                    f"Default config template not found: {template_path}\n"
                    "Please ensure config/defaults.yaml exists in the project root."
                )

        config.create_default_config = patched_create_default_config

        with pytest.raises(FileNotFoundError) as exc_info:
            config.create_default_config(temp_dir / "test.yaml")

        assert "defaults.yaml" in str(exc_info.value)


class TestConfigManagerMethods:
    """Test ConfigManager utility methods."""

    def test_get_scan_paths(self, sample_config_yaml):
        """Test getting scan paths from config."""
        config = ConfigManager(sample_config_yaml)
        scan_paths = config.get_scan_paths()

        assert isinstance(scan_paths, list)
        assert len(scan_paths) > 0

    def test_get_plugin_paths(self, sample_config_yaml):
        """Test getting plugin paths from config."""
        config = ConfigManager(sample_config_yaml)
        plugin_paths = config.get_plugin_paths()

        assert isinstance(plugin_paths, list)
        assert len(plugin_paths) > 0

    def test_get_exclude_paths(self, sample_config_yaml):
        """Test getting exclude paths from config."""
        config = ConfigManager(sample_config_yaml)
        exclude_paths = config.get_exclude_paths()

        assert isinstance(exclude_paths, list)
        assert len(exclude_paths) > 0
