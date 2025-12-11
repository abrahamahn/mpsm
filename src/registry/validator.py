"""Registry path validation."""

from pathlib import Path
from typing import Dict, List, Tuple

from ..core.logger import get_logger
from .registry_reader import RegistryReader


class PathValidator:
    """Validates registry path changes."""

    def __init__(self):
        """Initialize path validator."""
        self.logger = get_logger()
        self.reader = RegistryReader()

    def validate_path_exists(self, path: str) -> bool:
        """
        Validate that a path exists on filesystem.

        Args:
            path: File or directory path

        Returns:
            True if path exists
        """
        try:
            path_obj = Path(path)
            exists = path_obj.exists()

            if not exists:
                self.logger.warning(f"Path does not exist: {path}")

            return exists

        except Exception as e:
            self.logger.error(f"Error validating path {path}: {e}")
            return False

    def validate_plugin_loadable(self, plugin_path: str) -> bool:
        """
        Validate that a plugin file is loadable.

        Args:
            plugin_path: Path to plugin file

        Returns:
            True if plugin appears loadable

        Note:
            This is a basic check. Full validation would require
            loading the plugin in a host application.
        """
        try:
            path = Path(plugin_path)

            # Check file exists
            if not path.exists():
                self.logger.warning(f"Plugin file not found: {plugin_path}")
                return False

            # Check file extension
            valid_extensions = [".dll", ".vst3", ".aax", ".clap"]
            if path.suffix.lower() not in valid_extensions:
                self.logger.warning(f"Invalid plugin extension: {path.suffix}")
                return False

            # Check file is not empty
            if path.stat().st_size == 0:
                self.logger.warning(f"Plugin file is empty: {plugin_path}")
                return False

            # Basic validation passed
            return True

        except Exception as e:
            self.logger.error(f"Error validating plugin {plugin_path}: {e}")
            return False

    def validate_registry_paths(self) -> List[Dict[str, str]]:
        """
        Validate all registry paths point to existing files.

        Returns:
            List of broken path entries
        """
        broken_paths = []

        self.logger.info("Validating registry paths...")

        # Get all registry entries
        all_entries = self.reader.scan_all_music_production_keys()

        for key_path, entries in all_entries.items():
            for entry in entries:
                if entry.is_path_value():
                    # Check if path exists
                    if not self.validate_path_exists(entry.value_data):
                        broken_paths.append(
                            {
                                "key_path": key_path,
                                "value_name": entry.value_name,
                                "path": entry.value_data,
                                "reason": "Path does not exist",
                            }
                        )

        self.logger.info(f"Found {len(broken_paths)} broken registry paths")
        return broken_paths

    def find_orphaned_registry_entries(
        self, known_plugin_paths: List[Path]
    ) -> List[Dict[str, str]]:
        """
        Find registry entries that point to non-existent plugins.

        Args:
            known_plugin_paths: List of known valid plugin paths

        Returns:
            List of orphaned registry entries
        """
        orphaned = []
        known_paths_set = {str(p).lower() for p in known_plugin_paths}

        # Get all registry entries
        all_entries = self.reader.scan_all_music_production_keys()

        for key_path, entries in all_entries.items():
            for entry in entries:
                if entry.is_path_value():
                    entry_path = entry.value_data.lower()

                    # Check if this path is in our known plugins
                    if entry_path not in known_paths_set:
                        # Check if file actually exists
                        if not Path(entry_path).exists():
                            orphaned.append(
                                {
                                    "key_path": key_path,
                                    "value_name": entry.value_name,
                                    "path": entry.value_data,
                                    "reason": "Plugin file not found",
                                }
                            )

        self.logger.info(f"Found {len(orphaned)} orphaned registry entries")
        return orphaned

    def generate_validation_report(self) -> Dict[str, any]:
        """
        Generate comprehensive validation report.

        Returns:
            Dictionary with validation results
        """
        self.logger.info("Generating validation report...")

        report = {
            "timestamp": str(Path.ctime),
            "broken_paths": self.validate_registry_paths(),
            "summary": {},
        }

        # Add summary statistics
        report["summary"] = {
            "total_broken_paths": len(report["broken_paths"]),
            "issues_found": len(report["broken_paths"]) > 0,
        }

        return report

    def suggest_path_fixes(
        self, broken_path: str, known_plugins: List[Path]
    ) -> List[Tuple[Path, float]]:
        """
        Suggest possible fixes for broken registry path.

        Args:
            broken_path: Broken path from registry
            known_plugins: List of known valid plugin paths

        Returns:
            List of (suggested_path, confidence_score) tuples

        Note:
            This uses simple heuristics based on filename matching.
            Confidence score is 0.0 to 1.0.
        """
        suggestions = []

        # Extract filename from broken path
        broken_filename = Path(broken_path).name.lower()

        for plugin_path in known_plugins:
            plugin_filename = plugin_path.name.lower()

            # Exact filename match
            if plugin_filename == broken_filename:
                suggestions.append((plugin_path, 1.0))

            # Partial match
            elif broken_filename in plugin_filename or plugin_filename in broken_filename:
                # Calculate simple similarity score
                score = len(set(broken_filename) & set(plugin_filename)) / max(
                    len(broken_filename), len(plugin_filename)
                )
                suggestions.append((plugin_path, score))

        # Sort by confidence score
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions[:5]  # Return top 5 suggestions
