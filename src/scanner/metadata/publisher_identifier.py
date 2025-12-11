"""Publisher identification from file paths and metadata."""

from pathlib import Path
from typing import Optional

from ...data.vendor_registry import vendor_registry


def identify_publisher_from_path(file_path: Path) -> str:
    """
    Identify publisher from file path.

    Uses centralized VendorRegistry for pattern matching.

    Args:
        file_path: Path to plugin file

    Returns:
        Publisher name or "Unknown"
    """
    path_str = str(file_path)

    # Use vendor registry to find matching vendor
    vendor = vendor_registry.find_vendor_by_pattern(path_str)
    return vendor if vendor else "Unknown"


def identify_publisher_from_metadata(product_name: str, company_name: str = "") -> str:
    """
    Identify publisher from product metadata.

    Uses centralized VendorRegistry for pattern matching.

    Args:
        product_name: Product/plugin name
        company_name: Company name from PE header

    Returns:
        Publisher name or "Unknown"
    """
    search_text = f"{product_name} {company_name}"

    # Use vendor registry to find matching vendor
    vendor = vendor_registry.find_vendor_by_pattern(search_text)
    if vendor:
        return vendor

    # Return company name if provided
    if company_name and company_name.lower() != "unknown":
        return company_name

    return "Unknown"
