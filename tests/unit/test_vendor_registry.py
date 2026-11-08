"""Unit tests for VendorRegistry."""

import pytest

from src.data.vendor_registry import VendorRegistry, vendor_registry


class TestVendorRegistry:
    """Test VendorRegistry functionality."""

    def test_singleton_pattern(self):
        """Test that VendorRegistry follows singleton pattern."""
        registry1 = VendorRegistry()
        registry2 = VendorRegistry()
        assert registry1 is registry2

    def test_vendor_count(self):
        """Test that vendors are loaded correctly."""
        registry = VendorRegistry()
        count = registry.vendor_count()
        assert count > 0
        assert count == 108  # Expected vendor count from vendors.yaml

    def test_find_vendor_by_pattern_native_instruments(self):
        """Test finding Native Instruments by pattern."""
        registry = VendorRegistry()

        # Test various patterns
        test_cases = [
            "C:/Program Files/Native Instruments/Kontakt/kontakt.dll",
            "C:/Users/test/Documents/Native Instruments/Komplete/",
            "/usr/local/lib/vst/kontakt.so",
            "D:\\Plugins\\Native Instruments\\Massive.dll",
        ]

        for test_path in test_cases:
            vendor = registry.find_vendor_by_pattern(test_path)
            assert vendor == "Native Instruments", f"Failed for path: {test_path}"

    def test_find_vendor_by_pattern_waves(self):
        """Test finding Waves by pattern."""
        registry = VendorRegistry()

        test_cases = [
            "C:/Program Files/Waves/Plug-Ins V14/WaveShell.dll",
            "C:/ProgramData/Waves Audio/instl/",
            "/Library/Audio/Plug-Ins/Waves/",
        ]

        for test_path in test_cases:
            vendor = registry.find_vendor_by_pattern(test_path)
            assert vendor == "Waves", f"Failed for path: {test_path}"

    def test_find_vendor_by_pattern_unknown(self):
        """Test that unknown paths return None."""
        registry = VendorRegistry()

        test_cases = [
            "C:/Unknown/Vendor/plugin.dll",
            "/usr/local/lib/random_plugin.so",
            "D:\\Plugins\\UnknownCompany\\plugin.vst3",
        ]

        for test_path in test_cases:
            vendor = registry.find_vendor_by_pattern(test_path)
            assert vendor is None, f"Should return None for: {test_path}"

    def test_find_vendor_by_folder(self):
        """Test finding vendor by folder name."""
        registry = VendorRegistry()

        test_cases = [
            ("Native Instruments", "Native Instruments"),
            ("Waves Audio", "Waves"),
            ("Image-Line", "Image-Line"),
            ("FL Studio", "Image-Line"),
            ("Steinberg", "Steinberg"),
        ]

        for folder_name, expected_vendor in test_cases:
            vendor = registry.find_vendor_by_folder(folder_name)
            assert vendor == expected_vendor, f"Failed for folder: {folder_name}"

    def test_find_vendor_by_folder_unknown(self):
        """Test that unknown folders return None."""
        registry = VendorRegistry()

        unknown_folders = ["UnknownVendor", "RandomFolder", "NotAVendor"]

        for folder_name in unknown_folders:
            vendor = registry.find_vendor_by_folder(folder_name)
            assert vendor is None, f"Should return None for: {folder_name}"

    def test_get_all_patterns(self):
        """Test getting all vendor patterns."""
        registry = VendorRegistry()
        patterns = registry.get_all_patterns()

        assert isinstance(patterns, dict)
        assert len(patterns) > 0
        assert "Native Instruments" in patterns
        assert "Waves" in patterns
        assert isinstance(patterns["Native Instruments"], list)
        assert len(patterns["Native Instruments"]) > 0

    def test_get_all_folders(self):
        """Test getting all vendor folders."""
        registry = VendorRegistry()
        folders = registry.get_all_folders()

        assert isinstance(folders, dict)
        assert len(folders) > 0
        assert "Native Instruments" in folders
        assert "Native Instruments" in folders["Native Instruments"]

    def test_get_all_daw_executables(self):
        """Test getting all DAW executables."""
        registry = VendorRegistry()
        daws = registry.get_all_daw_executables()

        assert isinstance(daws, dict)
        assert len(daws) > 0

        # Check specific DAWs
        assert any("FL" in name or "Image-Line" in name for name in daws.keys())
        assert any("Ableton" in name for name in daws.keys())

    def test_get_all_plugin_manager_executables(self):
        """Test getting all plugin manager executables."""
        registry = VendorRegistry()
        managers = registry.get_all_plugin_manager_executables()

        assert isinstance(managers, dict)
        assert len(managers) > 0

        # Check specific managers
        assert any("Native" in name for name in managers.keys())
        assert any("Waves" in name for name in managers.keys())

    def test_get_all_standalone_executables(self):
        """Test getting all standalone plugin executables."""
        registry = VendorRegistry()
        standalones = registry.get_all_standalone_executables()

        assert isinstance(standalones, dict)
        assert len(standalones) > 0

        # Check specific standalones
        assert any("Native Instruments" in name for name in standalones.keys())

    def test_all_vendor_names(self):
        """Test getting all vendor names."""
        registry = VendorRegistry()
        names = registry.all_vendor_names()

        assert isinstance(names, list)
        assert len(names) > 0
        assert "Native Instruments" in names
        assert "Waves" in names
        assert names == sorted(names)  # Should be sorted

    def test_search_vendors(self):
        """Test searching for vendors."""
        registry = VendorRegistry()

        # Test searching by name
        results = registry.search_vendors("Native")
        assert "Native Instruments" in results

        # Test searching by pattern
        results = registry.search_vendors("kontakt")
        assert "Native Instruments" in results

        # Test searching for unknown
        results = registry.search_vendors("UnknownVendor123")
        assert len(results) == 0

    def test_vendor_registry_singleton_module_level(self):
        """Test that module-level vendor_registry is the same instance."""
        registry1 = VendorRegistry()
        assert vendor_registry is registry1

    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive."""
        registry = VendorRegistry()

        test_cases = [
            "C:/NATIVE INSTRUMENTS/Kontakt/",
            "C:/native instruments/KONTAKT/",
            "C:/Native_Instruments/kontakt/",
        ]

        for test_path in test_cases:
            vendor = registry.find_vendor_by_pattern(test_path)
            assert vendor == "Native Instruments", f"Case-insensitive match failed for: {test_path}"

    def test_get_vendor_info(self):
        """Test getting complete vendor information."""
        registry = VendorRegistry()

        # Test getting Native Instruments info
        info = registry.get_vendor_info("native_instruments")
        assert info is not None
        assert info["name"] == "Native Instruments"
        assert "patterns" in info
        assert "folders" in info
        assert "executables" in info

    def test_repr(self):
        """Test string representation."""
        registry = VendorRegistry()
        repr_str = repr(registry)
        assert "VendorRegistry" in repr_str
        assert "vendors=" in repr_str


@pytest.mark.integration
class TestVendorRegistryIntegration:
    """Integration tests for VendorRegistry with actual vendor data."""

    def test_all_vendors_have_required_fields(self):
        """Test that all vendors have required fields."""
        registry = VendorRegistry()

        for vendor_key, vendor_data in registry._vendors.items():
            assert "name" in vendor_data, f"Vendor {vendor_key} missing 'name' field"
            assert "patterns" in vendor_data, f"Vendor {vendor_key} missing 'patterns' field"
            assert isinstance(
                vendor_data["patterns"], list
            ), f"Patterns should be list for {vendor_key}"

    def test_no_duplicate_vendor_names(self):
        """Test that vendor names are unique."""
        registry = VendorRegistry()
        names = registry.all_vendor_names()
        assert len(names) == len(set(names)), "Duplicate vendor names found"

    def test_pattern_matching_coverage(self):
        """Test that pattern matching works for major vendors."""
        registry = VendorRegistry()

        major_vendors = [
            ("Native Instruments", "kontakt"),
            ("Waves", "waves"),
            ("FabFilter", "fabfilter"),
            ("iZotope", "izotope"),
            ("Arturia", "arturia"),
        ]

        for vendor_name, pattern in major_vendors:
            vendor = registry.find_vendor_by_pattern(f"C:/test/{pattern}/plugin.dll")
            assert vendor == vendor_name, f"Pattern matching failed for {vendor_name}"
