"""Target folder structure builder."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import ConfigManager
from ..core.exceptions import ValidationException
from ..core.logger import get_logger
from ..models.application import Application
from ..models.folder import DataFolder, FolderType
from ..models.plugin import Plugin, PluginType


class StructureBuilder:
    """Builds target folder structure for all components."""

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize structure builder.

        Args:
            config: Configuration manager. If None, loads default config.
        """
        self.logger = get_logger()
        self.config = config or ConfigManager()
        self.root_path = self.config.get_root_path()

    def create_structure(self) -> None:
        """
        Create complete target folder structure.

        Creates:
            - DAWs/
            - Plugins/VST2, VST3, AAX, etc.
            - Libraries/
            - Licenses/
            - Temp/
        """
        self.logger.info(f"Creating folder structure at: {self.root_path}")

        # Get paths from config
        paths_to_create = [
            self.root_path,
            self.root_path / self.config.get("custom_paths.vst2", "Plugins/VST2"),
            self.root_path / self.config.get("custom_paths.vst3", "Plugins/VST3"),
            self.root_path / self.config.get("custom_paths.aax", "Plugins/AAX"),
            self.root_path / self.config.get("custom_paths.clap", "Plugins/CLAP"),
            self.root_path / self.config.get("custom_paths.daw_fl", "DAWs/FLStudio"),
            self.root_path / self.config.get("custom_paths.daw_ableton", "DAWs/Ableton"),
            self.root_path / self.config.get("custom_paths.libraries", "Libraries"),
            self.root_path / self.config.get("custom_paths.licenses", "Licenses"),
            self.root_path / self.config.get("custom_paths.temp", "Temp"),
        ]

        for path in paths_to_create:
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {path}")
            except Exception as e:
                self.logger.error(f"Failed to create {path}: {e}")
                raise ValidationException(
                    "Could not create directory", {"path": str(path), "error": str(e)}
                )

        self.logger.info("✓ Folder structure created successfully")

    def validate_structure(self) -> List[str]:
        """
        Validate that target structure exists.

        Returns:
            List of validation errors. Empty if valid.
        """
        errors = []

        # Check root path
        if not self.root_path.exists():
            errors.append(f"Root path does not exist: {self.root_path}")
            return errors

        # Check required subdirectories
        required_paths = [
            "custom_paths.vst2",
            "custom_paths.vst3",
            "custom_paths.libraries",
            "custom_paths.licenses",
        ]

        for path_key in required_paths:
            path = self.root_path / self.config.get(path_key, "")
            if not path.exists():
                errors.append(f"Required path missing: {path}")

        return errors

    def map_plugin_file_location(self, plugin: Plugin) -> Path:
        """
        Determine target location for a plugin file.

        Args:
            plugin: Plugin object

        Returns:
            Target path for plugin file

        Example:
            VST2: C:\\MusicProduction\\Plugins\\VST2\\Waves\\WavesPlugin.dll
            VST3: C:\\MusicProduction\\Plugins\\VST3\\Serum.vst3
        """
        # Get base path for plugin type
        if plugin.plugin_type == PluginType.VST2:
            base_path = self.root_path / str(self.config.get("custom_paths.vst2", "Plugins/VST2"))
        elif plugin.plugin_type == PluginType.VST3:
            base_path = self.root_path / str(self.config.get("custom_paths.vst3", "Plugins/VST3"))
        elif plugin.plugin_type == PluginType.AAX:
            base_path = self.root_path / str(self.config.get("custom_paths.aax", "Plugins/AAX"))
        elif plugin.plugin_type == PluginType.CLAP:
            base_path = self.root_path / str(self.config.get("custom_paths.clap", "Plugins/CLAP"))
        else:
            base_path = self.root_path / "Plugins" / "Unknown"

        # For certain publishers (like Waves), group in vendor folder
        if plugin.publisher in [
            "Waves",
            "iZotope",
            "FabFilter",
            "Native Instruments",
            "Plugin Alliance",
        ]:
            vendor_path = base_path / plugin.publisher
            return (
                vendor_path / plugin.file_path.name
                if plugin.file_path
                else vendor_path / f"{plugin.name}.dll"
            )
        else:
            # Individual plugins go in root of type folder
            return (
                base_path / plugin.file_path.name
                if plugin.file_path
                else base_path / f"{plugin.name}.dll"
            )

    def map_application_location(self, app: Application) -> Path:
        """
        Determine target location for an application.

        Args:
            app: Application object

        Returns:
            Target path for application folder

        Example:
            C:\\MusicProduction\\Plugins\\Xfer\\Serum\\Serum.exe
        """
        base_path = self.root_path / "Plugins"

        # Create vendor/app folder
        vendor_path = base_path / app.publisher / app.name
        return vendor_path

    def map_data_folder_location(self, folder: DataFolder, plugin_name: str) -> Path:
        """
        Determine target location for a data folder.

        Args:
            folder: DataFolder object
            plugin_name: Name of plugin that owns this folder

        Returns:
            Target path for data folder

        Example:
            C:\\MusicProduction\\Libraries\\Serum\\Presets\\
            C:\\MusicProduction\\Libraries\\Kontakt\\Libraries\\
        """
        base_path = self.root_path / str(self.config.get("custom_paths.libraries", "Libraries"))

        # Create plugin folder under Libraries
        plugin_path = base_path / plugin_name

        # Map folder type to subdirectory
        if folder.folder_type == FolderType.PRESETS:
            return plugin_path / "Presets"
        elif folder.folder_type == FolderType.SAMPLES:
            return plugin_path / "Samples"
        elif folder.folder_type == FolderType.USER_DATA:
            return plugin_path / "UserData"
        elif folder.folder_type == FolderType.FACTORY_DATA:
            return plugin_path / "Factory"
        else:
            return plugin_path / folder.path.name

    def map_license_location(self, plugin_name: str) -> Path:
        """
        Determine target location for license files.

        Args:
            plugin_name: Plugin name

        Returns:
            Target path for license files

        Example:
            C:\\MusicProduction\\Licenses\\Serum\\
        """
        base_path = self.root_path / str(self.config.get("custom_paths.licenses", "Licenses"))
        return base_path / plugin_name

    def get_vendor_folder_path(self, vendor: str, plugin_type: PluginType) -> Path:
        """
        Get path to vendor folder for organizing plugins.

        Args:
            vendor: Vendor/publisher name
            plugin_type: Plugin type

        Returns:
            Path to vendor folder
        """
        if plugin_type == PluginType.VST2:
            base = self.root_path / str(self.config.get("custom_paths.vst2", "Plugins/VST2"))
        elif plugin_type == PluginType.VST3:
            base = self.root_path / str(self.config.get("custom_paths.vst3", "Plugins/VST3"))
        elif plugin_type == PluginType.AAX:
            base = self.root_path / str(self.config.get("custom_paths.aax", "Plugins/AAX"))
        else:
            base = self.root_path / "Plugins"

        return base / vendor

    def calculate_required_space(self, items: List) -> int:
        """
        Calculate total space required for items.

        Args:
            items: List of plugins, applications, or folders

        Returns:
            Total space required in bytes
        """
        total_size = 0

        for item in items:
            if hasattr(item, "file_size"):
                total_size += item.file_size
            elif hasattr(item, "total_size"):
                total_size += item.total_size

        return total_size

    def get_available_space(self, path: Optional[Path] = None) -> int:
        """
        Get available disk space at target location.

        Args:
            path: Path to check. If None, uses root_path.

        Returns:
            Available space in bytes
        """
        import shutil

        check_path = path or self.root_path

        # Ensure path exists or use parent
        while not check_path.exists() and check_path.parent != check_path:
            check_path = check_path.parent

        try:
            stat = shutil.disk_usage(check_path)
            return stat.free
        except Exception as e:
            self.logger.warning(f"Could not get disk space for {check_path}: {e}")
            return 0

    def verify_sufficient_space(self, required_bytes: int) -> bool:
        """
        Verify sufficient disk space is available.

        Args:
            required_bytes: Required space in bytes

        Returns:
            True if sufficient space available
        """
        available = self.get_available_space()

        # Add 10% buffer
        required_with_buffer = int(required_bytes * 1.1)

        if available < required_with_buffer:
            self.logger.error(
                f"Insufficient disk space. "
                f"Required: {required_with_buffer / (1024**3):.2f} GB, "
                f"Available: {available / (1024**3):.2f} GB"
            )
            return False

        return True

    def get_structure_summary(self) -> Dict[str, Any]:
        """
        Get summary of target structure.

        Returns:
            Dictionary with structure information
        """
        paths_info: Dict[str, Dict[str, Any]] = {}
        summary: Dict[str, Any] = {
            "root_path": str(self.root_path),
            "paths": paths_info,
            "available_space_gb": round(self.get_available_space() / (1024**3), 2),
        }

        # Add all configured paths
        for key in ["vst2", "vst3", "aax", "clap", "libraries", "licenses"]:
            path_key = f"custom_paths.{key}"
            rel_path = self.config.get(path_key, "")
            if rel_path:
                full_path = self.root_path / rel_path
                paths_info[key] = {
                    "path": str(full_path),
                    "exists": full_path.exists(),
                }

        return summary
