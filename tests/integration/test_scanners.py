"""Integration tests for refactored scanners."""

import pytest
from pathlib import Path
from src.scanner.folder_scanner import FolderScanner
from src.scanner.application_scanner import ApplicationScanner


@pytest.mark.integration
class TestFolderScannerIntegration:
    """Integration tests for FolderScanner with BaseScanner."""

    def test_folder_scanner_extends_base_scanner(self):
        """Test that FolderScanner properly extends BaseScanner."""
        from src.scanner.base_scanner import BaseScanner

        scanner = FolderScanner()
        assert isinstance(scanner, BaseScanner)

    def test_folder_scanner_has_base_scanner_methods(self):
        """Test that FolderScanner has BaseScanner methods."""
        scanner = FolderScanner()

        # Check for BaseScanner methods
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'get_items')
        assert hasattr(scanner, 'item_count')
        assert hasattr(scanner, 'clear')
        assert hasattr(scanner, '_get_default_scan_paths')
        assert hasattr(scanner, '_identify_item')

    def test_folder_scanner_backward_compatibility(self):
        """Test that FolderScanner maintains backward compatibility."""
        scanner = FolderScanner()

        # Check for backward compatible API
        assert hasattr(scanner, 'scan_for_data_folders')
        assert hasattr(scanner, 'data_folders')

        # Test property access
        scanner.data_folders = []
        assert scanner.data_folders == []
        assert scanner.items == []

    def test_folder_scanner_scan_empty_path(self, temp_dir):
        """Test scanning an empty directory."""
        scanner = FolderScanner()

        # Create empty test directory
        test_dir = temp_dir / "test"
        test_dir.mkdir()

        # Scan should work without errors
        results = scanner.scan_for_data_folders([str(test_dir)])

        assert isinstance(results, list)
        assert len(results) == 0

    def test_folder_scanner_scan_with_mock_folder(self, temp_dir):
        """Test scanning with a mock folder structure."""
        scanner = FolderScanner()

        # Create mock folder structure
        preset_dir = temp_dir / "TestVendor" / "Presets"
        preset_dir.mkdir(parents=True)

        # Scan
        results = scanner.scan_for_data_folders([str(temp_dir)])

        # May or may not find folder depending on identification logic
        assert isinstance(results, list)


@pytest.mark.integration
class TestApplicationScannerIntegration:
    """Integration tests for ApplicationScanner with BaseScanner."""

    def test_application_scanner_extends_base_scanner(self):
        """Test that ApplicationScanner properly extends BaseScanner."""
        from src.scanner.base_scanner import BaseScanner

        scanner = ApplicationScanner()
        assert isinstance(scanner, BaseScanner)

    def test_application_scanner_has_base_scanner_methods(self):
        """Test that ApplicationScanner has BaseScanner methods."""
        scanner = ApplicationScanner()

        # Check for BaseScanner methods
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'get_items')
        assert hasattr(scanner, 'item_count')
        assert hasattr(scanner, 'clear')
        assert hasattr(scanner, '_get_default_scan_paths')
        assert hasattr(scanner, '_identify_item')

    def test_application_scanner_backward_compatibility(self):
        """Test that ApplicationScanner maintains backward compatibility."""
        scanner = ApplicationScanner()

        # Check for backward compatible API
        assert hasattr(scanner, 'scan_for_applications')
        assert hasattr(scanner, 'applications')

        # Test property access
        scanner.applications = []
        assert scanner.applications == []
        assert scanner.items == []

    def test_application_scanner_scan_empty_path(self, temp_dir):
        """Test scanning an empty directory."""
        scanner = ApplicationScanner()

        # Create empty test directory
        test_dir = temp_dir / "test"
        test_dir.mkdir()

        # Scan should work without errors
        results = scanner.scan_for_applications([str(test_dir)])

        assert isinstance(results, list)
        assert len(results) == 0

    def test_application_scanner_identify_item_non_file(self, temp_dir):
        """Test that _identify_item returns None for directories."""
        scanner = ApplicationScanner()

        # Test with directory (should return None)
        result = scanner._identify_item(temp_dir)
        assert result is None


@pytest.mark.integration
class TestBaseScannerIntegration:
    """Integration tests for BaseScanner functionality."""

    def test_scanners_share_base_class(self):
        """Test that all scanners share the same base class."""
        from src.scanner.base_scanner import BaseScanner

        folder_scanner = FolderScanner()
        app_scanner = ApplicationScanner()

        assert isinstance(folder_scanner, BaseScanner)
        assert isinstance(app_scanner, BaseScanner)

        # Check they have same base methods
        assert hasattr(folder_scanner, 'scan')
        assert hasattr(app_scanner, 'scan')

    def test_scanners_use_items_list(self):
        """Test that scanners use the items list from BaseScanner."""
        folder_scanner = FolderScanner()
        app_scanner = ApplicationScanner()

        # Both should have items attribute from BaseScanner
        assert hasattr(folder_scanner, 'items')
        assert hasattr(app_scanner, 'items')

        # Both should be lists
        assert isinstance(folder_scanner.items, list)
        assert isinstance(app_scanner.items, list)

    def test_scanner_len_method(self):
        """Test that scanners support len() via BaseScanner."""
        scanner = FolderScanner()

        assert len(scanner) == 0

        # Test after adding items
        scanner.items = [None, None, None]
        assert len(scanner) == 3

    def test_scanner_repr(self):
        """Test that scanners have repr from BaseScanner."""
        folder_scanner = FolderScanner()
        app_scanner = ApplicationScanner()

        folder_repr = repr(folder_scanner)
        app_repr = repr(app_scanner)

        assert "FolderScanner" in folder_repr
        assert "items=" in folder_repr

        assert "ApplicationScanner" in app_repr
        assert "items=" in app_repr
