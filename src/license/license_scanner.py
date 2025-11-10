"""License file scanner."""

import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..core.config import ConfigManager
from ..core.logger import get_logger
from ..models.license import License, LicenseFormat, LicenseScanResult, LicenseStatus, LicenseType


class LicenseScanner:
    """Scans for license files and registry-based licenses."""

    # Known license file extensions
    LICENSE_EXTENSIONS = [
        ".lic",
        ".license",
        ".key",
        ".dat",  # Some vendors use .dat for licenses
        ".rsa",  # RSA key files
        ".nks",  # Native Instruments
        ".ilok",  # iLok license files
    ]

    # Known license file names (exact match)
    LICENSE_FILENAMES = [
        "license.txt",
        "license.dat",
        "license.xml",
        "activation.dat",
        "auth.dat",
        "serial.txt",
        "registration.txt",
    ]

    # Vendor-specific license file patterns
    VENDOR_PATTERNS = {
        "Native Instruments": ["*.nks", "*.nkc", "*.nki"],
        "iZotope": ["*.dat", "auth.dat"],
        "Waves": ["*.dat", "*.wpc"],
        "Arturia": ["*.arturia"],
        "FabFilter": ["*.license"],
        "iLok": ["*.ilok", "*.ilic"],
    }

    def __init__(self, config: Optional[ConfigManager] = None, max_workers: int = 4):
        """
        Initialize license scanner.

        Args:
            config: Configuration manager
            max_workers: Maximum parallel scan workers
        """
        self.logger = get_logger()
        self.config = config or ConfigManager()
        self.max_workers = max_workers

        # Discovered licenses
        self.licenses: List[License] = []

    def scan_for_licenses(self, scan_paths: Optional[List[str]] = None) -> LicenseScanResult:
        """
        Scan for all license files.

        Args:
            scan_paths: Paths to scan. If None, uses config paths.

        Returns:
            LicenseScanResult
        """
        start_time = datetime.now()
        self.licenses = []

        if scan_paths is None:
            scan_paths = self.config.get("scan.paths", [])

        self.logger.info(f"Scanning for licenses in {len(scan_paths)} paths...")

        # Scan each path for license files
        for path_str in scan_paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                self._scan_directory(path)
            else:
                self.logger.warning(f"Scan path does not exist: {path}")

        # Create scan result
        scan_duration = (datetime.now() - start_time).total_seconds()

        result = LicenseScanResult(
            scan_date=datetime.now(),
            total_licenses=len(self.licenses),
            licenses=self.licenses,
            scanned_paths=[Path(p) for p in scan_paths],
        )

        # Calculate statistics
        self._calculate_statistics(result)

        self.logger.info(
            f"License scan complete: {len(self.licenses)} licenses found in {scan_duration:.2f}s"
        )

        return result

    def _scan_directory(self, directory: Path) -> None:
        """
        Scan a directory for license files.

        Args:
            directory: Directory to scan
        """
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    # Check if file is a license file
                    if self._is_license_file(item):
                        license_obj = self._create_license_from_file(item)
                        if license_obj:
                            self.licenses.append(license_obj)

        except PermissionError:
            self.logger.warning(f"Permission denied scanning {directory}")
        except Exception as e:
            self.logger.error(f"Error scanning {directory}: {e}")

    def _is_license_file(self, file_path: Path) -> bool:
        """
        Check if file is a license file.

        Args:
            file_path: File to check

        Returns:
            True if file is a license file
        """
        # Check extension
        if file_path.suffix.lower() in self.LICENSE_EXTENSIONS:
            return True

        # Check filename
        if file_path.name.lower() in self.LICENSE_FILENAMES:
            return True

        # Check if 'license' in name
        if "license" in file_path.name.lower():
            return True

        # Check if 'activation' in name
        if "activation" in file_path.name.lower():
            return True

        return False

    def _create_license_from_file(self, file_path: Path) -> Optional[License]:
        """
        Create License object from file.

        Args:
            file_path: License file path

        Returns:
            License object or None
        """
        try:
            # Generate unique license ID
            license_id = str(uuid.uuid4())[:8]

            # Try to extract owner/publisher from path
            owner = self._extract_owner_from_path(file_path)
            publisher = owner  # Default to same as owner

            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)

            # Determine license format
            license_format = self._determine_license_format(file_path)

            # Try to read license key from file
            key_string = None
            activation_code = None
            if file_path.stat().st_size < 10 * 1024:  # Only read small files
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # Extract potential key strings (alphanumeric sequences)
                        if len(content) < 1000:  # Reasonable size
                            key_string = content.strip()
                except Exception:
                    pass

            license = License(
                license_id=license_id,
                name=owner,
                owner=owner,
                publisher=publisher,
                license_type=LicenseType.UNKNOWN,
                license_format=license_format,
                status=LicenseStatus.UNKNOWN,
                file_path=file_path,
                file_hash=file_hash,
                key_string=key_string,
                installation_date=datetime.fromtimestamp(file_path.stat().st_ctime),
                last_verified=datetime.now(),
            )

            return license

        except Exception as e:
            self.logger.warning(f"Could not create license from {file_path}: {e}")
            return None

    def _extract_owner_from_path(self, file_path: Path) -> str:
        """
        Extract owner/plugin name from file path.

        Args:
            file_path: File path

        Returns:
            Owner name
        """
        # Try to find vendor name in path
        path_parts = file_path.parts

        # Common vendor folder names
        vendors = [
            "Native Instruments",
            "iZotope",
            "Waves",
            "Arturia",
            "FabFilter",
            "Xfer",
            "Spectrasonics",
            "Serum",
            "Kontakt",
            "iLok",
            "Steinberg",
            "Image-Line",
            "FL Studio",
        ]

        for part in path_parts:
            # Check if part matches known vendor
            for vendor in vendors:
                if vendor.lower() in part.lower():
                    return vendor

        # If no vendor found, use parent folder name
        if len(path_parts) > 1:
            return path_parts[-2]

        return "Unknown"

    def _determine_license_format(self, file_path: Path) -> LicenseFormat:
        """
        Determine license format from file.

        Args:
            file_path: License file path

        Returns:
            LicenseFormat
        """
        ext = file_path.suffix.lower()

        if ext == ".ilok" or ext == ".ilic":
            return LicenseFormat.ILOK
        elif ext in [".lic", ".license", ".key"]:
            return LicenseFormat.FILE
        elif ext in [".dat"]:
            return LicenseFormat.FILE
        else:
            return LicenseFormat.FILE

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file.

        Args:
            file_path: File to hash

        Returns:
            Hex digest of hash
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.warning(f"Could not hash {file_path}: {e}")
            return ""

    def _calculate_statistics(self, result: LicenseScanResult) -> None:
        """
        Calculate statistics for scan result.

        Args:
            result: LicenseScanResult to update
        """
        # Count by type
        for license in result.licenses:
            result.licenses_by_type[license.license_type] = (
                result.licenses_by_type.get(license.license_type, 0) + 1
            )

            result.licenses_by_format[license.license_format] = (
                result.licenses_by_format.get(license.license_format, 0) + 1
            )

            result.licenses_by_status[license.status] = (
                result.licenses_by_status.get(license.status, 0) + 1
            )

            # Count active/expired
            if license.status == LicenseStatus.ACTIVE:
                result.active_licenses += 1
            elif license.status == LicenseStatus.EXPIRED:
                result.expired_licenses += 1

            # Check if expiring soon
            if license.is_expiring_soon(30):
                result.expiring_soon += 1

    def find_licenses_by_owner(self, owner: str) -> List[License]:
        """
        Find all licenses for a specific owner/plugin.

        Args:
            owner: Owner name to search for

        Returns:
            List of matching licenses
        """
        return [l for l in self.licenses if owner.lower() in l.owner.lower()]

    def find_licenses_by_format(self, license_format: LicenseFormat) -> List[License]:
        """
        Find all licenses of a specific format.

        Args:
            license_format: License format to search for

        Returns:
            List of matching licenses
        """
        return [l for l in self.licenses if l.license_format == license_format]

    def find_expired_licenses(self) -> List[License]:
        """
        Find all expired licenses.

        Returns:
            List of expired licenses
        """
        return [l for l in self.licenses if l.status == LicenseStatus.EXPIRED]

    def find_expiring_soon(self, days: int = 30) -> List[License]:
        """
        Find licenses expiring within specified days.

        Args:
            days: Number of days to check

        Returns:
            List of licenses expiring soon
        """
        return [l for l in self.licenses if l.is_expiring_soon(days)]

    def scan_registry_licenses(self) -> List[License]:
        """
        Scan Windows Registry for license information.

        Returns:
            List of registry-based licenses
        """
        # This will be implemented when we integrate with registry scanner
        # For now, return empty list
        self.logger.info("Registry license scanning not yet implemented")
        return []
