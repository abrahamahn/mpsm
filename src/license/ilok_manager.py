"""iLok license manager integration."""

import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import platform

from ..core.logger import get_logger
from ..models.license import iLokLicense, License, LicenseFormat, LicenseType, LicenseStatus


IS_WINDOWS = platform.system() == 'Windows'


class iLokManager:
    """Manages integration with PACE iLok License Manager."""

    # Common iLok installation paths
    ILOK_PATHS_WINDOWS = [
        r"C:\Program Files (x86)\PACE Anti-Piracy\iLok License Manager",
        r"C:\Program Files\PACE Anti-Piracy\iLok License Manager",
    ]

    ILOK_PATHS_MAC = [
        "/Applications/iLok License Manager.app",
    ]

    # iLok License Manager executable names
    ILOK_EXECUTABLES = [
        "iLokLicenseManager.exe",  # Windows
        "iLok License Manager",     # Mac
    ]

    def __init__(self):
        """Initialize iLok manager."""
        self.logger = get_logger()
        self.ilok_path: Optional[Path] = None
        self.is_installed = False

        # Detect iLok installation
        self._detect_ilok_installation()

    def _detect_ilok_installation(self) -> None:
        """Detect if iLok License Manager is installed."""
        if IS_WINDOWS:
            search_paths = self.ILOK_PATHS_WINDOWS
        else:
            search_paths = self.ILOK_PATHS_MAC

        for path_str in search_paths:
            path = Path(path_str)
            if path.exists():
                self.ilok_path = path
                self.is_installed = True
                self.logger.info(f"iLok License Manager found at: {path}")
                return

        self.logger.info("iLok License Manager not found")
        self.is_installed = False

    def get_ilok_licenses(self) -> List[iLokLicense]:
        """
        Get all iLok licenses from PACE system.

        Returns:
            List of iLokLicense objects

        Note:
            This requires iLok License Manager to be installed.
            On Windows, this may require elevated permissions.
        """
        if not self.is_installed:
            self.logger.warning("iLok License Manager not installed")
            return []

        licenses = []

        # Try to get licenses from iLok cloud folder
        cloud_licenses = self._get_cloud_licenses()
        licenses.extend(cloud_licenses)

        # Try to get licenses from local iLok devices
        device_licenses = self._get_device_licenses()
        licenses.extend(device_licenses)

        # Try to get computer-activated licenses
        computer_licenses = self._get_computer_licenses()
        licenses.extend(computer_licenses)

        self.logger.info(f"Found {len(licenses)} iLok licenses")
        return licenses

    def _get_cloud_licenses(self) -> List[iLokLicense]:
        """
        Get licenses stored in iLok Cloud.

        Returns:
            List of cloud-based licenses
        """
        # iLok Cloud licenses are typically stored in user AppData
        if IS_WINDOWS:
            ilok_data_path = Path.home() / "AppData" / "Local" / "PACE Anti-Piracy" / "Eden"
        else:
            ilok_data_path = Path.home() / "Library" / "Application Support" / "PACE Anti-Piracy" / "Eden"

        licenses = []

        if ilok_data_path.exists():
            self.logger.debug(f"Checking iLok Cloud data at: {ilok_data_path}")

            # Look for license files
            for lic_file in ilok_data_path.rglob("*.ilic"):
                try:
                    license = self._parse_ilok_license_file(lic_file)
                    if license:
                        license.location = "Cloud"
                        licenses.append(license)
                except Exception as e:
                    self.logger.warning(f"Could not parse iLok license file {lic_file}: {e}")

        return licenses

    def _get_device_licenses(self) -> List[iLokLicense]:
        """
        Get licenses stored on physical iLok devices.

        Returns:
            List of device-based licenses
        """
        # This would require iLok License Manager API or CLI
        # For now, return empty list
        # Future: Use iLok CLI tools if available
        return []

    def _get_computer_licenses(self) -> List[iLokLicense]:
        """
        Get licenses activated to this computer.

        Returns:
            List of computer-activated licenses
        """
        # Computer-activated licenses are stored locally
        if IS_WINDOWS:
            computer_lic_path = Path.home() / "AppData" / "Local" / "PACE Anti-Piracy" / "Repository"
        else:
            computer_lic_path = Path.home() / "Library" / "Application Support" / "PACE Anti-Piracy" / "Repository"

        licenses = []

        if computer_lic_path.exists():
            self.logger.debug(f"Checking computer licenses at: {computer_lic_path}")

            for lic_file in computer_lic_path.rglob("*.ilic"):
                try:
                    license = self._parse_ilok_license_file(lic_file)
                    if license:
                        license.location = "Computer"
                        licenses.append(license)
                except Exception as e:
                    self.logger.warning(f"Could not parse iLok license file {lic_file}: {e}")

        return licenses

    def _parse_ilok_license_file(self, file_path: Path) -> Optional[iLokLicense]:
        """
        Parse an iLok license file.

        Args:
            file_path: Path to .ilic file

        Returns:
            iLokLicense object or None
        """
        # iLok license files are binary format
        # Without official documentation, we can only extract basic info
        # For now, create basic license object with file info

        try:
            # Extract product name from filename or parent folder
            product_name = file_path.stem
            publisher = "Unknown"

            # Try to extract publisher from path
            path_parts = file_path.parts
            for part in path_parts:
                if any(vendor in part for vendor in [
                    'Waves', 'iZotope', 'FabFilter', 'Native Instruments',
                    'Plugin Alliance', 'Slate Digital', 'Softube'
                ]):
                    publisher = part
                    break

            license = iLokLicense(
                license_id=file_path.stem,
                product_name=product_name,
                publisher=publisher,
                location="Unknown",
                license_type="Unknown",
            )

            return license

        except Exception as e:
            self.logger.warning(f"Failed to parse iLok license {file_path}: {e}")
            return None

    def convert_to_license(self, ilok_license: iLokLicense) -> License:
        """
        Convert iLokLicense to standard License object.

        Args:
            ilok_license: iLokLicense to convert

        Returns:
            License object
        """
        return License(
            license_id=ilok_license.license_id,
            name=ilok_license.product_name,
            owner=ilok_license.product_name,
            publisher=ilok_license.publisher,
            license_type=LicenseType.UNKNOWN,
            license_format=LicenseFormat.ILOK,
            status=LicenseStatus.ACTIVE,
            ilok_account=None,  # Would need to query iLok API
            ilok_location=ilok_license.location,
            expiration_date=ilok_license.expiration_date,
            last_verified=datetime.now(),
        )

    def get_ilok_info(self) -> Dict[str, any]:
        """
        Get information about iLok installation.

        Returns:
            Dictionary with iLok info
        """
        info = {
            'installed': self.is_installed,
            'installation_path': str(self.ilok_path) if self.ilok_path else None,
            'version': self._get_ilok_version(),
        }

        return info

    def _get_ilok_version(self) -> Optional[str]:
        """
        Get iLok License Manager version.

        Returns:
            Version string or None
        """
        # Try to get version from iLok executable
        if not self.is_installed or not self.ilok_path:
            return None

        # This would require running iLok CLI with --version
        # For now, return None
        return None

    def check_ilok_devices(self) -> List[Dict[str, str]]:
        """
        Check for connected iLok USB devices.

        Returns:
            List of connected iLok devices
        """
        devices = []

        # On Windows, check for iLok USB devices in Device Manager
        # On Mac, check for iLok devices in system_profiler
        # For now, return empty list

        return devices

    def get_ilok_cloud_session(self) -> Optional[str]:
        """
        Get current iLok Cloud session info.

        Returns:
            Session info or None
        """
        # Would require iLok API access
        return None

    def validate_ilok_license(self, license_id: str) -> bool:
        """
        Validate an iLok license.

        Args:
            license_id: License ID to validate

        Returns:
            True if license is valid
        """
        # Would require iLok API or CLI
        # For now, return False
        return False

    def export_ilok_licenses(self, output_path: Path) -> bool:
        """
        Export iLok license information to file.

        Args:
            output_path: Path to export to

        Returns:
            True if successful
        """
        try:
            licenses = self.get_ilok_licenses()

            # Convert to JSON
            licenses_data = [lic.to_dict() for lic in licenses]

            with open(output_path, 'w') as f:
                json.dump({
                    'export_date': datetime.now().isoformat(),
                    'total_licenses': len(licenses),
                    'licenses': licenses_data,
                }, f, indent=2)

            self.logger.info(f"Exported {len(licenses)} iLok licenses to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export iLok licenses: {e}")
            return False
