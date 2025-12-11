"""Plugin installation consolidator."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..core.config import ConfigManager
from ..core.exceptions import FileOperationException
from ..core.logger import get_logger
from ..models.folder import PluginInstallation
from ..models.plugin import Plugin
from ..models.scan_result import ComprehensiveScanResult
from .file_mover import FileMover, MoveOperation
from .structure_builder import StructureBuilder


@dataclass
class ConsolidationPlan:
    """Plan for consolidating plugin installations."""

    plan_id: str
    created_date: datetime
    total_plugins: int
    total_folders: int
    total_size_bytes: int
    move_operations: List[tuple] = field(default_factory=list)  # (source, dest, is_folder)
    registry_updates: List[Dict] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "plan_id": self.plan_id,
            "created_date": self.created_date.isoformat(),
            "total_plugins": self.total_plugins,
            "total_folders": self.total_folders,
            "total_size_mb": round(self.total_size_bytes / (1024 * 1024), 2),
            "total_size_gb": round(self.total_size_bytes / (1024**3), 2),
            "operations_count": len(self.move_operations),
            "registry_updates_count": len(self.registry_updates),
            "conflicts_count": len(self.conflicts),
            "warnings_count": len(self.warnings),
        }

    def get_summary(self) -> str:
        """Generate summary string."""
        summary = f"""
Consolidation Plan: {self.plan_id}
==================================
Created: {self.created_date.strftime('%Y-%m-%d %H:%M:%S')}

Components:
- Plugins: {self.total_plugins}
- Data Folders: {self.total_folders}
- Total Size: {self.total_size_bytes / (1024**3):.2f} GB

Operations:
- File/Folder Moves: {len(self.move_operations)}
- Registry Updates: {len(self.registry_updates)}

