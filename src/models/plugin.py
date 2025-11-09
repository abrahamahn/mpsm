"""Plugin data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class PluginType(Enum):
    """Plugin format types."""
    VST2 = "VST2"
    VST3 = "VST3"
    AAX = "AAX"
    CLAP = "CLAP"
    AU = "AU"
    UNKNOWN = "UNKNOWN"


class PluginCategory(Enum):
    """Plugin vendor categories."""
    INDIVIDUAL = "Individual"
    WAVES = "Waves"
    IZOTOPE = "iZotope"
    FABFILTER = "FabFilter"
    NATIVE_INSTRUMENTS = "Native Instruments"
    ARTURIA = "Arturia"
    PLUGIN_ALLIANCE = "Plugin Alliance"
    XFER = "Xfer Records"
    OTHER = "Other"


@dataclass
class Version:
    """Software version information."""

    major: int
    minor: int
    patch: int
    build: Optional[int] = None

    def __str__(self) -> str:
        """String representation of version."""
        if self.build is not None:
            return f"{self.major}.{self.minor}.{self.patch}.{self.build}"
        return f"{self.major}.{self.minor}.{self.patch}"

    def __gt__(self, other: 'Version') -> bool:
        """Compare versions (greater than)."""
        return (self.major, self.minor, self.patch, self.build or 0) > \
               (other.major, other.minor, other.patch, other.build or 0)

    def __lt__(self, other: 'Version') -> bool:
        """Compare versions (less than)."""
        return (self.major, self.minor, self.patch, self.build or 0) < \
               (other.major, other.minor, other.patch, other.build or 0)

    def __eq__(self, other: object) -> bool:
        """Compare versions (equals)."""
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.build or 0) == \
               (other.major, other.minor, other.patch, other.build or 0)

    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        """
        Parse version from string.

        Args:
            version_str: Version string (e.g., "1.2.3" or "1.2.3.4")

        Returns:
            Version object

        Example:
            >>> Version.from_string("1.2.3")
            Version(major=1, minor=2, patch=3, build=None)
        """
        parts = version_str.split('.')
        if len(parts) < 3:
            raise ValueError(f"Invalid version string: {version_str}")

        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
        build = int(parts[3]) if len(parts) > 3 else None

        return cls(major=major, minor=minor, patch=patch, build=build)


@dataclass
class Plugin:
    """Core plugin data model."""

    # Identification
    name: str
    publisher: str
    plugin_id: Optional[str] = None

    # Classification
    plugin_type: PluginType = PluginType.UNKNOWN
    category: PluginCategory = PluginCategory.OTHER

    # Version
    version: Optional[Version] = None

    # Paths
    file_path: Optional[Path] = None
    install_date: Optional[datetime] = None

    # Registry
    registry_key: Optional[str] = None

    # License
    license_status: str = "Unknown"  # "Verified", "Pending", "Missing", "Expired"
    license_path: Optional[Path] = None

    # Metadata
    file_size: int = 0
    file_hash: str = ""
    architecture: str = "x64"  # "x64", "x86", "ARM"

    # Additional Info
    description: Optional[str] = None
    website: Optional[str] = None
    support_url: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for CSV/JSON export.

        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'publisher': self.publisher,
            'plugin_id': self.plugin_id,
            'type': self.plugin_type.value,
            'category': self.category.value,
            'version': str(self.version) if self.version else "Unknown",
            'file_path': str(self.file_path) if self.file_path else "",
            'registry_key': self.registry_key or "",
            'license_status': self.license_status,
            'license_path': str(self.license_path) if self.license_path else "",
            'architecture': self.architecture,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2),
            'file_hash': self.file_hash,
            'install_date': self.install_date.isoformat() if self.install_date else "",
            'description': self.description or "",
            'website': self.website or "",
        }

    def get_display_name(self) -> str:
        """
        Get display name for plugin.

        Returns:
            Formatted display name
        """
        if self.version:
            return f"{self.name} v{self.version} by {self.publisher}"
        return f"{self.name} by {self.publisher}"

    def is_licensed(self) -> bool:
        """Check if plugin is properly licensed."""
        return self.license_status.lower() == "verified"

    def __repr__(self) -> str:
        """String representation."""
        return f"Plugin(name='{self.name}', publisher='{self.publisher}', type={self.plugin_type.value})"

    def __str__(self) -> str:
        """User-friendly string representation."""
        return self.get_display_name()
