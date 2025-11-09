"""Configuration management for MPSM."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file. If None, uses default config.yaml
        """
        if config_path is None:
            # Default to config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yaml"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Loaded configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        return self.config

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: Configuration to save. If None, saves current config.
        """
        if config is not None:
            self.config = config

        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot notation.

        Args:
            key_path: Dot-separated path to config value (e.g., 'scan.parallel')
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default

        Example:
            >>> config.get('scan.parallel')
            True
            >>> config.get('scan.max_workers', 4)
            4
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set config value by dot notation.

        Args:
            key_path: Dot-separated path to config value
            value: Value to set

        Example:
            >>> config.set('scan.parallel', False)
        """
        keys = key_path.split('.')
        config_ref = self.config

        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]

        config_ref[keys[-1]] = value

    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors = []

        # Check required top-level keys
        required_keys = ['version', 'root_path', 'scan', 'logging']
        for key in required_keys:
            if key not in self.config:
                errors.append(f"Missing required config key: {key}")

        # Validate scan configuration
        if 'scan' in self.config:
            scan_config = self.config['scan']

            if 'scan_paths' not in scan_config:
                errors.append("Missing scan.scan_paths")
            elif not isinstance(scan_config['scan_paths'], list):
                errors.append("scan.scan_paths must be a list")

            if 'max_workers' in scan_config:
                if not isinstance(scan_config['max_workers'], int):
                    errors.append("scan.max_workers must be an integer")
                elif scan_config['max_workers'] < 1:
                    errors.append("scan.max_workers must be at least 1")

        # Validate root_path exists (if not placeholder)
        root_path = self.get('root_path')
        if root_path and '{' not in root_path:  # Not a template
            root_path_obj = Path(root_path)
            # Note: On Linux, Windows paths won't exist, so we skip this check
            # if the path looks like a Windows path
            if not root_path.startswith('C:\\'):
                if not root_path_obj.exists() and not root_path_obj.parent.exists():
                    errors.append(f"root_path parent directory doesn't exist: {root_path}")

        # Validate logging configuration
        if 'logging' in self.config:
            log_config = self.config['logging']
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

            if 'level' in log_config:
                if log_config['level'] not in valid_levels:
                    errors.append(
                        f"Invalid logging level: {log_config['level']}. "
                        f"Must be one of {valid_levels}"
                    )

        return errors

    def create_default_config(self, output_path: Optional[Path] = None) -> None:
        """
        Create default configuration file.

        Args:
            output_path: Where to save config. If None, uses self.config_path
        """
        default_config = {
            'version': '1.0',
            'root_path': 'C:\\MusicProduction',
            'custom_paths': {
                'vst2': 'Plugins\\VST2',
                'vst3': 'Plugins\\VST3',
                'aax': 'Plugins\\AAX',
            },
            'scan': {
                'scan_paths': ['C:\\'],
                'exclude_paths': [
                    'C:\\Windows',
                    'C:\\Windows\\System32',
                ],
                'parallel': True,
                'max_workers': 4,
            },
            'logging': {
                'level': 'INFO',
                'log_to_console': True,
                'log_to_file': True,
            },
            'safety': {
                'dry_run': True,
                'backup_before_move': True,
            },
        }

        save_path = output_path or self.config_path
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    def get_scan_paths(self) -> List[str]:
        """Get list of paths to scan."""
        return self.get('scan.scan_paths', [])

    def get_exclude_paths(self) -> List[str]:
        """Get list of paths to exclude from scanning."""
        return self.get('scan.exclude_paths', [])

    def get_root_path(self) -> Path:
        """Get root path for music production files."""
        root = self.get('root_path', 'C:\\MusicProduction')
        return Path(root)

    def is_dry_run(self) -> bool:
        """Check if dry-run mode is enabled."""
        return self.get('safety.dry_run', True)

    def __repr__(self) -> str:
        """String representation."""
        return f"ConfigManager(config_path={self.config_path})"
