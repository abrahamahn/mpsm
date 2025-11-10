"""Application data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from .plugin import Version


class ApplicationType(Enum):
    """Application type."""

    PLUGIN_MANAGER = "Plugin Manager"
    STANDALONE = "Standalone Plugin"
    DAW = "DAW"
    UTILITY = "Utility"
    INSTALLER = "Installer"


@dataclass
class Application:
    """Application/Executable data model."""

    # Identification
    name: str
    publisher: str
    app_type: ApplicationType

    # Version
    version: Optional[Version] = None

    # Paths
    executable_path: Optional[Path] = None
    install_path: Optional[Path] = None

    # Registry
    registry_key: Optional[str] = None
    uninstall_key: Optional[str] = None

    # Relationships
    related_plugins: List[str] = field(default_factory=list)
    related_folders: List[Path] = field(default_factory=list)

    # Metadata
    file_size: int = 0
    install_date: Optional[datetime] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for export.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "publisher": self.publisher,
            "type": self.app_type.value,
            "version": str(self.version) if self.version else "Unknown",
            "executable": str(self.executable_path) if self.executable_path else "",
            "install_path": str(self.install_path) if self.install_path else "",
            "registry_key": self.registry_key or "",
            "uninstall_key": self.uninstall_key or "",
            "related_plugins": ", ".join(self.related_plugins),
            "related_folders_count": len(self.related_folders),
            "file_size_mb": round(self.file_size / (1024 * 1024), 2),
            "install_date": self.install_date.isoformat() if self.install_date else "",
            "description": self.description or "",
        }

    def add_related_plugin(self, plugin_name: str) -> None:
        """Add a related plugin."""
        if plugin_name not in self.related_plugins:
            self.related_plugins.append(plugin_name)

    def add_related_folder(self, folder_path: Path) -> None:
        """Add a related folder."""
        if folder_path not in self.related_folders:
            self.related_folders.append(folder_path)

    def __repr__(self) -> str:
        """String representation."""
        return f"Application(name='{self.name}', type={self.app_type.value})"

    def __str__(self) -> str:
        """User-friendly string representation."""
        if self.version:
            return f"{self.name} v{self.version} ({self.app_type.value})"
        return f"{self.name} ({self.app_type.value})"
