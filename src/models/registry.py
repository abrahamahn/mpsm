"""Registry entry data model."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class RegistryEntry:
    """Registry entry data model."""

    # Key info
    key_path: str  # Full registry path
    value_name: str
    value_data: str
    value_type: str = "REG_SZ"  # REG_SZ, REG_DWORD, REG_BINARY, etc.

    # Relationships
    related_file: Optional[Path] = None
    related_plugin: Optional[str] = None
    related_application: Optional[str] = None

    # Metadata
    hive: str = "HKLM"  # HKLM, HKCU, HKCR, etc.
    category: str = "Unknown"  # "VST Path", "Install Location", "License", etc.
    last_modified: Optional[datetime] = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for export.

        Returns:
            Dictionary representation
        """
        return {
            'key_path': self.key_path,
            'value_name': self.value_name,
            'value_data': self.value_data,
            'value_type': self.value_type,
            'hive': self.hive,
            'category': self.category,
            'related_file': str(self.related_file) if self.related_file else "",
            'related_plugin': self.related_plugin or "",
            'related_application': self.related_application or "",
            'last_modified': self.last_modified.isoformat() if self.last_modified else "",
        }

    def get_full_path(self) -> str:
        """
        Get full registry path including value name.

        Returns:
            Full registry path
        """
        return f"{self.key_path}\\{self.value_name}"

    def is_path_value(self) -> bool:
        """Check if this entry contains a file path."""
        if not self.value_data:
            return False

        # Check if value looks like a path
        return ('\\' in self.value_data or '/' in self.value_data) and \
               (self.value_data.startswith('C:\\') or
                self.value_data.startswith('D:\\') or
                ':\\' in self.value_data)

    def __repr__(self) -> str:
        """String representation."""
        return f"RegistryEntry(key='{self.key_path}', value='{self.value_name}')"

    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.key_path}\\{self.value_name} = {self.value_data}"


@dataclass
class RegistryBackup:
    """Registry backup metadata."""

    backup_id: str
    backup_date: datetime
    backup_path: Path
    keys_backed_up: list[str]
    registry_file: Path

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'backup_id': self.backup_id,
            'backup_date': self.backup_date.isoformat(),
            'backup_path': str(self.backup_path),
            'keys_count': len(self.keys_backed_up),
            'keys_backed_up': ', '.join(self.keys_backed_up[:5]) + ('...' if len(self.keys_backed_up) > 5 else ''),
            'registry_file': str(self.registry_file),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"RegistryBackup(id='{self.backup_id}', keys={len(self.keys_backed_up)})"


@dataclass
class PathUpdate:
    """Registry path update operation."""

    key_path: str
    value_name: str
    old_path: str
    new_path: str
    updated: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'key_path': self.key_path,
            'value_name': self.value_name,
            'old_path': self.old_path,
            'new_path': self.new_path,
            'updated': self.updated,
            'error': self.error or "",
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "✓" if self.updated else "✗"
        return f"PathUpdate({status} {self.key_path}\\{self.value_name})"
