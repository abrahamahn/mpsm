"""Configuration management for MPSM."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

try:
    from dotenv import dotenv_values
except ImportError:
    dotenv_values = None


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: Optional[Path] = None, create_if_missing: bool = False):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file. If None, uses default config.yaml
            create_if_missing: If True, skip loading if file doesn't exist (for init command)
        """
        if config_path is None:
            # Default to config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yaml"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

        # Only load config if file exists OR if we're not in create mode
        if self.config_path.exists():
            self.load_config()
        elif not create_if_missing:
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Loaded configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
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

            # Check for either new plugin_paths or legacy scan_paths
            has_plugin_paths = 'plugin_paths' in scan_config and scan_config['plugin_paths']
            has_legacy_paths = 'scan_paths' in scan_config and scan_config['scan_paths']

            if not has_plugin_paths and not has_legacy_paths:
                errors.append("Missing scan.plugin_paths or scan.scan_paths")

            if 'plugin_paths' in scan_config and not isinstance(scan_config['plugin_paths'], list):
                errors.append("scan.plugin_paths must be a list")

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
        Create default configuration file with OPTIMIZED targeted scan paths.

        Args:
            output_path: Where to save config. If None, uses self.config_path
        """
        # Get current Windows username for user paths
        username = os.getenv('USERNAME', 'YOUR_USERNAME')

        default_config = {
            'version': '1.0',
            'root_path': 'C:\\MusicProduction',
            'custom_paths': {
                'vst2': 'Plugins\\VST2',
                'vst3': 'Plugins\\VST3',
                'aax': 'Plugins\\AAX',
                'clap': 'Plugins\\CLAP',
            },
            'scan': {
                # PLUGIN BINARIES ONLY - Known installation directories
                # These paths contain actual .dll/.vst3/.aaxplugin files
                'plugin_paths': [
                    # Common VST2/VST3/AAX installation directories
                    'C:\\Program Files\\VSTPlugins',
                    'C:\\Program Files\\Common Files\\VST3',
                    'C:\\Program Files\\Common Files\\Avid\\Audio\\Plug-Ins',
                    'C:\\Program Files (x86)\\VSTPlugins',
                    'C:\\Program Files (x86)\\Steinberg\\VstPlugins',
                    'C:\\Program Files (x86)\\Common Files\\VST3',
                    # Known vendor plugin directories in Program Files
                    'C:\\Program Files\\Waves\\Plug-Ins V12',
                    'C:\\Program Files\\Waves\\Plug-Ins V13',
                    'C:\\Program Files\\Waves\\Plug-Ins V14',
                    'C:\\Program Files\\Native Instruments',
                    'C:\\Program Files\\iZotope',
                    'C:\\Program Files\\FabFilter',
                    'C:\\Program Files\\Arturia',
                    'C:\\Program Files\\Spectrasonics',
                    'C:\\Program Files\\Xfer',
                    'C:\\Program Files\\u-he',
                    'C:\\Program Files\\Output',
                    'C:\\Program Files\\Soundtoys',
                    'C:\\Program Files\\Slate Digital',
                    'C:\\Program Files\\Plugin Alliance',
                    'C:\\Program Files\\Kilohearts',
                    'C:\\Program Files\\Steinberg\\VSTPlugins',
                    # DAW-specific plugin folders
                    'C:\\Program Files\\Image-Line\\FL Studio\\Plugins',
                    'C:\\Program Files\\Ableton\\Live\\Plug-Ins',
                    'C:\\Program Files\\Avid\\Pro Tools\\Plug-Ins',
                    'C:\\Program Files\\PreSonus\\Studio One\\Plug-Ins',
                    # TARGETED AppData\Roaming vendor directories (plugins only)
                    f'C:\\Users\\{username}\\AppData\\Roaming\\Ableton\\Live',
                    f'C:\\Users\\{username}\\AppData\\Roaming\\Steinberg',
                    f'C:\\Users\\{username}\\AppData\\Roaming\\Image-Line',
                    # TARGETED AppData\Local vendor directories (plugins only)
                    f'C:\\Users\\{username}\\AppData\\Local\\Ableton\\Live',
                    f'C:\\Users\\{username}\\AppData\\Local\\Image-Line',
                    f'C:\\Users\\{username}\\AppData\\Local\\FL Studio',
                    # ProgramData vendor directories (plugins only)
                    'C:\\ProgramData\\Ableton\\Live',
                    'C:\\ProgramData\\Steinberg',
                    # Custom organized directory
                    'C:\\Production\\Applications',
                ],
                # DATA/PRESETS - Scanned with vendor name filtering only
                # These contain presets, samples, licenses, NOT plugin binaries
                'data_paths': [
                    f'C:\\Users\\{username}\\AppData\\Roaming',
                    'C:\\ProgramData',
                    f'C:\\Users\\{username}\\Documents',
                    'C:\\Production',
                ],
                # Backward compatibility - merges plugin_paths + data_paths if no plugin_paths exists
                'scan_paths': [],  # Deprecated, kept for compatibility
                'exclude_paths': [
                    # System directories
                    'C:\\Windows',
                    'C:\\Windows\\System32',
                    'C:\\Windows\\SysWOW64',
                    'C:\\Windows\\WinSxS',
                    # Temp and cache directories (CRITICAL)
                    '**/AppData/Local/Temp/**',
                    '**/AppData/Local/Cache/**',
                    '**/Temp/**',
                    '**/Cache/**',
                    # Installer caches (CRITICAL - thousands of false positives)
                    '**/Waves Audio/instl/**',
                    '**/Native Access/Cache/**',
                    '**/iZotope Product Portal/Cache/**',
                    '**/Splice/Cache/**',
                    # Microsoft directories (NOT music-related)
                    '**/Microsoft/**',
                    '**/Microsoft Corporation/**',
                    '**/MicrosoftEdge/**',
                    '**/OneDrive/**',
                    '**/Windows Mail/**',
                    '**/WindowsApps/**',
                    # Development tools (NOT music-related)
                    '**/VisualStudio/**',
                    '**/Visual Studio Code/**',
                    '**/Node.js/**',
                    '**/Python/**',
                    '**/npm/**',
                    '**/pip/**',
                    '**/conda/**',
                    # Communication apps (NOT music-related)
                    '**/Discord/**',
                    '**/Slack/**',
                    '**/Zoom/**',
                    '**/Microsoft Teams/**',
                    '**/Skype/**',
                    # Browsers (NOT music-related)
                    '**/Google/Chrome/**',
                    '**/Mozilla Firefox/**',
                    '**/Opera/**',
                    '**/Brave/**',
                    # Gaming platforms (NOT music-related)
                    '**/Steam/**',
                    '**/Epic Games/**',
                    '**/Battle.net/**',
                    # Cloud storage (NOT music-related)
                    '**/Dropbox/**',
                    '**/Google Drive/**',
                    '**/Box/**',
                    # Generic non-music apps
                    '**/Adobe/Acrobat/**',
                    '**/Notepad++/**',
                    '**/VLC/**',
                    '**/WinRAR/**',
                    '**/7-Zip/**',
                    # Resource DLLs and artifacts
                    '**/*.resources.dll',
                    '**/node_modules/**',
                    '**/__pycache__/**',
                    '**/bin/**',
                    '**/obj/**',
                ],
                # File validation settings
                'validation': {
                    'check_vst2_exports': True,  # Verify VST2 DLLs have VSTPluginMain export
                    'min_plugin_size_mb': 0.1,  # Skip suspiciously small files
                    'max_plugin_size_mb': 500,  # Skip suspiciously large files
                },
                'parallel': True,
                'max_workers': 4,
                'max_depth': 5,
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
        """
        Get list of paths to scan.

        For backward compatibility, merges plugin_paths + data_paths if no plugin_paths.
        """
        plugin_paths = self.get('scan.plugin_paths', [])
        data_paths = self.get('scan.data_paths', [])
        legacy_paths = self.get('scan.scan_paths', [])

        # If using new config structure
        if plugin_paths:
            return plugin_paths + data_paths
        # Backward compatibility
        elif legacy_paths:
            return legacy_paths
        else:
            return []

    def get_plugin_paths(self) -> List[str]:
        """
        Get list of paths containing plugin binaries (.dll, .vst3, .aaxplugin).

        Includes custom paths from .env file if present.
        """
        plugin_paths = self.get('scan.plugin_paths', [])
        if not plugin_paths:
            # Fallback to scan_paths for backward compatibility
            plugin_paths = self.get('scan.scan_paths', [])

        # Load custom paths from .env file
        custom_paths = self._load_custom_paths_from_env()
        if custom_paths:
            plugin_paths = list(plugin_paths) + custom_paths

        return plugin_paths

    def _load_custom_paths_from_env(self) -> List[str]:
        """
        Load custom plugin paths from .env file.

        Reads all CUSTOM_*_PATH_* variables from .env and returns valid paths.

        Returns:
            List of custom paths that exist
        """
        if dotenv_values is None:
            return []

        env_file = self.config_path.parent / '.env'
        if not env_file.exists():
            return []

        try:
            env_vars = dotenv_values(env_file)
            custom_paths = []

            # Sort keys to maintain consistent order
            sorted_keys = sorted(env_vars.keys())

            for key in sorted_keys:
                # Match CUSTOM_*_PATH_* pattern
                if key.startswith('CUSTOM_') and '_PATH_' in key:
                    value = env_vars[key]
                    if value and value.strip():
                        # Add path regardless of existence (Windows paths won't exist on Linux)
                        custom_paths.append(value.strip())

            return custom_paths

        except Exception as e:
            # Log error but don't fail - custom paths are optional
            return []

    def get_data_paths(self) -> List[str]:
        """Get list of paths containing presets, samples, licenses (vendor-filtered)."""
        return self.get('scan.data_paths', [])

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
