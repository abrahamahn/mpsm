"""Scan command - comprehensive system scanning for plugins, DAWs, and data."""

import sys
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from ..core.config import ConfigManager
from ..core.exceptions import MPSMException
from ..core.logger import get_logger
from ..license.license_scanner import LicenseScanner
from ..models.plugin import Plugin, PluginType
from ..models.scan_result import ComprehensiveScanResult
from ..registry.registry_reader import RegistryReader
from ..scanner.application_scanner import ApplicationScanner
from ..scanner.file_scanner import FileScanner
from ..scanner.folder_scanner import FolderScanner
from ..scanner.metadata.extractor import MetadataExtractor
from .scan_reporter import display_scan_samples, display_scan_summary, export_scan_results

console = Console()


@click.command()
@click.option("--config", default="config.yaml", help="Config file path")
@click.option("--output", default="data", help="Output directory for results")
@click.option(
    "--format", type=click.Choice(["csv", "excel", "both"]), default="both", help="Export format"
)
@click.option("--skip-plugins", is_flag=True, help="Skip plugin file scanning")
@click.option("--skip-apps", is_flag=True, help="Skip application scanning")
@click.option("--skip-folders", is_flag=True, help="Skip data folder scanning")
@click.option("--skip-registry", is_flag=True, help="Skip registry scanning")
@click.option("--skip-licenses", is_flag=True, help="Skip license scanning")
@click.option(
    "--enable-vst-host",
    is_flag=True,
    help="Enable external JUCE VST host for plugin_id extraction (requires VSTScanner.exe)",
)
@click.option(
    "--enable-registry",
    is_flag=True,
    default=True,
    help="Enable Windows registry metadata extraction",
)
@click.option(
    "--raw-output",
    is_flag=True,
    help="Skip validation filtering - output all candidate files for manual analysis",
)
def scan(
    config,
    output,
    format,
    skip_plugins,
    skip_apps,
    skip_folders,
    skip_registry,
    skip_licenses,
    enable_vst_host,
    enable_registry,
    raw_output,
):
    """Comprehensive scan for music production software, plugins, DAWs, and data."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]MPSM Comprehensive Scanner[/bold cyan]\n"
            "[dim]Music Production Software Manager[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    try:
        console.print("📋 [bold]Loading configuration...[/bold]", end=" ")
        config_manager = ConfigManager(Path(config))
        errors = config_manager.validate_config()

        if errors:
            console.print("[red]✗[/red]")
            console.print("\n[red]Configuration errors:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)

        console.print("[green]✓[/green]")

        logger = get_logger(
            level="WARNING",
            log_to_console=False,
            log_to_file=config_manager.get("logging.log_to_file", True),
        )

        plugin_paths = config_manager.get_plugin_paths()
        data_paths = config_manager.get_data_paths()

        start_time = datetime.now()
        scan_result = ComprehensiveScanResult(
            scan_id=str(uuid.uuid4()),
            scan_date=datetime.now(),
        )

        console.print("\n[bold]Scan Configuration:[/bold]")
        console.print(f"  • Plugin directories: [cyan]{len(plugin_paths)}[/cyan]")
        console.print(f"  • Data directories: [cyan]{len(data_paths)}[/cyan]")
        console.print()

        # 1. SCAN FOR PLUGIN FILES (VST2, VST3, AAX, CLAP)
        if not skip_plugins:
            console.print("[bold cyan]━━━ Phase 1: Plugin Files ━━━[/bold cyan]")

            scanner = FileScanner(
                exclude_paths=config_manager.get_exclude_paths(),
                max_workers=config_manager.get("scan.max_workers", 4),
                verbose=False,
            )
            metadata_extractor = MetadataExtractor(
                enable_vst_host=enable_vst_host, enable_registry=enable_registry
            )

            if enable_vst_host:
                console.print(
                    "  [cyan]🔌 External VST Host enabled[/cyan] - Requires JUCE VSTScanner.exe"
                )
            if enable_registry:
                console.print("  [cyan]ℹ Registry scanning enabled[/cyan]")

            vst2_ext = config_manager.get("scan.extensions.plugins.vst2", [".dll"])
            vst3_ext = config_manager.get("scan.extensions.plugins.vst3", [".vst3"])
            aax_ext = config_manager.get("scan.extensions.plugins.aax", [".aax"])
            clap_ext = config_manager.get("scan.extensions.plugins.clap", [".clap"])
            all_extensions = vst2_ext + vst3_ext + aax_ext + clap_ext

            console.print(f"  Extensions: [dim]{', '.join(all_extensions)}[/dim]")

            min_size = config_manager.get("scan.validation.min_plugin_size_mb", 0.1)
            max_size = config_manager.get("scan.validation.max_plugin_size_mb", 500)

            progress_start_time = time.time()

            def show_scan_progress(directory: str) -> None:
                current_count = scanner.files_scanned
                elapsed = time.time() - progress_start_time
                files_per_sec = current_count / elapsed if elapsed > 0 else 0
                display_path = directory if len(directory) <= 50 else f"...{directory[-47:]}"
                sys.stdout.write(
                    f"\r  🔍 Scanning: {current_count:,} files "
                    f"({files_per_sec:.0f}/s) | {display_path}" + " " * 10
                )
                sys.stdout.flush()

            console.print("  🔍 Scanning directories...")
            plugin_files = scanner.scan_parallel(
                plugin_paths, all_extensions, progress_callback=show_scan_progress
            )
            sys.stdout.write("\r" + " " * 120 + "\r")
            console.print(f"  ✓ Found [cyan]{len(plugin_files)}[/cyan] candidate files")

            if raw_output:
                console.print("  📋 Processing all files (raw output mode - no filtering)...")
            else:
                console.print("  🔬 Validating plugins...")
            validated_count = 0
            filtered_count = 0
            vst_host_attempts = 0
            vst_host_successes = 0

            for i, file_path in enumerate(plugin_files):
                try:
                    if len(plugin_files) > 0:
                        percent = int((i + 1) / len(plugin_files) * 100)
                        status = "Processing" if raw_output else "Validating"
                        sys.stdout.write(
                            f"\r  🔬 {status}: {percent:3d}% ({i+1:,}/{len(plugin_files):,}) | "
                            f"✓ {validated_count:,} processed" + " " * 20
                        )
                        sys.stdout.flush()

                    if not raw_output:
                        if not metadata_extractor.is_valid_plugin_file(
                            file_path, min_size, max_size
                        ):
                            filtered_count += 1
                            continue

                    try:
                        metadata = metadata_extractor.extract_file_metadata(file_path)
                    except Exception:
                        metadata = {
                            "file_size": file_path.stat().st_size if file_path.exists() else 0,
                            "file_hash": "",
                        }

                    try:
                        plugin_type = metadata_extractor.detect_plugin_type(file_path)
                    except Exception:
                        plugin_type = PluginType.UNKNOWN

                    try:
                        product_name = metadata_extractor.get_product_name(file_path)
                    except Exception:
                        product_name = file_path.stem

                    try:
                        architecture = metadata_extractor.detect_architecture(file_path)
                    except Exception:
                        architecture = "unknown"

                    try:
                        version = metadata_extractor.extract_version_from_pe(file_path)
                    except Exception:
                        version = None

                    try:
                        category_str = metadata_extractor.detect_plugin_category(
                            file_path, product_name, ""
                        )
                    except Exception:
                        category_str = "unknown"

                    try:
                        publisher = metadata_extractor.identify_publisher(file_path)
                        if publisher == "Unknown":
                            publisher = ""
                    except Exception:
                        publisher = ""

                    plugin_id = None
                    if enable_vst_host and plugin_type == PluginType.VST2:
                        vst_host_attempts += 1
                        try:
                            vst_metadata = metadata_extractor._get_vst_host_metadata(file_path)
                            if vst_metadata and "plugin_id" in vst_metadata:
                                plugin_id = vst_metadata["plugin_id"]
                                vst_host_successes += 1
                                if not publisher and "vst_vendor" in vst_metadata:
                                    publisher = vst_metadata["vst_vendor"]
                        except Exception as e:
                            logger.debug(f"VST host failed for {file_path}: {e}")

                    plugin = Plugin(
                        name=product_name,
                        publisher=publisher,
                        plugin_id=plugin_id,
                        plugin_type=plugin_type,
                        category=category_str,
                        version=version,
                        file_path=file_path,
                        file_size=int(metadata["file_size"]),
                        file_hash=str(metadata["file_hash"]),
                        architecture=architecture,
                        registry_key=None,
                        license_status="unknown",
                        license_path=None,
                    )
                    scan_result.plugins.append(plugin)
                    validated_count += 1

                except Exception as e:
                    if raw_output:
                        logger.warning(f"Failed to process {file_path}: {e}")
                    filtered_count += 1

            sys.stdout.write("\r" + " " * 120 + "\r")
            scan_result.total_files_scanned = scanner.files_scanned

            if raw_output:
                console.print(
                    f"  ✓ [green bold]{len(scan_result.plugins)} files processed[/green bold]"
                    " (no filtering applied)"
                )
                if filtered_count > 0:
                    console.print(
                        f"  ⚠ [yellow]{filtered_count} files failed to process[/yellow]"
                        " (check logs for details)"
                    )
            else:
                console.print(
                    f"  ✓ [green bold]{len(scan_result.plugins)} real plugins[/green bold]"
                    " validated"
                )
                if filtered_count > 0:
                    console.print(
                        f"  ⚠ [yellow]{filtered_count} files filtered[/yellow]"
                        " (helpers, installers, etc.)"
                    )

            if enable_vst_host and vst_host_attempts > 0:
                success_rate = (
                    (vst_host_successes / vst_host_attempts * 100) if vst_host_attempts > 0 else 0
                )
                console.print(
                    f"  🔌 VST Host: {vst_host_successes}/{vst_host_attempts}"
                    f" plugin_ids extracted ({success_rate:.0f}%)"
                )

            console.print()

        # 2. SCAN FOR APPLICATIONS (DAWs, Plugin Managers, Standalone)
        if not skip_apps:
            console.print("[bold cyan]━━━ Phase 2: Applications ━━━[/bold cyan]")

            app_scanner = ApplicationScanner(config=config_manager)
            applications = app_scanner.scan_for_applications()
            scan_result.applications = applications

            console.print(f"  ✓ Found [cyan]{len(applications)}[/cyan] applications")

            daws = app_scanner.find_daws()
            managers = app_scanner.find_plugin_managers()
            standalone = app_scanner.find_standalone_plugins()

            console.print(f"    • DAWs: [cyan]{len(daws)}[/cyan]")
            console.print(f"    • Plugin Managers: [cyan]{len(managers)}[/cyan]")
            console.print(f"    • Standalone: [cyan]{len(standalone)}[/cyan]")
            console.print()

        # 3. SCAN FOR DATA FOLDERS (Presets, Samples, Libraries)
        if not skip_folders:
            console.print("[bold cyan]━━━ Phase 3: Data Folders ━━━[/bold cyan]")

            folder_scanner = FolderScanner(config=config_manager)
            data_folders = folder_scanner.scan_for_data_folders()
            scan_result.data_folders = data_folders

            console.print(f"  ✓ Found [cyan]{len(data_folders)}[/cyan] data folders")

            presets = folder_scanner.find_preset_folders()
            samples = folder_scanner.find_sample_folders()
            libraries = folder_scanner.find_library_folders()

            console.print(f"    • Presets: [cyan]{len(presets)}[/cyan]")
            console.print(f"    • Samples: [cyan]{len(samples)}[/cyan]")
            console.print(f"    • Libraries: [cyan]{len(libraries)}[/cyan]")
            console.print()

        # 4. SCAN REGISTRY (Windows only)
        if not skip_registry:
            console.print("[bold cyan]━━━ Phase 4: Windows Registry ━━━[/bold cyan]")

            try:
                registry_reader = RegistryReader()
                registry_entries = registry_reader.scan_all_music_production_keys()
                scan_result.total_registry_entries = sum(
                    len(entries) for entries in registry_entries.values()
                )

                console.print(
                    f"  ✓ Found [cyan]{len(registry_entries)}[/cyan] registry keys"
                    f" ([cyan]{scan_result.total_registry_entries}[/cyan] entries)"
                )
                console.print()
            except Exception as e:
                console.print(f"  ⚠ [yellow]Registry scanning skipped:[/yellow] {e}")
                console.print()

        # 5. SCAN FOR LICENSES
        if not skip_licenses:
            console.print("[bold cyan]━━━ Phase 5: License Files ━━━[/bold cyan]")

            try:
                license_scanner = LicenseScanner(config=config_manager)
                license_result = license_scanner.scan_for_licenses()
                scan_result.licenses = license_result.licenses

                console.print(f"  ✓ Found [cyan]{len(license_result.licenses)}[/cyan] licenses")

                if license_result.licenses_by_format:
                    for fmt, count in license_result.licenses_by_format.items():
                        console.print(f"    • {fmt.value}: [cyan]{count}[/cyan]")
                console.print()
            except Exception as e:
                console.print(f"  ⚠ [yellow]License scanning skipped:[/yellow] {e}")
                console.print()

        # FINALIZE SCAN
        scan_result.scan_duration = (datetime.now() - start_time).total_seconds()
        scan_result.calculate_statistics()

        display_scan_summary(console, scan_result)
        export_scan_results(console, scan_result, Path(output), format)
        display_scan_samples(console, scan_result)

    except MPSMException as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        traceback.print_exc()
        sys.exit(1)
