"""License tracking data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict


class LicenseType(Enum):
    """Types of software licenses."""

    PERPETUAL = "perpetual"
    SUBSCRIPTION = "subscription"
    TRIAL = "trial"
    NFR = "nfr"  # Not For Resale
    EDUCATIONAL = "educational"
    RENTAL = "rental"
    UNKNOWN = "unknown"


class LicenseStatus(Enum):
    """License activation status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    DEACTIVATED = "deactivated"
    NOT_ACTIVATED = "not_activated"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class LicenseFormat(Enum):
    """Format of license storage."""

    FILE = "file"  # .lic, .key, .license files
    REGISTRY = "registry"  # Stored in Windows Registry
    ILOK = "ilok"  # PACE iLok
    CHALLENGE_RESPONSE = "challenge_response"  # Manual activation
    ONLINE = "online"  # Online verification only
    HARDWARE_DONGLE = "hardware_dongle"  # USB dongle (e.g., eLicenser, WIBU)
    UNKNOWN = "unknown"


@dataclass
class License:
    """Represents a software license."""

    license_id: str
    name: str  # Product name
    owner: str  # Plugin/product owner
    publisher: str  # Software publisher
    license_type: LicenseType
    license_format: LicenseFormat
    status: LicenseStatus

    # File-based licenses
    file_path: Optional[Path] = None
    file_hash: Optional[str] = None

    # Key-based licenses
    key_string: Optional[str] = None
    activation_code: Optional[str] = None

    # Registry-based licenses
    registry_key: Optional[str] = None
    registry_value: Optional[str] = None

    # iLok licenses
    ilok_account: Optional[str] = None
    ilok_location: Optional[str] = None  # Cloud, iLok device, computer

    # Dongle-based licenses
    dongle_id: Optional[str] = None
    dongle_type: Optional[str] = None  # eLicenser, WIBU, etc.

    # Dates
    installation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    last_verified: Optional[datetime] = None

    # Network licenses
    license_server: Optional[str] = None
    license_server_port: Optional[int] = None

    # Metadata
    version: Optional[str] = None
    machine_id: Optional[str] = None
    user_email: Optional[str] = None
    notes: Optional[str] = None

    # Relationships
    related_plugin: Optional[str] = None  # Plugin file this license activates
    related_application: Optional[str] = None  # Application this license activates

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'license_id': self.license_id,
            'name': self.name,
            'owner': self.owner,
            'publisher': self.publisher,
            'license_type': self.license_type.value,
            'license_format': self.license_format.value,
            'status': self.status.value,
            'file_path': str(self.file_path) if self.file_path else None,
            'file_hash': self.file_hash,
            'key_string': self.key_string[:20] + '...' if self.key_string and len(self.key_string) > 20 else self.key_string,
            'activation_code': self.activation_code[:20] + '...' if self.activation_code and len(self.activation_code) > 20 else self.activation_code,
            'registry_key': self.registry_key,
            'ilok_account': self.ilok_account,
            'ilok_location': self.ilok_location,
            'dongle_id': self.dongle_id,
            'dongle_type': self.dongle_type,
            'installation_date': self.installation_date.isoformat() if self.installation_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'last_verified': self.last_verified.isoformat() if self.last_verified else None,
            'license_server': self.license_server,
            'version': self.version,
            'notes': self.notes,
            'related_plugin': self.related_plugin,
            'related_application': self.related_application,
        }

    def is_valid(self) -> bool:
        """Check if license is currently valid."""
        if self.status == LicenseStatus.ACTIVE:
            if self.expiration_date:
                return datetime.now() < self.expiration_date
            return True
        return False

    def days_until_expiration(self) -> Optional[int]:
        """Calculate days until license expires."""
        if self.expiration_date:
            delta = self.expiration_date - datetime.now()
            return max(0, delta.days)
        return None

    def is_expiring_soon(self, days: int = 30) -> bool:
        """Check if license expires within specified days."""
        days_left = self.days_until_expiration()
        if days_left is not None:
            return 0 <= days_left <= days
        return False


@dataclass
class LicenseScanResult:
    """Results from scanning for licenses."""

    scan_date: datetime
    total_licenses: int
    licenses_by_type: Dict[LicenseType, int] = field(default_factory=dict)
    licenses_by_format: Dict[LicenseFormat, int] = field(default_factory=dict)
    licenses_by_status: Dict[LicenseStatus, int] = field(default_factory=dict)

    licenses: List[License] = field(default_factory=list)

    # Statistics
    active_licenses: int = 0
    expired_licenses: int = 0
    expiring_soon: int = 0  # Within 30 days

    # File locations scanned
    scanned_paths: List[Path] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'scan_date': self.scan_date.isoformat(),
            'total_licenses': self.total_licenses,
            'licenses_by_type': {k.value: v for k, v in self.licenses_by_type.items()},
            'licenses_by_format': {k.value: v for k, v in self.licenses_by_format.items()},
            'licenses_by_status': {k.value: v for k, v in self.licenses_by_status.items()},
            'active_licenses': self.active_licenses,
            'expired_licenses': self.expired_licenses,
            'expiring_soon': self.expiring_soon,
            'scanned_paths': [str(p) for p in self.scanned_paths],
        }

    def get_summary(self) -> str:
        """Generate summary string."""
        summary = f"""
License Scan Summary
===================
Scan Date: {self.scan_date.strftime('%Y-%m-%d %H:%M:%S')}
Total Licenses: {self.total_licenses}

Status:
- Active: {self.active_licenses}
- Expired: {self.expired_licenses}
- Expiring Soon: {self.expiring_soon}

By Type:
"""
        for license_type, count in self.licenses_by_type.items():
            summary += f"- {license_type.value.title()}: {count}\n"

        summary += "\nBy Format:\n"
        for license_format, count in self.licenses_by_format.items():
            summary += f"- {license_format.value.replace('_', ' ').title()}: {count}\n"

        return summary


@dataclass
class iLokLicense:
    """Represents an iLok license from PACE system."""

    license_id: str
    product_name: str
    publisher: str
    location: str  # Cloud, iLok2, iLok3, Computer
    license_type: str
    expiration_date: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'license_id': self.license_id,
            'product_name': self.product_name,
            'publisher': self.publisher,
            'location': self.location,
            'license_type': self.license_type,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
        }


@dataclass
class LicenseBackup:
    """Represents a license backup."""

    backup_id: str
    backup_date: datetime
    licenses_count: int
    backup_path: Path
    description: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'backup_id': self.backup_id,
            'backup_date': self.backup_date.isoformat(),
            'licenses_count': self.licenses_count,
            'backup_path': str(self.backup_path),
            'description': self.description,
        }
