"""Custom exceptions for MPSM."""

from typing import Any, Dict, Optional


class MPSMException(Exception):
    """Base exception for MPSM."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize exception.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of exception."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} | Details: {details_str}"
        return self.message


class ScanException(MPSMException):
    """Raised during scanning operations."""

    pass


class RegistryException(MPSMException):
    """Raised during registry operations."""

    pass


class FileOperationException(MPSMException):
    """Raised during file operations."""

    pass


class LicenseException(MPSMException):
    """Raised during license operations."""

    pass


class ConfigException(MPSMException):
    """Raised for configuration errors."""

    pass


class ValidationException(MPSMException):
    """Raised when validation fails."""

    pass


class RollbackException(MPSMException):
    """Raised when rollback fails."""

    pass


class MetadataExtractionException(MPSMException):
    """Raised when metadata extraction fails."""

    pass


class PathNotFoundException(FileOperationException):
    """Raised when a required path is not found."""

    pass


class InsufficientPermissionsException(MPSMException):
    """Raised when operations fail due to insufficient permissions."""

    pass


class DiskSpaceException(FileOperationException):
    """Raised when insufficient disk space is available."""

    pass


class PluginNotFoundException(MPSMException):
    """Raised when a plugin cannot be found."""

    pass
