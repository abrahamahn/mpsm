"""Folder data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class FolderType(Enum):
    """Folder type classification."""

    PLUGIN_INSTALLATION = "Plugin Installation"
    PRESETS = "Presets"
    SAMPLES = "Samples"
    LIBRARY = "Library"
    PROJECTS = "Projects"
    USER_DATA = "User Data"
    FACTORY_DATA = "Factory Data"
    CONFIGURATION = "Configuration"
    CACHE = "Cache"
    DOCUMENTATION = "Documentation"
    UNKNOWN = "Unknown"


@dataclass
class DataFolder:
    """Data folder data model."""

    # Identification
    path: Path
    name: Optional[str] = None
    folder_type: FolderType = FolderType.UNKNOWN
    owner: Optional[str] = None  # Plugin/App that owns this folder

    # Contents
    file_count: int = 0
    total_size: int = 0
    file_types: Dict[str, int] = field(default_factory=dict)  # Extension -> count

    # Metadata
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None

    # Relationships
    parent_plugin: Optional[str] = None
    parent_application: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for export.

        Returns:
            Dictionary representation
        """
        return {
            "path": str(self.path),
            "type": self.folder_type.value,
            "owner": self.owner or "",
            "file_count": self.file_count,
            "size_mb": round(self.total_size / (1024 * 1024), 2),
            "size_gb": round(self.total_size / (1024 * 1024 * 1024), 3),
            "parent_plugin": self.parent_plugin or "",
            "parent_application": self.parent_application or "",
            "created_date": self.created_date.isoformat() if self.created_date else "",
            "modified_date": self.modified_date.isoformat() if self.modified_date else "",
            "file_types": ", ".join(f"{ext}:{count}" for ext, count in self.file_types.items()),
        }

    def add_file_type(self, extension: str, count: int = 1) -> None:
        """Add or increment file type count."""
        extension = extension.lower()
        self.file_types[extension] = self.file_types.get(extension, 0) + count

    def get_size_mb(self) -> float:
        """Get folder size in MB."""
        return round(self.total_size / (1024 * 1024), 2)

    def get_size_gb(self) -> float:
        """Get folder size in GB."""
        return round(self.total_size / (1024 * 1024 * 1024), 3)

    def __repr__(self) -> str:
        """String representation."""
        return f"DataFolder(path='{self.path}', type={self.folder_type.value})"

    def __str__(self) -> str:
        """User-friendly string representation."""
        size_str = (
            f"{self.get_size_gb():.2f} GB"
            if self.total_size > 1024**3
            else f"{self.get_size_mb():.2f} MB"
        )
        return f"{self.path.name} ({self.folder_type.value}, {self.file_count} files, {size_str})"


@dataclass
class PluginInstallation:
    """Complete plugin installation including all components."""

    # Plugin info
    plugin_name: str
    publisher: str

    # Components
    plugin_files: List[Path] = field(default_factory=list)  # VST2/VST3/AAX files
    executables: List[Path] = field(default_factory=list)  # Standalone versions
    data_folders: List[DataFolder] = field(default_factory=list)  # Presets, samples, etc.

    # Installation
    install_root: Optional[Path] = None
    total_size: int = 0

    # Registry
    registry_keys: List[str] = field(default_factory=list)

    def get_all_paths(self) -> List[Path]:
        """
        Get all file/folder paths for this installation.

        Returns:
            List of all paths
        """
        paths = []
        paths.extend(self.plugin_files)
        paths.extend(self.executables)
        paths.extend([f.path for f in self.data_folders])
        if self.install_root:
            paths.append(self.install_root)
        return paths

    def to_dict(self) -> dict:
        """
        Convert to dictionary for export.

        Returns:
            Dictionary representation
        """
        return {
            "plugin_name": self.plugin_name,
            "publisher": self.publisher,
            "plugin_files_count": len(self.plugin_files),
            "executables_count": len(self.executables),
            "data_folders_count": len(self.data_folders),
            "install_root": str(self.install_root) if self.install_root else "",
            "total_size_gb": round(self.total_size / (1024 * 1024 * 1024), 3),
            "registry_keys_count": len(self.registry_keys),
            "plugin_files": ", ".join(str(p) for p in self.plugin_files),
            "executables": ", ".join(str(p) for p in self.executables),
        }

    def calculate_total_size(self) -> int:
        """
        Calculate total installation size.

        Returns:
            Total size in bytes
        """
        total = 0

        # Add plugin files
        for file_path in self.plugin_files:
            if file_path.exists():
                total += file_path.stat().st_size

        # Add executables
        for file_path in self.executables:
            if file_path.exists():
                total += file_path.stat().st_size

        # Add data folders
        for folder in self.data_folders:
            total += folder.total_size

        self.total_size = total
        return total

    def __repr__(self) -> str:
        """String representation."""
        return f"PluginInstallation(plugin_name='{self.plugin_name}', publisher='{self.publisher}')"

    def __str__(self) -> str:
        """User-friendly string representation."""
        size_gb = round(self.total_size / (1024 * 1024 * 1024), 2)
        return (
            f"{self.plugin_name} by {self.publisher} ({len(self.plugin_files)} files, {size_gb} GB)"
        )
