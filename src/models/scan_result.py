"""Scan result data models."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import pandas as pd

from .plugin import Plugin
from .application import Application
from .folder import DataFolder, PluginInstallation


@dataclass
class ComprehensiveScanResult:
    """Complete scan result containing ALL discovered items."""

    scan_id: str
    scan_date: datetime
    scan_duration: float = 0.0  # seconds

    # Discovered items
    plugins: List[Plugin] = field(default_factory=list)
    applications: List[Application] = field(default_factory=list)
    data_folders: List[DataFolder] = field(default_factory=list)
    plugin_installations: List[PluginInstallation] = field(default_factory=list)
    # daws: List[DAW] = field(default_factory=list)  # TODO: Implement DAW model
    # licenses: List[License] = field(default_factory=list)  # TODO: Implement License model
    # registry_entries: List[RegistryEntry] = field(default_factory=list)  # TODO: Implement RegistryEntry model

    # Statistics
    total_files_scanned: int = 0
    total_plugins_found: int = 0
    total_applications_found: int = 0
    total_folders_found: int = 0
    total_size_gb: float = 0.0
    total_registry_entries: int = 0

    # Issues
    broken_links: List[Path] = field(default_factory=list)
    missing_licenses: List[str] = field(default_factory=list)
    registry_mismatches: List[dict] = field(default_factory=list)
    orphaned_folders: List[Path] = field(default_factory=list)
    orphaned_registry: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate statistics after initialization."""
        self.calculate_statistics()

    def calculate_statistics(self) -> None:
        """Calculate scan statistics."""
        self.total_plugins_found = len(self.plugins)
        self.total_applications_found = len(self.applications)
        self.total_folders_found = len(self.data_folders)

        # Calculate total size
        total_size_bytes = 0
        for plugin in self.plugins:
            total_size_bytes += plugin.file_size
        for folder in self.data_folders:
            total_size_bytes += folder.total_size

        self.total_size_gb = round(total_size_bytes / (1024 ** 3), 2)

    def to_dataframe(self, item_type: str = 'plugins') -> pd.DataFrame:
        """
        Convert to pandas DataFrame for export.

        Args:
            item_type: Type of items to export ('plugins', 'applications', 'folders', etc.)

        Returns:
            DataFrame with scan results
        """
        if item_type == 'plugins':
            return pd.DataFrame([p.to_dict() for p in self.plugins])
        elif item_type == 'applications':
            return pd.DataFrame([a.to_dict() for a in self.applications])
        elif item_type == 'folders':
            return pd.DataFrame([f.to_dict() for f in self.data_folders])
        elif item_type == 'installations':
            return pd.DataFrame([i.to_dict() for i in self.plugin_installations])
        else:
            raise ValueError(f"Unknown item type: {item_type}")

    def export_csv(self, output_dir: Path) -> None:
        """
        Export scan results to CSV files.

        Args:
            output_dir: Directory to save CSV files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export plugins
        if self.plugins:
            plugins_df = self.to_dataframe('plugins')
            plugins_df.to_csv(output_dir / 'plugins.csv', index=False)

        # Export applications
        if self.applications:
            apps_df = self.to_dataframe('applications')
            apps_df.to_csv(output_dir / 'applications.csv', index=False)

        # Export folders
        if self.data_folders:
            folders_df = self.to_dataframe('folders')
            folders_df.to_csv(output_dir / 'folders.csv', index=False)

        # Export installations
        if self.plugin_installations:
            installations_df = self.to_dataframe('installations')
            installations_df.to_csv(output_dir / 'installations.csv', index=False)

        # Export summary
        summary_df = pd.DataFrame([self.get_summary_dict()])
        summary_df.to_csv(output_dir / 'summary.csv', index=False)

    def export_excel(self, output_path: Path) -> None:
        """
        Export comprehensive scan results to Excel with multiple sheets.

        Args:
            output_path: Path to save Excel file

        Sheets:
            - Plugins
            - Applications
            - Folders
            - Installations
            - Issues
            - Statistics
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Export plugins
            if self.plugins:
                plugins_df = self.to_dataframe('plugins')
                plugins_df.to_excel(writer, sheet_name='Plugins', index=False)

            # Export applications
            if self.applications:
                apps_df = self.to_dataframe('applications')
                apps_df.to_excel(writer, sheet_name='Applications', index=False)

            # Export folders
            if self.data_folders:
                folders_df = self.to_dataframe('folders')
                folders_df.to_excel(writer, sheet_name='Folders', index=False)

            # Export installations
            if self.plugin_installations:
                installations_df = self.to_dataframe('installations')
                installations_df.to_excel(writer, sheet_name='Installations', index=False)

            # Export issues
            issues_data = {
                'Broken Links': [str(p) for p in self.broken_links],
                'Missing Licenses': self.missing_licenses,
                'Orphaned Folders': [str(p) for p in self.orphaned_folders],
                'Orphaned Registry': self.orphaned_registry,
            }
            # Pad lists to same length
            max_len = max(len(v) for v in issues_data.values()) if issues_data else 0
            for key in issues_data:
                issues_data[key] += [''] * (max_len - len(issues_data[key]))

            issues_df = pd.DataFrame(issues_data)
            issues_df.to_excel(writer, sheet_name='Issues', index=False)

            # Export statistics
            stats_df = pd.DataFrame([self.get_summary_dict()])
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)

    def get_summary_dict(self) -> dict:
        """
        Get summary as dictionary.

        Returns:
            Dictionary with scan summary
        """
        return {
            'scan_id': self.scan_id,
            'scan_date': self.scan_date.isoformat(),
            'scan_duration_seconds': round(self.scan_duration, 2),
            'total_plugins': self.total_plugins_found,
            'total_applications': self.total_applications_found,
            'total_folders': self.total_folders_found,
            'total_installations': len(self.plugin_installations),
            'total_size_gb': self.total_size_gb,
            'total_files_scanned': self.total_files_scanned,
            'broken_links_count': len(self.broken_links),
            'missing_licenses_count': len(self.missing_licenses),
            'orphaned_folders_count': len(self.orphaned_folders),
            'orphaned_registry_count': len(self.orphaned_registry),
        }

    def generate_summary(self) -> str:
        """
        Generate human-readable summary.

        Returns:
            Formatted summary string
        """
        summary = f"""
Scan Summary (ID: {self.scan_id})
================================
Scan Date: {self.scan_date.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {self.scan_duration:.2f}s

Components Found:
- Plugins: {self.total_plugins_found}
- Applications: {self.total_applications_found}
- Data Folders: {self.total_folders_found}
- Complete Installations: {len(self.plugin_installations)}
- Registry Entries: {self.total_registry_entries}

Total Size: {self.total_size_gb:.2f} GB
Files Scanned: {self.total_files_scanned:,}

Issues:
- Broken Links: {len(self.broken_links)}
- Missing Licenses: {len(self.missing_licenses)}
- Registry Mismatches: {len(self.registry_mismatches)}
- Orphaned Folders: {len(self.orphaned_folders)}
- Orphaned Registry Entries: {len(self.orphaned_registry)}
"""
        return summary

    def __repr__(self) -> str:
        """String representation."""
        return f"ComprehensiveScanResult(scan_id='{self.scan_id}', plugins={len(self.plugins)}, apps={len(self.applications)})"

    def __str__(self) -> str:
        """User-friendly string representation."""
        return self.generate_summary()
