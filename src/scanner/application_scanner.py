"""Application and DAW scanner."""

from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import platform

from ..core.logger import get_logger
from ..core.config import ConfigManager
from ..models.application import Application, ApplicationType


IS_WINDOWS = platform.system() == 'Windows'


class ApplicationScanner:
    """Scans for music production applications and DAWs."""

    # Known DAW executables
    DAW_EXECUTABLES = {
        'FL Studio': ['FL64.exe', 'FL.exe'],
        'Ableton Live': ['Ableton Live*.exe'],
        'Cubase': ['Cubase*.exe'],
        'Nuendo': ['Nuendo*.exe'],
        'Pro Tools': ['ProTools.exe'],
        'Logic Pro': ['Logic Pro X'],
        'Studio One': ['Studio One.exe'],
        'Reaper': ['reaper.exe'],
        'Bitwig Studio': ['Bitwig Studio.exe'],
        'Reason': ['Reason.exe'],
        'Cakewalk': ['Cakewalk.exe', 'SONAR.exe'],
        'GarageBand': ['GarageBand'],
    }

    # Known plugin managers and utilities
    PLUGIN_MANAGERS = {
        'Waves Central': ['WavesCentral.exe'],
        'Native Access': ['Native Access.exe'],
        'iLok License Manager': ['iLokLicenseManager.exe', 'iLok License Manager'],
        'Plugin Alliance': ['Plugin Alliance*.exe'],
        'Arturia Software Center': ['Arturia Software Center.exe'],
        'Splice': ['Splice.exe'],
        'Output Hub': ['Output Hub.exe'],
        'Roland Cloud Manager': ['Roland Cloud Manager.exe'],
        'Komplete Kontrol': ['Komplete Kontrol.exe'],
        'Vienna Assistant': ['Vienna Assistant.exe'],
        'Soundtoys': ['Soundtoys*.exe'],
        'iZotope Product Portal': ['iZotope Product Portal.exe'],
    }

    # Known standalone instruments/effects
    STANDALONE_PLUGINS = {
        'Kontakt': ['Kontakt*.exe'],
        'Komplete Kontrol': ['Komplete Kontrol*.exe'],
        'Battery': ['Battery*.exe'],
        'Reaktor': ['Reaktor*.exe'],
        'Maschine': ['Maschine*.exe'],
        'Serum': ['Serum*.exe'],
        'Omnisphere': ['Omnisphere*.exe'],
        'Keyscape': ['Keyscape*.exe'],
        'Trilian': ['Trilian*.exe'],
    }

    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        max_workers: int = 4
    ):
        """
        Initialize application scanner.

        Args:
            config: Configuration manager
            max_workers: Maximum parallel scan workers
        """
        self.logger = get_logger()
        self.config = config or ConfigManager()
        self.max_workers = max_workers

        # Discovered applications
        self.applications: List[Application] = []

    def scan_for_applications(
        self,
        scan_paths: Optional[List[str]] = None
    ) -> List[Application]:
        """
        Scan for music production applications.

        Args:
            scan_paths: Paths to scan. If None, uses common installation paths.

        Returns:
            List of discovered applications
        """
        if scan_paths is None:
            scan_paths = self._get_common_installation_paths()

        self.logger.info(f"Scanning for applications in {len(scan_paths)} paths...")
        self.applications = []

        for path_str in scan_paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                self._scan_directory_for_applications(path)

        self.logger.info(f"Found {len(self.applications)} applications")
        return self.applications

    def _get_common_installation_paths(self) -> List[str]:
        """
        Get common installation paths for applications.

        Returns:
            List of common installation paths
        """
        paths = []

        if IS_WINDOWS:
            paths.extend([
                'C:\\Program Files',
                'C:\\Program Files (x86)',
                'C:\\Program Files\\Common Files',
                'C:\\Program Files (x86)\\Common Files',
                'C:\\Program Files\\VSTPlugins',
                'C:\\Program Files\\Steinberg',
                'C:\\Program Files\\Image-Line',
                'C:\\Program Files\\Ableton',
                'C:\\Program Files\\Avid',
            ])
        else:
            # Mac/Linux paths
            paths.extend([
                '/Applications',
                '/Library/Application Support',
                str(Path.home() / 'Applications'),
            ])

        return paths

    def _scan_directory_for_applications(self, directory: Path, depth: int = 0, max_depth: int = 3) -> None:
        """
        Scan a directory for applications.

        Args:
            directory: Directory to scan
            depth: Current recursion depth
            max_depth: Maximum recursion depth
        """
        if depth > max_depth:
            return

        try:
            for item in directory.iterdir():
                if item.is_file():
                    # Check if file is a known application
                    app = self._identify_application(item)
                    if app:
                        self.applications.append(app)

                elif item.is_dir():
                    # Recurse into subdirectories
                    self._scan_directory_for_applications(item, depth + 1, max_depth)

        except PermissionError:
            self.logger.debug(f"Permission denied scanning {directory}")
        except Exception as e:
            self.logger.warning(f"Error scanning {directory}: {e}")

    def _identify_application(self, file_path: Path) -> Optional[Application]:
        """
        Identify if file is a known music production application.

        Args:
            file_path: File path to check

        Returns:
            Application object if identified, None otherwise
        """
        filename = file_path.name

        # Check DAWs
        for daw_name, executables in self.DAW_EXECUTABLES.items():
            for exe_pattern in executables:
                if self._match_pattern(filename, exe_pattern):
                    return self._create_application(
                        file_path,
                        daw_name,
                        ApplicationType.DAW
                    )

        # Check plugin managers
        for manager_name, executables in self.PLUGIN_MANAGERS.items():
            for exe_pattern in executables:
                if self._match_pattern(filename, exe_pattern):
                    return self._create_application(
                        file_path,
                        manager_name,
                        ApplicationType.PLUGIN_MANAGER
                    )

        # Check standalone plugins
        for plugin_name, executables in self.STANDALONE_PLUGINS.items():
            for exe_pattern in executables:
                if self._match_pattern(filename, exe_pattern):
                    return self._create_application(
                        file_path,
                        plugin_name,
                        ApplicationType.STANDALONE_PLUGIN
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
        import fnmatch
        return fnmatch.fnmatch(filename.lower(), pattern.lower())

    def _create_application(
        self,
        file_path: Path,
        name: str,
        app_type: ApplicationType
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
            # Get file stats
            stats = file_path.stat()
            file_size = stats.st_size
            install_date = datetime.fromtimestamp(stats.st_ctime)

            # Extract version if possible
            version = self._extract_version(file_path)

            # Determine publisher
            publisher = self._determine_publisher(name, file_path)

            app = Application(
                name=name,
                publisher=publisher,
                version=version,
                app_type=app_type,
                executable_path=file_path,
                install_path=file_path.parent,
                file_size=file_size,
                installation_date=install_date,
            )

            self.logger.debug(f"Identified application: {name} at {file_path}")
            return app

        except Exception as e:
            self.logger.warning(f"Error creating application object for {file_path}: {e}")
            raise

    def _extract_version(self, file_path: Path) -> Optional[str]:
        """
        Extract version from executable.

        Args:
            file_path: Path to executable

        Returns:
            Version string or None
        """
        # This would require reading PE headers on Windows
        # For now, try to extract from filename or parent directory

        # Check filename for version
        parts = file_path.stem.split()
        for part in parts:
            if part[0].isdigit() and any(c in part for c in ['.', 'v']):
                return part.replace('v', '').replace('V', '')

        # Check parent directory for version
        parent = file_path.parent.name
        parts = parent.split()
        for part in parts:
            if part[0].isdigit() and '.' in part:
                return part

        return None

    def _determine_publisher(self, app_name: str, file_path: Path) -> str:
        """
        Determine application publisher.

        Args:
            app_name: Application name
            file_path: File path

        Returns:
            Publisher name
        """
        # Map of applications to publishers
        publishers = {
            'FL Studio': 'Image-Line',
            'Ableton Live': 'Ableton',
            'Cubase': 'Steinberg',
            'Nuendo': 'Steinberg',
            'Pro Tools': 'Avid',
            'Logic Pro': 'Apple',
            'Studio One': 'PreSonus',
            'Reaper': 'Cockos',
            'Bitwig Studio': 'Bitwig',
            'Reason': 'Reason Studios',
            'Cakewalk': 'BandLab',
            'GarageBand': 'Apple',
            'Waves Central': 'Waves',
            'Native Access': 'Native Instruments',
            'iLok License Manager': 'PACE',
            'Plugin Alliance': 'Plugin Alliance',
            'Arturia Software Center': 'Arturia',
            'Kontakt': 'Native Instruments',
            'Komplete Kontrol': 'Native Instruments',
            'Battery': 'Native Instruments',
            'Reaktor': 'Native Instruments',
            'Maschine': 'Native Instruments',
            'Serum': 'Xfer Records',
            'Omnisphere': 'Spectrasonics',
            'Keyscape': 'Spectrasonics',
            'Trilian': 'Spectrasonics',
        }

        # Check if known application
        for known_app, publisher in publishers.items():
            if known_app.lower() in app_name.lower():
                return publisher

        # Try to extract from path
        path_parts = file_path.parts
        for part in path_parts:
            if part in publishers.values():
                return part

        # Check for common publisher names in path
        common_publishers = [
            'Steinberg', 'Image-Line', 'Ableton', 'Avid', 'Native Instruments',
            'Waves', 'iZotope', 'FabFilter', 'Plugin Alliance', 'Arturia',
            'Spectrasonics', 'Xfer', 'Cockos', 'PreSonus', 'Bitwig'
        ]

        for part in path_parts:
            for publisher in common_publishers:
                if publisher.lower() in part.lower():
                    return publisher

        return 'Unknown'

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
        return [app for app in self.applications if app.app_type == ApplicationType.STANDALONE_PLUGIN]

    def get_by_publisher(self, publisher: str) -> List[Application]:
        """
        Get all applications by publisher.

        Args:
            publisher: Publisher name

        Returns:
            List of applications from publisher
        """
        return [
            app for app in self.applications
            if publisher.lower() in app.publisher.lower()
        ]