Issues:
- Conflicts: {len(self.conflicts)}
- Warnings: {len(self.warnings)}
"""
        return summary


@dataclass
class ConsolidationResult:
    """Results from consolidation execution."""

    plan_id: str
    execution_date: datetime
    duration_seconds: float
    operations_attempted: int
    operations_successful: int
    operations_failed: int
    registry_updates_successful: int
    registry_updates_failed: int
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "plan_id": self.plan_id,
            "execution_date": self.execution_date.isoformat(),
            "duration_seconds": round(self.duration_seconds, 2),
            "operations_attempted": self.operations_attempted,
            "operations_successful": self.operations_successful,
            "operations_failed": self.operations_failed,
            "registry_updates_successful": self.registry_updates_successful,
            "registry_updates_failed": self.registry_updates_failed,
            "success_rate": round(
                (self.operations_successful / max(self.operations_attempted, 1)) * 100, 1
            ),
        }


class Consolidator:
    """Consolidates complete plugin installations."""

    def __init__(self, config: Optional[ConfigManager] = None, dry_run: bool = True):
        """
        Initialize consolidator.

        Args:
            config: Configuration manager
            dry_run: Don't actually move files, just plan
        """
        self.logger = get_logger()
        self.config = config or ConfigManager()
        self.dry_run = dry_run

        self.structure_builder = StructureBuilder(self.config)
        self.file_mover = FileMover(dry_run=dry_run)

    def plan_consolidation(self, scan_result: ComprehensiveScanResult) -> ConsolidationPlan:
        """
        Create consolidation plan from scan results.

        Args:
            scan_result: Scan results

        Returns:
            ConsolidationPlan
        """
        import uuid

        plan_id = str(uuid.uuid4())[:8]

        self.logger.info(f"Creating consolidation plan {plan_id}...")

        plan = ConsolidationPlan(
            plan_id=plan_id,
            created_date=datetime.now(),
            total_plugins=len(scan_result.plugins),
            total_folders=len(scan_result.data_folders),
            total_size_bytes=0,
        )

        # Plan moves for each plugin
        for plugin in scan_result.plugins:
            if not plugin.file_path or not plugin.file_path.exists():
                plan.warnings.append(f"Plugin file not found: {plugin.name}")
                continue

            # Determine target location
            target_path = self.structure_builder.map_plugin_file_location(plugin)

            # Check for conflicts
            if target_path.exists():
                plan.conflicts.append(f"Destination already exists: {target_path}")
                continue

            # Add to operations
            plan.move_operations.append((plugin.file_path, target_path, False))
            plan.total_size_bytes += plugin.file_size

            # Plan registry update if plugin has registry key
            if plugin.registry_key:
                plan.registry_updates.append(
                    {
                        "key_path": plugin.registry_key,
                        "value_name": "Path",  # Common value name
                        "old_path": str(plugin.file_path),
                        "new_path": str(target_path),
                    }
                )

        # Plan moves for data folders
        for folder in scan_result.data_folders:
            if not folder.path.exists():
                plan.warnings.append(f"Folder not found: {folder.path}")
                continue

            # Determine target location
            plugin_name = folder.parent_plugin or folder.owner or "Unknown"
            target_path = self.structure_builder.map_data_folder_location(folder, plugin_name)

            # Check for conflicts
            if target_path.exists():
                plan.conflicts.append(f"Destination already exists: {target_path}")
                continue

            # Add to operations
            plan.move_operations.append((folder.path, target_path, True))
            plan.total_size_bytes += folder.total_size

        self.logger.info(f"Plan created: {len(plan.move_operations)} operations")

        # Check for sufficient disk space
        if not self.structure_builder.verify_sufficient_space(plan.total_size_bytes):
            plan.conflicts.append("Insufficient disk space for consolidation")

        return plan

    def execute_consolidation(
        self, plan: ConsolidationPlan, create_backup: bool = True
    ) -> ConsolidationResult:
        """
        Execute consolidation plan.

        Args:
            plan: ConsolidationPlan to execute
            create_backup: Create backups before moving

        Returns:
            ConsolidationResult
        """
        import time

        self.logger.info(f"Executing consolidation plan {plan.plan_id}...")

        start_time = time.time()

        result = ConsolidationResult(
            plan_id=plan.plan_id,
            execution_date=datetime.now(),
            duration_seconds=0,
            operations_attempted=len(plan.move_operations),
            operations_successful=0,
            operations_failed=0,
            registry_updates_successful=0,
            registry_updates_failed=0,
        )

        # Check for conflicts
        if plan.conflicts:
            self.logger.error(f"Plan has {len(plan.conflicts)} conflicts - aborting")
            result.errors.append(f"{len(plan.conflicts)} conflicts detected")
            return result

        # Create target structure
        try:
            self.structure_builder.create_structure()
        except Exception as e:
            self.logger.error(f"Failed to create target structure: {e}")
            result.errors.append(f"Structure creation failed: {e}")
            return result

        # Execute move operations
        batch_result = self.file_mover.batch_move(plan.move_operations)

        result.operations_successful = batch_result.successful
        result.operations_failed = batch_result.failed

        # Execute registry updates (if not dry run)
        if not self.dry_run and plan.registry_updates:
            result.registry_updates_successful, result.registry_updates_failed = (
                self._execute_registry_updates(plan.registry_updates)
            )

        result.duration_seconds = time.time() - start_time

        if result.operations_failed > 0:
            self.logger.warning(f"Consolidation completed with {result.operations_failed} failures")
        else:
            self.logger.info(
                f"✓ Consolidation completed successfully in {result.duration_seconds:.2f}s"
            )

        return result

    def _execute_registry_updates(self, updates: List[Dict]) -> tuple[int, int]:
        """
        Execute registry updates.

        Args:
            updates: List of registry update dictionaries

        Returns:
            Tuple of (successful_count, failed_count)
        """
        try:
            from ..registry.manager import RegistryManager

            manager = RegistryManager(auto_backup=True)
            results = manager.batch_update(updates, description="Plugin consolidation")

            successful = sum(1 for r in results.values() if r.updated)
            failed = len(results) - successful

            return successful, failed

        except Exception as e:
            self.logger.error(f"Registry updates failed: {e}")
            return 0, len(updates)

    def create_installation_plan(self, installation: PluginInstallation) -> Dict[str, Path]:
        """
        Create plan to move an entire plugin installation.

        Args:
            installation: PluginInstallation object

        Returns:
            Dictionary mapping old path to new path

        Example:
            {
                'plugin_file': new_path,
                'standalone': new_path,
                'presets': new_path,
                ...
            }
        """
        plan = {}

        # Map plugin files
        for i, plugin_file in enumerate(installation.plugin_files):
            # Create a temporary Plugin object to get target location
            from ..models.plugin import Plugin, PluginType

            plugin = Plugin(
                name=installation.plugin_name,
                publisher=installation.publisher,
                file_path=plugin_file,
            )

            # Detect plugin type from extension
            if plugin_file.suffix.lower() == ".vst3":
                plugin.plugin_type = PluginType.VST3
            elif plugin_file.suffix.lower() == ".dll":
                plugin.plugin_type = PluginType.VST2
            elif plugin_file.suffix.lower() == ".aax":
                plugin.plugin_type = PluginType.AAX

            target = self.structure_builder.map_plugin_file_location(plugin)
            plan[f"plugin_file_{i}"] = target

        # Map executables
        for i, exe_file in enumerate(installation.executables):
            from ..models.application import Application, ApplicationType

            app = Application(
                name=installation.plugin_name,
                publisher=installation.publisher,
                app_type=ApplicationType.STANDALONE,
                executable_path=exe_file,
            )

            target = self.structure_builder.map_application_location(app)
            plan[f"executable_{i}"] = target / exe_file.name

        # Map data folders
        for i, data_folder in enumerate(installation.data_folders):
            target = self.structure_builder.map_data_folder_location(
                data_folder, installation.plugin_name
            )
            plan[f"data_folder_{i}"] = target

        return plan

    def validate_plan(self, plan: ConsolidationPlan) -> List[str]:
        """
        Validate consolidation plan.

        Args:
            plan: ConsolidationPlan to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check for conflicts
        if plan.conflicts:
            errors.extend(plan.conflicts)

        # Check disk space
        if not self.structure_builder.verify_sufficient_space(plan.total_size_bytes):
            errors.append("Insufficient disk space")

        # Validate target structure
        structure_errors = self.structure_builder.validate_structure()
        errors.extend(structure_errors)

        return errors

    def estimate_consolidation_time(self, plan: ConsolidationPlan) -> float:
        """
        Estimate time to execute consolidation.

        Args:
            plan: ConsolidationPlan

        Returns:
            Estimated time in seconds
        """
        return self.file_mover.estimate_move_time(plan.total_size_bytes)
