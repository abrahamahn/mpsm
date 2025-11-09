"""Data folder scanner for presets, samples, and libraries."""

from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import platform

from ..core.logger import get_logger
from ..core.config import ConfigManager
from ..models.folder import DataFolder, FolderType


IS_WINDOWS = platform.system() == 'Windows'


class FolderScanner:
    """Scans for music production data folders (presets, samples, libraries)."""

    # Known folder patterns for different types
    PRESET_PATTERNS = [
        '**/Presets/**',
        '**/User Presets/**',
        '**/*.vstpreset',
        '**/FXP/**',
        '**/FXB/**',
    ]

    SAMPLE_PATTERNS = [
        '**/Samples/**',
        '**/Sample Libraries/**',
        '**/Audio Samples/**',
    ]

    LIBRARY_PATTERNS = [
        '**/Libraries/**',
        '**/Content/**',
        '**/Soundbanks/**',
        '**/Instruments/**',
    ]

    # Known vendor data folder locations
    VENDOR_DATA_FOLDERS = {
        'Native Instruments': [
            'Native Instruments',
            'NI Resources',
        ],
        'Spectrasonics': [
            'Spectrasonics',
            'STEAM',
        ],
        'Waves': [
            'Waves Audio',
            'WavesData',
        ],
        'iZotope': [
            'iZotope',
        ],
        'FabFilter': [
            'FabFilter',
        ],
        'Arturia': [
            'Arturia',
        ],
        'Image-Line': [
            'Image-Line',
            'FL Studio',
        ],
        # Additional vendors from user's installation
        'Zynaptiq': ['Zynaptiq'],
        'Air Music Technology': ['Air Music Technology'],
        'Baby Audio': ['Baby Audio'],
        'DeviousMachines': ['DeviousMachines'],
        'discoDSP': ['discoDSP'],
        'Eventide': ['Eventide'],
        'Fielding DSP': ['Fielding DSP'],
        'HOFA': ['HOFA'],
        'Klanghelm': ['Klanghelm'],
        'Klevgrand': ['Klevgrand'],
        'KORG': ['KORG'],
        'KV331 Audio': ['KV331 Audio'],
        'LenndarDigital': ['LenndarDigital'],
        'Newfangled Audio': ['Newfangled Audio'],
        'Ohm Force': ['Ohm Force'],
        'Plugin Alliance': ['Plugin Alliance'],
        'Plugin Boutique': ['Plugin Boutique'],
        'Press Play': ['Press Play'],
        'Propellerhead': ['Propellerhead'],
        'reFX': ['reFX'],
        'Softube': ['Softube', 'Softube Central'],
        'Sonarworks': ['Sonarworks'],
        'Sonic Charge': ['Sonic Charge'],
        'Sonnox': ['Sonnox'],
        'Sononym': ['Sononym'],
        'Tokyo Dawn Labs': ['Tokyo Dawn Labs'],
        'u-he': ['u-he'],
        'Vital': ['Vital'],
        'Voxengo': ['Voxengo'],
        'XLN Audio': ['XLN Audio'],
        'Youlean': ['Youlean'],
        # Additional vendors from user's comprehensive plugin list
        'Aberrant DSP': ['Aberrant DSP'],
        'Acustica Audio': ['Acustica Audio', 'Acustica'],
        'Antelope Audio': ['Antelope Audio'],
        'AudioThing': ['AudioThing'],
        'Black Rooster Audio': ['Black Rooster Audio', 'Black Rooster'],
        'Boz Digital Labs': ['Boz Digital Labs', 'Boz Digital'],
        'Cableguys': ['Cableguys'],
        'Caelum Audio': ['Caelum Audio'],
        'D16': ['D16'],
        'Dada Life': ['Dada Life'],
        'Fiedler Audio': ['Fiedler Audio'],
        'Future Audio Workshop': ['Future Audio Workshop', 'FAW'],
        'Ignite Amps': ['Ignite Amps'],
        'Kilohearts': ['Kilohearts'],
        'MeldaProduction': ['MeldaProduction', 'Melda'],
        'Mixed In Key': ['Mixed In Key'],
        'Oeksound': ['Oeksound'],
        'Output': ['Output'],
        'Polyverse': ['Polyverse'],
        'Reaper': ['Reaper', 'Cockos'],
        'Reason Studios': ['Reason Studios'],
        'Reveal Sound': ['Reveal Sound'],
        'Schrammel': ['Schrammel'],
        'Serato': ['Serato'],
        'Shattered Glass Audio': ['Shattered Glass Audio', 'Shattered Glass'],
        'Slate Digital': ['Slate Digital'],
        'Sonible': ['Sonible'],
        'Sonic Academy': ['Sonic Academy'],
        'Soundtheory': ['Soundtheory'],
        'Soundtoys': ['Soundtoys'],
        'TAL': ['TAL'],
        'Tokyo Dawn Records': ['Tokyo Dawn Records', 'TDR'],
        'United Plugins': ['United Plugins'],
        'Valhalla': ['Valhalla'],
        'Vengeance': ['Vengeance'],
        'Wavesfactory': ['Wavesfactory'],
        'waveTracing': ['waveTracing'],
    }

    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        max_workers: int = 4
    ):
        """
        Initialize folder scanner.

        Args:
            config: Configuration manager
            max_workers: Maximum parallel scan workers
        """
        self.logger = get_logger()
        self.config = config or ConfigManager()
        self.max_workers = max_workers

        # Discovered folders
        self.data_folders: List[DataFolder] = []

    def scan_for_data_folders(
        self,
        scan_paths: Optional[List[str]] = None
    ) -> List[DataFolder]:
        """
        Scan for music production data folders.

        Args:
            scan_paths: Paths to scan. If None, uses common data locations.

        Returns:
            List of discovered data folders
        """
        if scan_paths is None:
            scan_paths = self._get_common_data_paths()

        self.logger.info(f"Scanning for data folders in {len(scan_paths)} paths...")
        self.data_folders = []

        for path_str in scan_paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                self._scan_directory_for_data(path)

        self.logger.info(f"Found {len(self.data_folders)} data folders")
        return self.data_folders

    def _get_common_data_paths(self) -> List[str]:
        """
        Get common data folder locations.

        Returns:
            List of common data paths
        """
        paths = []

        if IS_WINDOWS:
            # Common Windows locations
            paths.extend([
                str(Path.home() / 'Documents'),
                str(Path.home() / 'AppData' / 'Local'),
                str(Path.home() / 'AppData' / 'Roaming'),
                'C:\\ProgramData',
                'C:\\Program Files\\Common Files',
                'C:\\Program Files (x86)\\Common Files',
            ])
        else:
            # Mac/Linux locations
            paths.extend([
                str(Path.home() / 'Library' / 'Application Support'),
                str(Path.home() / 'Library' / 'Audio'),
                str(Path.home() / 'Music'),
                str(Path.home() / 'Documents'),
                '/Library/Application Support',
                '/Library/Audio',
            ])

        return paths

    def _scan_directory_for_data(self, directory: Path, depth: int = 0, max_depth: int = 4) -> None:
        """
        Scan a directory for data folders.

        Args:
            directory: Directory to scan
            depth: Current recursion depth
            max_depth: Maximum recursion depth
        """
        if depth > max_depth:
            return

        try:
            for item in directory.iterdir():
                if item.is_dir():
                    # Check if this is a data folder
                    folder_type = self._identify_folder_type(item)
                    if folder_type:
                        data_folder = self._create_data_folder(item, folder_type)
                        if data_folder:
                            self.data_folders.append(data_folder)

                    # Recurse into subdirectories
                    self._scan_directory_for_data(item, depth + 1, max_depth)

        except PermissionError:
            self.logger.debug(f"Permission denied scanning {directory}")
        except Exception as e:
            self.logger.warning(f"Error scanning {directory}: {e}")

    def _identify_folder_type(self, folder_path: Path) -> Optional[FolderType]:
        """
        Identify the type of data folder.

        Args:
            folder_path: Folder path to check

        Returns:
            FolderType if identified, None otherwise
        """
        folder_name_lower = folder_path.name.lower()

        # Check for preset folders
        if any(pattern in folder_name_lower for pattern in [
            'preset', 'fxp', 'fxb', 'patch', 'sound'
        ]):
            return FolderType.PRESETS

        # Check for sample folders
        if any(pattern in folder_name_lower for pattern in [
            'sample', 'audio', 'wav', 'loops', 'drums'
        ]):
            return FolderType.SAMPLES

        # Check for library folders
        if any(pattern in folder_name_lower for pattern in [
            'library', 'libraries', 'content', 'soundbank', 'instrument'
        ]):
            return FolderType.LIBRARY

        # Check for project folders
        if any(pattern in folder_name_lower for pattern in [
            'project', 'session', 'song'
        ]):
            return FolderType.PROJECTS

        # Check for known vendor folders
        for vendor, folder_names in self.VENDOR_DATA_FOLDERS.items():
            if any(name.lower() in folder_name_lower for name in folder_names):
                # Determine more specific type based on subfolder
                if 'preset' in folder_name_lower or 'user' in folder_name_lower:
                    return FolderType.PRESETS
                elif 'sample' in folder_name_lower:
                    return FolderType.SAMPLES
                else:
                    return FolderType.LIBRARY

        return None

    def _create_data_folder(
        self,
        folder_path: Path,
        folder_type: FolderType
    ) -> Optional[DataFolder]:
        """
        Create DataFolder object.

        Args:
            folder_path: Path to folder
            folder_type: Type of folder

        Returns:
            DataFolder object or None
        """
        try:
            # Calculate folder size and file count
            total_size, file_count = self._calculate_folder_stats(folder_path)

            # Determine owner/publisher
            owner = self._determine_owner(folder_path)

            data_folder = DataFolder(
                name=folder_path.name,
                owner=owner,
                folder_type=folder_type,
                path=folder_path,
                total_size=total_size,
                file_count=file_count,
            )

            self.logger.debug(f"Identified {folder_type.value} folder: {folder_path}")
            return data_folder

        except Exception as e:
            self.logger.warning(f"Error creating data folder object for {folder_path}: {e}")
            return None

    def _calculate_folder_stats(self, folder_path: Path) -> tuple:
        """
        Calculate folder size and file count.

        Args:
            folder_path: Path to folder

        Returns:
            Tuple of (total_size_bytes, file_count)
        """
        total_size = 0
        file_count = 0

        try:
            for item in folder_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except:
                        pass
        except Exception as e:
            self.logger.debug(f"Error calculating stats for {folder_path}: {e}")

        return total_size, file_count

    def _determine_owner(self, folder_path: Path) -> str:
        """
        Determine folder owner/publisher.

        Args:
            folder_path: Folder path

        Returns:
            Owner name
        """
        # Check path for vendor names
        path_str = str(folder_path).lower()

        for vendor, folder_names in self.VENDOR_DATA_FOLDERS.items():
            if any(name.lower() in path_str for name in folder_names):
                return vendor

        # Check for common vendor names in path
        vendors = [
            # Original vendors
            'Native Instruments', 'Spectrasonics', 'Waves', 'iZotope',
            'FabFilter', 'Arturia', 'Image-Line', 'Steinberg', 'Ableton',
            'Avid', 'Xfer', 'Serum', 'Kontakt', 'Omnisphere',
            # Additional vendors from user's installation
            'Zynaptiq', 'Air Music Technology', 'Baby Audio', 'DeviousMachines',
            'discoDSP', 'Eventide', 'Fielding DSP', 'HOFA', 'Klanghelm',
            'Klevgrand', 'KORG', 'KV331 Audio', 'LenndarDigital', 'Newfangled Audio',
            'Ohm Force', 'Plugin Alliance', 'Plugin Boutique', 'Press Play',
            'Propellerhead', 'reFX', 'Softube', 'Sonarworks', 'Sonic Charge',
            'Sonnox', 'Sononym', 'Tokyo Dawn Labs', 'u-he', 'Vital',
            'Voxengo', 'XLN Audio', 'Youlean', 'FL Cloud Plugins',
            # Additional vendors from user's comprehensive plugin list
            'Aberrant DSP', 'Acustica Audio', 'Antelope Audio', 'AudioThing',
            'Black Rooster Audio', 'Boz Digital Labs', 'Cableguys', 'Caelum Audio',
            'D16', 'Dada Life', 'Fiedler Audio', 'Future Audio Workshop',
            'Ignite Amps', 'Kilohearts', 'MeldaProduction', 'Mixed In Key',
            'Oeksound', 'Output', 'Polyverse', 'Reaper', 'Reason Studios',
            'Reveal Sound', 'Schrammel', 'Serato', 'Shattered Glass Audio',
            'Slate Digital', 'Sonible', 'Sonic Academy', 'Soundtheory',
            'Soundtoys', 'TAL', 'Tokyo Dawn Records', 'United Plugins',
            'Valhalla', 'Vengeance', 'Wavesfactory', 'waveTracing', 'Cockos',
            'PreSonus',
        ]

        for vendor in vendors:
            if vendor.lower() in path_str:
                return vendor

        # Try to extract from folder name or parent
        if len(folder_path.parts) > 1:
            parent = folder_path.parent.name
            if parent not in ['Documents', 'AppData', 'Local', 'Roaming', 'Application Support']:
                return parent

        return 'Unknown'

    def find_preset_folders(self) -> List[DataFolder]:
        """
        Find all preset folders.

        Returns:
            List of preset folders
        """
        return [f for f in self.data_folders if f.folder_type == FolderType.PRESETS]

    def find_sample_folders(self) -> List[DataFolder]:
        """
        Find all sample folders.

        Returns:
            List of sample folders
        """
        return [f for f in self.data_folders if f.folder_type == FolderType.SAMPLES]

    def find_library_folders(self) -> List[DataFolder]:
        """
        Find all library folders.

        Returns:
            List of library folders
        """
        return [f for f in self.data_folders if f.folder_type == FolderType.LIBRARY]

    def get_by_owner(self, owner: str) -> List[DataFolder]:
        """
        Get all folders by owner.

        Args:
            owner: Owner name

        Returns:
            List of folders from owner
        """
        return [
            folder for folder in self.data_folders
            if owner.lower() in folder.owner.lower()
        ]

    def get_total_size_by_type(self) -> Dict[FolderType, int]:
        """
        Get total size by folder type.

        Returns:
            Dictionary mapping folder type to total size in bytes
        """
        sizes = {}
        for folder in self.data_folders:
            if folder.folder_type not in sizes:
                sizes[folder.folder_type] = 0
            sizes[folder.folder_type] += folder.total_size
        return sizes
