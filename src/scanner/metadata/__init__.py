"""Metadata extraction modules.

This package contains modular components for extracting metadata from plugin files:
- extractor: Main MetadataExtractor class
- pe_parser: PE header parsing
- vst_detector: VST signature detection
- publisher_identifier: Publisher identification
"""

from .extractor import MetadataExtractor

__all__ = ["MetadataExtractor"]
