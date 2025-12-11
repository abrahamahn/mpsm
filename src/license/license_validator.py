"""License validation and verification."""

import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..core.logger import get_logger
from ..models.license import License, LicenseFormat, LicenseStatus, LicenseType


class LicenseValidator:
    """Validates and verifies licenses."""

    def __init__(self):
        """Initialize license validator."""
        self.logger = get_logger()

    def validate_license(self, license: License) -> bool:
        """
        Validate a license.

        Args:
            license: License to validate

        Returns:
            True if license is valid
        """
        # Check if license file exists (for file-based licenses)
        if license.license_format == LicenseFormat.FILE and license.file_path:
            if not license.file_path.exists():
                self.logger.warning(f"License file not found: {license.file_path}")
                license.status = LicenseStatus.INVALID
                return False

        # Check if license has expired
        if license.expiration_date:
            if datetime.now() > license.expiration_date:
                license.status = LicenseStatus.EXPIRED
                return False

        # Verify file integrity (for file-based licenses)
        if license.license_format == LicenseFormat.FILE and license.file_path:
            if not self._verify_file_integrity(license):
                license.status = LicenseStatus.INVALID
                return False

        # If all checks pass, mark as active
        license.status = LicenseStatus.ACTIVE
        license.last_verified = datetime.now()
        return True

    def _verify_file_integrity(self, license: License) -> bool:
        """
        Verify license file integrity using hash.

        Args:
            license: License to verify

        Returns:
            True if file integrity verified
        """
        if not license.file_path or not license.file_hash:
            return True  # Can't verify without hash

        try:
            current_hash = self._calculate_file_hash(license.file_path)
            if current_hash != license.file_hash:
                self.logger.warning(f"License file hash mismatch: {license.file_path}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error verifying file integrity: {e}")
            return False

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file.

        Args:
            file_path: File to hash

        Returns:
            Hex digest of hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def batch_validate(self, licenses: List[License]) -> Dict[str, int]:
        """
        Validate multiple licenses.

        Args:
            licenses: List of licenses to validate

        Returns:
            Dictionary with validation statistics
        """
        valid_count = 0
        invalid_count = 0
        expired_count = 0

        for license in licenses:
            if self.validate_license(license):
                valid_count += 1
            else:
                if license.status == LicenseStatus.EXPIRED:
                    expired_count += 1
                else:
                    invalid_count += 1

        stats = {
            "total": len(licenses),
            "valid": valid_count,
            "invalid": invalid_count,
            "expired": expired_count,
        }

        self.logger.info(
            f"Validated {len(licenses)} licenses: "
            f"{valid_count} valid, {invalid_count} invalid, {expired_count} expired"
        )

        return stats

    def find_expiring_licenses(self, licenses: List[License], days: int = 30) -> List[License]:
        """
        Find licenses expiring within specified days.

        Args:
            licenses: List of licenses to check
            days: Number of days to check ahead

        Returns:
            List of licenses expiring soon
        """
        expiring = []
        threshold = datetime.now() + timedelta(days=days)

        for license in licenses:
            if license.expiration_date:
                if datetime.now() < license.expiration_date <= threshold:
                    expiring.append(license)

        return expiring

    def find_expired_licenses(self, licenses: List[License]) -> List[License]:
        """
        Find all expired licenses.

        Args:
            licenses: List of licenses to check

        Returns:
            List of expired licenses
        """
        expired = []

        for license in licenses:
            if license.expiration_date:
                if datetime.now() > license.expiration_date:
                    license.status = LicenseStatus.EXPIRED
                    expired.append(license)

        return expired

    def find_invalid_licenses(self, licenses: List[License]) -> List[License]:
        """
        Find all invalid licenses.

        Args:
            licenses: List of licenses to check

        Returns:
            List of invalid licenses
        """
        invalid = []

        for license in licenses:
            if not self.validate_license(license):
                if license.status != LicenseStatus.EXPIRED:
                    invalid.append(license)

        return invalid

    def check_license_conflicts(self, licenses: List[License]) -> List[Dict[str, any]]:
        """
        Check for license conflicts (duplicates, mismatches, etc.).

        Args:
            licenses: List of licenses to check

        Returns:
            List of conflicts found
        """
        conflicts = []

        # Check for duplicate license files
        file_hashes = {}
        for license in licenses:
            if license.file_path and license.file_hash:
                if license.file_hash in file_hashes:
                    conflicts.append(
                        {
                            "type": "duplicate",
                            "license1": license.name,
                            "license2": file_hashes[license.file_hash].name,
                            "hash": license.file_hash,
                        }
                    )
                else:
                    file_hashes[license.file_hash] = license

        # Check for multiple licenses for same product
        products = {}
        for license in licenses:
            product_key = (license.owner, license.publisher)
            if product_key in products:
                products[product_key].append(license)
            else:
                products[product_key] = [license]

        for product_key, product_licenses in products.items():
            if len(product_licenses) > 1:
                conflicts.append(
                    {
                        "type": "multiple_licenses",
                        "product": product_key[0],
                        "publisher": product_key[1],
                        "count": len(product_licenses),
                    }
                )

        return conflicts

    def verify_license_plugin_match(self, license: License, plugin_path: Path) -> bool:
        """
        Verify that a license matches a plugin.

        Args:
            license: License to verify
            plugin_path: Plugin file path

        Returns:
            True if license matches plugin
        """
        # Check if plugin path contains license owner name
        if license.owner.lower() in str(plugin_path).lower():
            return True

        # Check if license has related_plugin
        if license.related_plugin:
            if license.related_plugin.lower() in str(plugin_path).lower():
                return True

        return False

    def generate_validation_report(self, licenses: List[License]) -> Dict[str, any]:
        """
        Generate comprehensive validation report.

        Args:
            licenses: List of licenses to report on

        Returns:
            Dictionary with validation report
        """
        # Validate all licenses
        stats = self.batch_validate(licenses)

        # Find expiring licenses
        expiring_30 = self.find_expiring_licenses(licenses, days=30)
        expiring_90 = self.find_expiring_licenses(licenses, days=90)

        # Find expired licenses
        expired = self.find_expired_licenses(licenses)

        # Check for conflicts
        conflicts = self.check_license_conflicts(licenses)

        report = {
            "report_date": datetime.now().isoformat(),
            "total_licenses": len(licenses),
            "validation_stats": stats,
            "expiring_30_days": len(expiring_30),
            "expiring_90_days": len(expiring_90),
            "expired": len(expired),
            "conflicts": len(conflicts),
            "conflict_details": conflicts,
        }

        return report

    def get_license_health_score(self, license: License) -> float:
        """
        Calculate health score for a license (0-100).

        Args:
            license: License to score

        Returns:
            Health score (0-100)
        """
        score = 100.0

        # Deduct for expired
        if license.status == LicenseStatus.EXPIRED:
            return 0.0

        # Deduct for invalid
        if license.status == LicenseStatus.INVALID:
            return 0.0

        # Deduct for expiring soon
        if license.expiration_date:
            days_left = (license.expiration_date - datetime.now()).days
            if days_left < 30:
                score -= 30
            elif days_left < 90:
                score -= 10

        # Deduct for missing file
        if license.license_format == LicenseFormat.FILE and license.file_path:
            if not license.file_path.exists():
                score -= 50

        # Deduct for no verification
        if license.last_verified:
            days_since_verification = (datetime.now() - license.last_verified).days
            if days_since_verification > 90:
                score -= 10

        return max(0.0, score)
