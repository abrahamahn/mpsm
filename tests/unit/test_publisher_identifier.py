"""Unit tests for publisher_identifier."""

from pathlib import Path

import pytest

from src.scanner.metadata.publisher_identifier import (identify_publisher_from_metadata,
                                                       identify_publisher_from_path)


class TestPublisherIdentifierFromPath:
    """Test identify_publisher_from_path function."""

    def test_native_instruments_paths(self):
        """Test identifying Native Instruments from various paths."""
        test_paths = [
            Path("C:/Program Files/Native Instruments/Kontakt/kontakt.dll"),
            Path("C:/Users/test/AppData/Roaming/Native Instruments/Komplete/"),
            Path("/usr/local/lib/vst/Native Instruments/Massive.so"),
            Path("D:\\Native Instruments\\Battery\\battery.dll"),
        ]

        for path in test_paths:
            publisher = identify_publisher_from_path(path)
            assert publisher == "Native Instruments", f"Failed for path: {path}"

    def test_waves_paths(self):
        """Test identifying Waves from various paths."""
        test_paths = [
            Path("C:/Program Files/Waves/Plug-Ins V14/WaveShell.dll"),
            Path("C:/ProgramData/Waves Audio/instl/plugin.dll"),
            Path("/Library/Audio/Plug-Ins/Waves/SomePlugin.vst"),
        ]

        for path in test_paths:
            publisher = identify_publisher_from_path(path)
            assert publisher == "Waves", f"Failed for path: {path}"

    def test_fabfilter_paths(self):
        """Test identifying FabFilter from paths."""
        test_paths = [
            Path("C:/Program Files/FabFilter/Pro-Q 3.dll"),
            Path("/Library/Audio/Plug-Ins/FabFilter/Pro-C 2.vst"),
        ]

        for path in test_paths:
            publisher = identify_publisher_from_path(path)
            assert publisher == "FabFilter", f"Failed for path: {path}"

    def test_unknown_publisher(self):
        """Test that unknown publishers return 'Unknown'."""
        test_paths = [
            Path("C:/Unknown/Vendor/plugin.dll"),
            Path("/usr/local/lib/random_plugin.so"),
            Path("D:\\Plugins\\UnknownCompany\\plugin.vst3"),
        ]

        for path in test_paths:
            publisher = identify_publisher_from_path(path)
            assert publisher == "Unknown", f"Should return 'Unknown' for path: {path}"

    def test_case_insensitive_matching(self):
        """Test that path matching is case-insensitive."""
        test_paths = [
            Path("C:/NATIVE INSTRUMENTS/Kontakt/kontakt.dll"),
            Path("C:/native instruments/KONTAKT/kontakt.dll"),
            Path("C:/Native_Instruments/kontakt.dll"),
        ]

        for path in test_paths:
            publisher = identify_publisher_from_path(path)
            assert publisher == "Native Instruments", f"Case-insensitive match failed for: {path}"

    def test_various_daw_manufacturers(self):
        """Test identifying various DAW manufacturers."""
        test_cases = [
            (Path("C:/Program Files/Steinberg/Cubase/plugin.dll"), "Steinberg"),
            (Path("C:/Ableton/Live/plugin.dll"), "Ableton"),
            (Path("C:/Image-Line/FL Studio/plugin.dll"), "Image-Line"),
            (Path("C:/Avid/Pro Tools/plugin.aaxplugin"), "Avid"),
        ]

        for path, expected_publisher in test_cases:
            publisher = identify_publisher_from_path(path)
            assert publisher == expected_publisher, f"Failed for {path}"

    def test_plugin_patterns_in_path(self):
        """Test that plugin-specific patterns are matched."""
        test_cases = [
            (Path("C:/Plugins/kontakt_library.dll"), "Native Instruments"),  # kontakt pattern
            (Path("C:/VST/serum_presets.dll"), "Xfer Records"),  # serum pattern
            (Path("C:/Audio/omnisphere_bank.dll"), "Spectrasonics"),  # omnisphere pattern
        ]

        for path, expected_publisher in test_cases:
            publisher = identify_publisher_from_path(path)
            assert publisher == expected_publisher, f"Pattern match failed for {path}"


