"""Data folder scanner for presets, samples, and libraries."""

import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..core.config import ConfigManager
from ..data.vendor_registry import vendor_registry
from ..models.folder import DataFolder, FolderType
from .base_scanner import BaseScanner

IS_WINDOWS = platform.system() == "Windows"


class FolderScanner(BaseScanner[DataFolder]):
    """Scans for music production data folders (presets, samples, libraries)."""

    # Known folder patterns for different types
    PRESET_PATTERNS = [
        "**/Presets/**",
        "**/User Presets/**",
        "**/*.vstpreset",
        "**/FXP/**",
        "**/FXB/**",
    ]

    SAMPLE_PATTERNS = [
        "**/Samples/**",
        "**/Sample Libraries/**",
        "**/Audio Samples/**",
    ]

    LIBRARY_PATTERNS = [
        "**/Libraries/**",
        "**/Content/**",
        "**/Soundbanks/**",
        "**/Instruments/**",
    ]

    def __init__(self, config: Optional[ConfigManager] = None, max_workers: int = 4):
        """
        Initialize folder scanner.

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
        Get default paths to scan for data folders.

        Returns:
            List of common data folder locations
        """
        return self._get_common_data_paths()

    def _identify_item(self, path: Path) -> Optional[DataFolder]:
        """
        Identify if path is a valid data folder.

        Args:
            path: Path to check

        Returns:
            DataFolder object if identified, None otherwise
        """
        if not path.is_dir():
            return None

        folder_type = self._identify_folder_type(path)
        if folder_type:
            return self._create_data_folder(path, folder_type)

        return None

    # ========================================================================
    # Public API (maintains backward compatibility)
    # ========================================================================

    @property
    def data_folders(self) -> List[DataFolder]:
        """Get discovered data folders (backward compatibility)."""
        return self.items

    @data_folders.setter
    def data_folders(self, value: List[DataFolder]) -> None:
        """Set discovered data folders (backward compatibility)."""
        self.items = value

    def scan_for_data_folders(self, scan_paths: Optional[List[str]] = None) -> List[DataFolder]:
        """
        Scan for music production data folders.

        Uses BaseScanner's scan() method for consistent behavior.

        Args:
            scan_paths: Paths to scan. If None, uses common data locations.

        Returns:
            List of discovered data folders
        """
        return self.scan(scan_paths)

    def _get_common_data_paths(self) -> List[str]:
        """
        Get common data folder locations.

        Returns:
            List of common data paths
        """
        paths: List[str] = []

        if IS_WINDOWS:
            paths.extend(
                [
                    str(Path.home() / "Documents"),
                    str(Path.home() / "AppData" / "Local"),
                    str(Path.home() / "AppData" / "Roaming"),
                    "C:\\ProgramData",
                    "C:\\Program Files\\Common Files",
                    "C:\\Program Files (x86)\\Common Files",
                ]
            )
        else:
            paths.extend(
                [
                    str(Path.home() / "Library" / "Application Support"),
                    str(Path.home() / "Library" / "Audio"),
                    str(Path.home() / "Music"),
                    str(Path.home() / "Documents"),
                    "/Library/Application Support",
                    "/Library/Audio",
                ]
            )

        return paths

    # ========================================================================
    # Helper methods (folder-specific logic)
    # ========================================================================

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
        if "soundbank" not in folder_name_lower and any(
            pattern in folder_name_lower for pattern in ["preset", "fxp", "fxb", "patch", "sound"]
        ):
            return FolderType.PRESETS

        # Check for sample folders
        if any(
            pattern in folder_name_lower for pattern in ["sample", "audio", "wav", "loops", "drums"]
        ):
            return FolderType.SAMPLES

        # Check for library folders
        if any(
            pattern in folder_name_lower
            for pattern in ["library", "libraries", "content", "soundbank", "instrument"]
        ):
            return FolderType.LIBRARY

        # Check for project folders
        if any(pattern in folder_name_lower for pattern in ["project", "session", "song"]):
            return FolderType.PROJECTS

        # Check for known vendor folders using VendorRegistry
        vendor = vendor_registry.find_vendor_by_folder(folder_path.name)
        if vendor:
            if "preset" in folder_name_lower or "user" in folder_name_lower:
                return FolderType.PRESETS
            if "sample" in folder_name_lower:
                return FolderType.SAMPLES
            return FolderType.LIBRARY

        return None

    def _create_data_folder(
        self, folder_path: Path, folder_type: FolderType
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
            total_size, file_count = self._calculate_folder_stats(folder_path)
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

    def _calculate_folder_stats(self, folder_path: Path) -> Tuple[int, int]:
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
            for item in folder_path.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except OSError:
                        pass
        except Exception as e:
            self.logger.debug(f"Error calculating stats for {folder_path}: {e}")

        return total_size, file_count

    def _determine_owner(self, folder_path: Path) -> str:
        """
        Determine folder owner/publisher.

        Uses centralized VendorRegistry for vendor matching.

        Args:
            folder_path: Folder path

        Returns:
            Owner name
        """
        path_str = str(folder_path)
        vendor = vendor_registry.find_vendor_by_pattern(path_str)
        if vendor:
            return vendor

        if len(folder_path.parts) > 1:
            parent = folder_path.parent.name
            if parent not in ["Documents", "AppData", "Local", "Roaming", "Application Support"]:
                return parent

        return "Unknown"

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
            folder
            for folder in self.data_folders
            if folder.owner and owner.lower() in folder.owner.lower()
        ]

    def get_total_size_by_type(self) -> Dict[FolderType, int]:
        """
        Get total size by folder type.

        Returns:
            Dictionary mapping folder type to total size in bytes
        """
        sizes: Dict[FolderType, int] = {}
        for folder in self.data_folders:
            if folder.folder_type not in sizes:
                sizes[folder.folder_type] = 0
            sizes[folder.folder_type] += folder.total_size
        return sizes
