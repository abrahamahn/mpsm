"""CLI command handlers for MPSM.

This module contains organized command handlers extracted from the main CLI.
Each command group has its own module for better separation of concerns.
"""

from .license_commands import license, license_ilok, license_info, license_scan, license_validate
from .organize_command import organize
from .registry_commands import (registry, registry_backup, registry_list, registry_restore,
                                registry_scan, registry_validate)
from .scan_command import scan

__all__ = [
    "scan",
    "organize",
    "registry",
    "registry_backup",
    "registry_restore",
    "registry_list",
    "registry_validate",
    "registry_scan",
    "license",
    "license_scan",
    "license_validate",
    "license_ilok",
    "license_info",
]
