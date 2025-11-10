"""Centralized vendor/publisher registry.

Single source of truth for all vendor information across MPSM.
Replaces duplicate vendor lists in publisher_identifier, folder_scanner,
and application_scanner modules.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

from ..core.logger import get_logger


class VendorRegistry:
    """
    Singleton registry for all vendor data.

    Loads vendor information from vendors.yaml and provides
    convenient access methods for different scanner modules.
    """

    _instance: Optional["VendorRegistry"] = None
    _vendors: Dict[str, Dict] = {}
    _loaded: bool = False

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize and load vendors if not already loaded."""
        if not self._loaded:
            self._load_vendors()
            VendorRegistry._loaded = True

    def _load_vendors(self):
        """Load vendors from YAML file."""
        logger = get_logger()
        vendor_file = Path(__file__).parent / "vendors.yaml"

        try:
            with open(vendor_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                VendorRegistry._vendors = data.get("vendors", {})

            logger.debug(f"Loaded {len(VendorRegistry._vendors)} vendors from registry")
        except FileNotFoundError:
            logger.error(f"Vendor registry file not found: {vendor_file}")
            VendorRegistry._vendors = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing vendor registry: {e}")
            VendorRegistry._vendors = {}

    # ========================================================================
    # PATTERN MATCHING METHODS
    # ========================================================================

    def find_vendor_by_pattern(self, text: str) -> Optional[str]:
        """
        Find vendor matching text patterns.

        Args:
            text: Text to search (file path, metadata, etc.)

        Returns:
            Vendor name if found, None otherwise

        Example:
            >>> registry.find_vendor_by_pattern("C:/Native Instruments/Kontakt")
            'Native Instruments'
        """
        text_lower = text.lower()

        for vendor_data in self._vendors.values():
            patterns = vendor_data.get("patterns", [])
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    return vendor_data.get("name", "Unknown")

        return None

    def find_vendor_by_folder(self, folder_name: str) -> Optional[str]:
        """
        Find vendor by folder name.

        Args:
            folder_name: Folder name to match

        Returns:
            Vendor name if found, None otherwise

        Example:
            >>> registry.find_vendor_by_folder("Native Instruments")
            'Native Instruments'
        """
        folder_lower = folder_name.lower()

        for vendor_data in self._vendors.values():
            folders = vendor_data.get("folders", [])
            for folder in folders:
                if folder.lower() == folder_lower or folder.lower() in folder_lower:
                    return vendor_data.get("name", "Unknown")

        return None

    # ========================================================================
    # DATA ACCESSOR METHODS
    # ========================================================================

    def get_patterns(self, vendor_key: str) -> List[str]:
        """
        Get path patterns for vendor.

        Args:
            vendor_key: Vendor key (e.g., 'native_instruments')

        Returns:
            List of search patterns
        """
        return self._vendors.get(vendor_key, {}).get("patterns", [])

    def get_folders(self, vendor_key: str) -> List[str]:
        """
        Get folder names for vendor.

        Args:
            vendor_key: Vendor key (e.g., 'native_instruments')

        Returns:
            List of expected folder names
        """
        return self._vendors.get(vendor_key, {}).get("folders", [])

    def get_executables(self, vendor_key: str) -> List[str]:
        """
        Get executable patterns for vendor (plugin managers, etc.).

        Args:
            vendor_key: Vendor key

        Returns:
            List of executable patterns
        """
        return self._vendors.get(vendor_key, {}).get("executables", [])

    def get_daw_executables(self, vendor_key: str) -> List[str]:
        """
        Get DAW executable patterns for vendor.

        Args:
            vendor_key: Vendor key

        Returns:
            List of DAW executable patterns
        """
        return self._vendors.get(vendor_key, {}).get("daw_executables", [])

    def get_standalone_executables(self, vendor_key: str) -> List[str]:
        """
        Get standalone plugin executable patterns for vendor.

        Args:
            vendor_key: Vendor key

        Returns:
            List of standalone executable patterns
        """
        return self._vendors.get(vendor_key, {}).get("standalone_executables", [])

    # ========================================================================
    # AGGREGATE DATA METHODS (for scanners)
    # ========================================================================

    def get_all_patterns(self) -> Dict[str, List[str]]:
        """
        Get all vendor patterns.

        Returns:
            Dictionary mapping vendor name to patterns

        Example:
            >>> patterns = registry.get_all_patterns()
            >>> patterns['Native Instruments']
            ['native instruments', 'komplete', 'kontakt']
        """
        result = {}
        for vendor_data in self._vendors.values():
            name = vendor_data.get("name")
            patterns = vendor_data.get("patterns", [])
            if name and patterns:
                result[name] = patterns
        return result

    def get_all_folders(self) -> Dict[str, List[str]]:
        """
        Get all vendor folders.

        Returns:
            Dictionary mapping vendor name to folder names
        """
        result = {}
        for vendor_data in self._vendors.values():
            name = vendor_data.get("name")
            folders = vendor_data.get("folders", [])
            if name and folders:
                result[name] = folders
        return result

    def get_all_daw_executables(self) -> Dict[str, List[str]]:
        """
        Get all DAW executables.

        Returns:
            Dictionary mapping DAW name to executable patterns
        """
        result = {}
        for vendor_data in self._vendors.values():
            name = vendor_data.get("name")
            daw_exes = vendor_data.get("daw_executables", [])
            if name and daw_exes:
                result[name] = daw_exes
        return result

    def get_all_plugin_manager_executables(self) -> Dict[str, List[str]]:
        """
        Get all plugin manager executables.

        Returns:
            Dictionary mapping manager name to executable patterns
        """
        result = {}
        for vendor_data in self._vendors.values():
            name = vendor_data.get("name")
            executables = vendor_data.get("executables", [])
            if name and executables:
                result[name] = executables
        return result

    def get_all_standalone_executables(self) -> Dict[str, List[str]]:
        """
        Get all standalone plugin executables.

        Returns:
            Dictionary mapping plugin name to executable patterns
        """
        result = {}
        for vendor_data in self._vendors.values():
            name = vendor_data.get("name")
            standalone_exes = vendor_data.get("standalone_executables", [])
            if name and standalone_exes:
                result[name] = standalone_exes
        return result

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def all_vendor_names(self) -> List[str]:
        """
        Get list of all vendor names.

        Returns:
            Sorted list of vendor display names
        """
        names = [v.get("name") for v in self._vendors.values() if v.get("name")]
        return sorted(names)

    def vendor_count(self) -> int:
        """
        Get total number of registered vendors.

        Returns:
            Number of vendors in registry
        """
        return len(self._vendors)

    def get_vendor_info(self, vendor_key: str) -> Optional[Dict]:
        """
        Get complete vendor information.

        Args:
            vendor_key: Vendor key

        Returns:
            Dictionary with all vendor data, or None if not found
        """
        return self._vendors.get(vendor_key)

    def search_vendors(self, query: str) -> List[str]:
        """
        Search for vendors by name or pattern.

        Args:
            query: Search query

        Returns:
            List of matching vendor names
        """
        query_lower = query.lower()
        matches = []

        for vendor_data in self._vendors.values():
            name = vendor_data.get("name", "")
            patterns = vendor_data.get("patterns", [])

            # Match against name
            if query_lower in name.lower():
                matches.append(name)
                continue

            # Match against patterns
            for pattern in patterns:
                if query_lower in pattern.lower():
                    matches.append(name)
                    break

        return sorted(set(matches))

    def reload(self):
        """Reload vendor data from YAML file."""
        VendorRegistry._loaded = False
        self._load_vendors()

    def __repr__(self) -> str:
        """String representation."""
        return f"VendorRegistry(vendors={self.vendor_count()})"


# Singleton instance - import this directly
vendor_registry = VendorRegistry()
