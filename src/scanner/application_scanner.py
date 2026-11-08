"""Application and DAW scanner."""

import fnmatch
import platform
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core.config import ConfigManager
from ..data.vendor_registry import vendor_registry
from ..models.application import Application, ApplicationType
from ..models.plugin import Version
from .base_scanner import BaseScanner
from .metadata.pe_parser import extract_version_from_pe, parse_version_string

IS_WINDOWS = platform.system() == "Windows"


class ApplicationScanner(BaseScanner[Application]):
    """
    Scans for music production applications and DAWs.

    Uses centralized VendorRegistry for executable pattern matching.
    """

    def __init__(self, config: Optional[ConfigManager] = None, max_workers: int = 4):
        """
        Initialize application scanner.

        Args:
            config: Configuration manager
            max_workers: Maximum parallel scan workers
        """
        super().__init__(config, max_workers)

    # ========================================================================
    # BaseScanner abstract methods implementation
    # ========================================================================

    def _get_default_scan_paths(self) -> List[str]:
        """
        Get default paths to scan for applications.

        Returns:
            List of common application installation paths
        """
        return self._get_common_installation_paths()

    def _identify_item(self, path: Path) -> Optional[Application]:
        """
        Identify if path is a known music production application.

        Args:
            path: Path to check

        Returns:
            Application object if identified, None otherwise
        """
        if not path.is_file():
            return None

        return self._identify_application(path)

    # ========================================================================
    # Public API (maintains backward compatibility)
    # ========================================================================

    @property
    def applications(self) -> List[Application]:
        """Get discovered applications (backward compatibility)."""
        return self.items

    @applications.setter
    def applications(self, value: List[Application]) -> None:
        """Set discovered applications (backward compatibility)."""
        self.items = value

    def scan_for_applications(self, scan_paths: Optional[List[str]] = None) -> List[Application]:
        """
        Scan for music production applications.

        Uses BaseScanner's scan() method for consistent behavior.

        Args:
            scan_paths: Paths to scan. If None, uses common installation paths.

        Returns:
            List of discovered applications
        """
        return self.scan(scan_paths)

    def _get_common_installation_paths(self) -> List[str]:
        """
        Get common installation paths for applications.

        Returns:
            List of common installation paths
        """
        paths: List[str] = []

        if IS_WINDOWS:
            paths.extend(
                [
                    "C:\\Program Files",
                    "C:\\Program Files (x86)",
                    "C:\\Program Files\\Common Files",
                    "C:\\Program Files (x86)\\Common Files",
                    "C:\\Program Files\\VSTPlugins",
                    "C:\\Program Files\\Steinberg",
                    "C:\\Program Files\\Image-Line",
                    "C:\\Program Files\\Ableton",
                    "C:\\Program Files\\Avid",
                ]
            )
        else:
            paths.extend(
                [
                    "/Applications",
                    "/Library/Application Support",
                    str(Path.home() / "Applications"),
                ]
            )

        return paths

    # ========================================================================
    # Helper methods (application-specific logic)
    # ========================================================================

    def _identify_application(self, file_path: Path) -> Optional[Application]:
        """
        Identify if file is a known music production application.

        Uses centralized VendorRegistry for executable pattern matching.

        Args:
            file_path: File path to check

        Returns:
            Application object if identified, None otherwise
        """
        filename = file_path.name

        # Check DAWs using VendorRegistry
        daw_executables = vendor_registry.get_all_daw_executables()
        for daw_name, executables in daw_executables.items():
            for exe_pattern in executables:
                if self._match_pattern(filename, exe_pattern):
                    return self._create_application(file_path, daw_name, ApplicationType.DAW)

        # Check plugin managers using VendorRegistry
        plugin_managers = vendor_registry.get_all_plugin_manager_executables()
        for manager_name, executables in plugin_managers.items():
            for exe_pattern in executables:
                if self._match_pattern(filename, exe_pattern):
                    return self._create_application(
                        file_path, manager_name, ApplicationType.PLUGIN_MANAGER
                    )

        # Check standalone plugins using VendorRegistry
        standalone_plugins = vendor_registry.get_all_standalone_executables()
        for plugin_name, executables in standalone_plugins.items():
            for exe_pattern in executables:
                if self._match_pattern(filename, exe_pattern):
                    return self._create_application(
                        file_path, plugin_name, ApplicationType.STANDALONE
                    )

        return None

    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """
        Match filename against pattern (supports wildcards).

        Args:
            filename: Filename to match
            pattern: Pattern with optional wildcards (*)

        Returns:
            True if matches
        """
        return fnmatch.fnmatch(filename.lower(), pattern.lower())

    def _create_application(
        self, file_path: Path, name: str, app_type: ApplicationType
    ) -> Application:
        """
        Create Application object.

        Args:
            file_path: Path to executable
            name: Application name
            app_type: Application type

        Returns:
            Application object
        """
        try:
            stats = file_path.stat()
            file_size = stats.st_size
            install_date = datetime.fromtimestamp(stats.st_ctime)

            version = self._extract_version(file_path)
            publisher = self._determine_publisher(name, file_path)

            app = Application(
                name=name,
                publisher=publisher,
                version=version,
                app_type=app_type,
                executable_path=file_path,
                install_path=file_path.parent,
                file_size=file_size,
                install_date=install_date,
            )

            self.logger.debug(f"Identified application: {name} at {file_path}")
            return app

        except Exception as e:
            self.logger.warning(f"Error creating application object for {file_path}: {e}")
            raise

    def _extract_version(self, file_path: Path) -> Optional[Version]:
        """
        Extract version from executable PE header or filename/directory.

        Args:
            file_path: Path to executable

        Returns:
            Version object or None
        """
        pe_version = extract_version_from_pe(file_path)
        if pe_version:
            return pe_version

        for text in (file_path.stem, file_path.parent.name):
            for part in text.split():
                if part and (part[0].isdigit() or part.lower().startswith("v")):
                    if "." in part:
                        parsed = parse_version_string(part)
                        if parsed:
                            return parsed

        return None

    def _determine_publisher(self, app_name: str, file_path: Path) -> str:
        """
        Determine application publisher using centralized VendorRegistry.

        Args:
            app_name: Application name
            file_path: File path

        Returns:
            Publisher name
        """
        vendor = vendor_registry.find_vendor_by_pattern(f"{app_name} {file_path}")
        if vendor:
            return vendor

        for part in file_path.parts:
            folder_vendor = vendor_registry.find_vendor_by_folder(part)
            if folder_vendor:
                return folder_vendor

        return "Unknown"

    def find_daws(self) -> List[Application]:
        """
        Find all DAW applications.

        Returns:
            List of DAW applications
        """
        return [app for app in self.applications if app.app_type == ApplicationType.DAW]

    def find_plugin_managers(self) -> List[Application]:
        """
        Find all plugin manager applications.

        Returns:
            List of plugin manager applications
        """
        return [app for app in self.applications if app.app_type == ApplicationType.PLUGIN_MANAGER]

    def find_standalone_plugins(self) -> List[Application]:
        """
        Find all standalone plugin applications.

        Returns:
            List of standalone plugin applications
        """
        return [app for app in self.applications if app.app_type == ApplicationType.STANDALONE]

    def get_by_publisher(self, publisher: str) -> List[Application]:
        """
        Get all applications by publisher.

        Args:
            publisher: Publisher name

        Returns:
            List of applications from publisher
        """
        return [app for app in self.applications if publisher.lower() in app.publisher.lower()]