class TestPublisherIdentifierFromMetadata:
    """Test identify_publisher_from_metadata function."""

    def test_product_name_matching(self):
        """Test identifying publisher from product name."""
        test_cases = [
            ("Kontakt 7", "", "Native Instruments"),
            ("Massive X", "", "Native Instruments"),
            ("FabFilter Pro-Q 3", "", "FabFilter"),
            ("Waves C6 Multiband Compressor", "", "Waves"),
            ("Omnisphere 2", "", "Spectrasonics"),
            ("Serum", "", "Xfer Records"),
        ]

        for product_name, company_name, expected_publisher in test_cases:
            publisher = identify_publisher_from_metadata(product_name, company_name)
            assert publisher == expected_publisher, f"Failed for product: {product_name}"

    def test_company_name_matching(self):
        """Test identifying publisher from company name."""
        test_cases = [
            ("Some Plugin", "Native Instruments GmbH", "Native Instruments"),
            ("Audio Plugin", "Waves Audio Ltd", "Waves"),
            ("VST Effect", "FabFilter", "FabFilter"),
        ]

        for product_name, company_name, expected_publisher in test_cases:
            publisher = identify_publisher_from_metadata(product_name, company_name)
            assert publisher == expected_publisher, f"Failed for company: {company_name}"

    def test_combined_product_and_company(self):
        """Test matching with both product and company name."""
        test_cases = [
            ("Battery 4", "Native Instruments", "Native Instruments"),
            ("H-Delay", "Waves Audio", "Waves"),
            ("Pro-L 2", "FabFilter BV", "FabFilter"),
        ]

        for product_name, company_name, expected_publisher in test_cases:
            publisher = identify_publisher_from_metadata(product_name, company_name)
            assert publisher == expected_publisher

    def test_fallback_to_company_name(self):
        """Test that it falls back to company name when no pattern matches."""
        # When no pattern matches, should return company name
        publisher = identify_publisher_from_metadata("Generic Plugin v1.0", "Small Audio Company")
        assert publisher == "Small Audio Company"

    def test_unknown_when_no_match(self):
        """Test that Unknown is returned when nothing matches."""
        test_cases = [
            ("Generic Plugin", ""),
            ("VST Effect", "Unknown"),
            ("", ""),
        ]

        for product_name, company_name in test_cases:
            publisher = identify_publisher_from_metadata(product_name, company_name)
            assert (
                publisher == "Unknown"
            ), f"Should return Unknown for: {product_name}, {company_name}"

    def test_case_insensitive_metadata_matching(self):
        """Test that metadata matching is case-insensitive."""
        test_cases = [
            ("KONTAKT 7", "", "Native Instruments"),
            ("kontakt 7", "", "Native Instruments"),
            ("KoNtAkT 7", "", "Native Instruments"),
        ]

        for product_name, company_name, expected_publisher in test_cases:
            publisher = identify_publisher_from_metadata(product_name, company_name)
            assert publisher == expected_publisher

    def test_empty_strings(self):
        """Test handling of empty strings."""
        publisher = identify_publisher_from_metadata("", "")
        assert publisher == "Unknown"

    def test_whitespace_handling(self):
        """Test handling of whitespace in product/company names."""
        test_cases = [
            ("  Kontakt 7  ", "  ", "Native Instruments"),
            ("Native Instruments Massive", "", "Native Instruments"),
        ]

        for product_name, company_name, expected_publisher in test_cases:
            publisher = identify_publisher_from_metadata(product_name, company_name)
            assert publisher == expected_publisher


@pytest.mark.integration
class TestPublisherIdentifierIntegration:
    """Integration tests for publisher identifier with VendorRegistry."""

    def test_all_major_vendors_discoverable_by_path(self):
        """Test that all major vendors can be discovered from paths."""
        major_vendors = [
            "Native Instruments",
            "Waves",
            "FabFilter",
            "iZotope",
            "Arturia",
            "Steinberg",
            "Ableton",
        ]

        for vendor in major_vendors:
            path = Path(f"C:/Program Files/{vendor}/plugin.dll")
            publisher = identify_publisher_from_path(path)
            assert publisher == vendor, f"Failed to identify {vendor}"

    def test_consistency_between_path_and_metadata(self):
        """Test that path and metadata methods are consistent."""
        test_cases = [
            (Path("C:/Native Instruments/Kontakt.dll"), "Kontakt", "Native Instruments"),
            (Path("C:/Waves/Plugin.dll"), "Waves C6", "Waves"),
            (
                Path("C:/FabFilter/ProQ.dll"),
                "FabFilter Pro-Q 3",
                "FabFilter",
            ),  # Fixed: include vendor name in product
        ]

        for path, product_name, expected_publisher in test_cases:
            publisher_from_path = identify_publisher_from_path(path)
            publisher_from_metadata = identify_publisher_from_metadata(product_name, "")

            assert publisher_from_path == expected_publisher
            assert publisher_from_metadata == expected_publisher
