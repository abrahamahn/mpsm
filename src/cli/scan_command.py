"""Scan command - comprehensive system scanning for plugins, DAWs, and data."""

import sys
import uuid
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
    # Header
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
        # Load configuration
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

        # Initialize logger (suppress console output during scan to avoid clutter)
        # Force WARNING level to reduce log spam, write everything to file
        logger = get_logger(
            level="WARNING",  # Only show warnings/errors in console
            log_to_console=False,  # Suppress ALL logger console output for clean UI
            log_to_file=config_manager.get("logging.log_to_file", True),
        )

        # Get scan paths
        plugin_paths = config_manager.get_plugin_paths()
        data_paths = config_manager.get_data_paths()

        # Create scan result
        start_time = datetime.now()
        scan_result = ComprehensiveScanResult(
            scan_id=str(uuid.uuid4()),
            scan_date=datetime.now(),
        )

        # Show scan configuration
        console.print("\n[bold]Scan Configuration:[/bold]")
        console.print(f"  • Plugin directories: [cyan]{len(plugin_paths)}[/cyan]")
        console.print(f"  • Data directories: [cyan]{len(data_paths)}[/cyan]")
        console.print()

        # ============================================================
        # 1. SCAN FOR PLUGIN FILES (VST2, VST3, AAX, CLAP)
        # ============================================================
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

            # Show metadata extraction settings
            if enable_vst_host:
                console.print(
                    "  [cyan]🔌 External VST Host enabled[/cyan] - Requires JUCE VSTScanner.exe"
                )
            if enable_registry:
                console.print("  [cyan]ℹ Registry scanning enabled[/cyan]")

            # Get all plugin extensions
            vst2_ext = config_manager.get("scan.extensions.plugins.vst2", [".dll"])
            vst3_ext = config_manager.get("scan.extensions.plugins.vst3", [".vst3"])
            aax_ext = config_manager.get("scan.extensions.plugins.aax", [".aax"])
            clap_ext = config_manager.get("scan.extensions.plugins.clap", [".clap"])
            all_extensions = vst2_ext + vst3_ext + aax_ext + clap_ext

            console.print(f"  Extensions: [dim]{', '.join(all_extensions)}[/dim]")

            # Get validation settings
            min_size = config_manager.get("scan.validation.min_plugin_size_mb", 0.1)
            max_size = config_manager.get("scan.validation.max_plugin_size_mb", 500)

            # Progress callback for real-time directory display with file counts
            import time

            progress_start_time = time.time()  # Renamed to avoid conflict with scan start_time
            last_count = [0]  # Use list to allow modification in closure

            def show_scan_progress(directory: str):
                # Get current file count from scanner
                current_count = scanner.files_scanned
                elapsed = time.time() - progress_start_time
                files_per_sec = current_count / elapsed if elapsed > 0 else 0

                # Truncate long paths for display
                display_path = directory if len(directory) <= 50 else f"...{directory[-47:]}"

                # Show: count | rate | current directory (no Rich markup in sys.stdout)
                sys.stdout.write(
                    f"\r  🔍 Scanning: {current_count:,} files "
                    f"({files_per_sec:.0f}/s) | {display_path}" + " " * 10
                )
                sys.stdout.flush()
                last_count[0] = current_count

            # Scan for plugins
            console.print("  🔍 Scanning directories...")
            plugin_files = scanner.scan_parallel(
                plugin_paths, all_extensions, progress_callback=show_scan_progress
            )
            sys.stdout.write("\r" + " " * 120 + "\r")  # Clear progress line
            console.print(f"  ✓ Found [cyan]{len(plugin_files)}[/cyan] candidate files")

            # Validate and extract metadata
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
                    # Show progress for every file
                    if len(plugin_files) > 0:
                        percent = int((i + 1) / len(plugin_files) * 100)
                        status = "Processing" if raw_output else "Validating"
                        sys.stdout.write(
                            f"\r  🔬 {status}: {percent:3d}% ({i+1:,}/{len(plugin_files):,}) | "
                            f"✓ {validated_count:,} processed" + " " * 20
                        )
                        sys.stdout.flush()

                    # CRITICAL: Validate file before processing (skip if raw_output mode)
                    if not raw_output:
                        if not metadata_extractor.is_valid_plugin_file(
                            file_path, min_size, max_size
                        ):
                            filtered_count += 1
                            continue

                    # Basic file metadata (use safe extraction with fallbacks)
                    try:
                        metadata = metadata_extractor.extract_file_metadata(file_path)
                    except Exception:
                        # Fallback for metadata extraction failure
                        metadata = {
                            "file_size": file_path.stat().st_size if file_path.exists() else 0,
                            "file_hash": "",
                        }

                    try:
                        plugin_type = metadata_extractor.detect_plugin_type(file_path)
                    except Exception:
                        plugin_type = None

                    try:
                        product_name = metadata_extractor.get_product_name(file_path)
                    except Exception:
                        product_name = file_path.stem  # Use filename as fallback

                    try:
                        architecture = metadata_extractor.detect_architecture(file_path)
                    except Exception:
                        architecture = "unknown"

                    # Extract additional metadata (conservative approach)
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

                    # Only set publisher if we can reliably detect it from path
                    try:
                        publisher = metadata_extractor.identify_publisher(file_path)
                        if publisher == "Unknown":
                            publisher = ""  # Leave empty instead of "Unknown"
                    except Exception:
                        publisher = ""

                    # Extract plugin_id using VST host if enabled (VST2 only)
                    plugin_id = None
                    if enable_vst_host and plugin_type == PluginType.VST2:
                        vst_host_attempts += 1
                        try:
                            vst_metadata = metadata_extractor._get_vst_host_metadata(file_path)
                            if vst_metadata and "plugin_id" in vst_metadata:
                                plugin_id = vst_metadata["plugin_id"]
                                vst_host_successes += 1
                                # Update publisher from VST host if available
                                if not publisher and "vst_vendor" in vst_metadata:
                                    publisher = vst_metadata["vst_vendor"]
                        except Exception as e:
                            # VST host extraction failed, skip this plugin
                            logger.debug(f"VST host failed for {file_path}: {e}")

                    # Leave registry_key empty for now
                    # (The registry scanner would need to be properly integrated)
                    registry_key = None

                    plugin = Plugin(
                        name=product_name,
                        publisher=publisher,
                        plugin_id=plugin_id,
                        plugin_type=plugin_type,
                        category=category_str,
                        version=version,
                        file_path=file_path,
                        file_size=metadata["file_size"],
                        file_hash=metadata["file_hash"],
                        architecture=architecture,
                        registry_key=registry_key,
                        license_status="unknown",  # Explicitly unknown
                        license_path=None,  # Leave empty
                    )
                    scan_result.plugins.append(plugin)
                    validated_count += 1

                except Exception as e:
                    # In raw_output mode, show what's failing
                    if raw_output:
                        logger.warning(f"Failed to process {file_path}: {e}")
                    filtered_count += 1

            sys.stdout.write("\r" + " " * 120 + "\r")  # Clear progress line
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

            # Show VST host statistics if enabled
            if enable_vst_host and vst_host_attempts > 0:
                success_rate = (
                    (vst_host_successes / vst_host_attempts * 100) if vst_host_attempts > 0 else 0
                )
                console.print(
                    f"  🔌 VST Host: {vst_host_successes}/{vst_host_attempts}"
                    f" plugin_ids extracted ({success_rate:.0f}%)"
                )

            console.print()

        # ============================================================
        # 2. SCAN FOR APPLICATIONS (DAWs, Plugin Managers, Standalone)
        # ============================================================
        if not skip_apps:
            console.print("[bold cyan]━━━ Phase 2: Applications ━━━[/bold cyan]")

            app_scanner = ApplicationScanner(config=config_manager)
            applications = app_scanner.scan_for_applications()
            scan_result.applications = applications

            console.print(f"  ✓ Found [cyan]{len(applications)}[/cyan] applications")

            # Show breakdown
            daws = app_scanner.find_daws()
            managers = app_scanner.find_plugin_managers()
            standalone = app_scanner.find_standalone_plugins()

            console.print(f"    • DAWs: [cyan]{len(daws)}[/cyan]")
            console.print(f"    • Plugin Managers: [cyan]{len(managers)}[/cyan]")
            console.print(f"    • Standalone: [cyan]{len(standalone)}[/cyan]")
            console.print()

        # ============================================================
        # 3. SCAN FOR DATA FOLDERS (Presets, Samples, Libraries)
        # ============================================================
        if not skip_folders:
            console.print("[bold cyan]━━━ Phase 3: Data Folders ━━━[/bold cyan]")

            folder_scanner = FolderScanner(config=config_manager)
            data_folders = folder_scanner.scan_for_data_folders()
            scan_result.data_folders = data_folders

            console.print(f"  ✓ Found [cyan]{len(data_folders)}[/cyan] data folders")

            # Show breakdown
            presets = folder_scanner.find_preset_folders()
            samples = folder_scanner.find_sample_folders()
            libraries = folder_scanner.find_library_folders()

            console.print(f"    • Presets: [cyan]{len(presets)}[/cyan]")
            console.print(f"    • Samples: [cyan]{len(samples)}[/cyan]")
            console.print(f"    • Libraries: [cyan]{len(libraries)}[/cyan]")
            console.print()

        # ============================================================
        # 4. SCAN REGISTRY (Windows only)
        # ============================================================
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

        # ============================================================
        # 5. SCAN FOR LICENSES
        # ============================================================
        if not skip_licenses:
            console.print("[bold cyan]━━━ Phase 5: License Files ━━━[/bold cyan]")

            try:
                license_scanner = LicenseScanner(config=config_manager)
                license_result = license_scanner.scan_for_licenses()
                scan_result.licenses = license_result.licenses

                console.print(f"  ✓ Found [cyan]{len(license_result.licenses)}[/cyan] licenses")

                # Show breakdown by format
                if license_result.licenses_by_format:
                    for fmt, count in license_result.licenses_by_format.items():
                        console.print(f"    • {fmt.value}: [cyan]{count}[/cyan]")
                console.print()
            except Exception as e:
                console.print(f"  ⚠ [yellow]License scanning skipped:[/yellow] {e}")
                console.print()

        # ============================================================
        # FINALIZE SCAN
        # ============================================================
        scan_result.scan_duration = (datetime.now() - start_time).total_seconds()
        scan_result.calculate_statistics()

        # Display comprehensive summary
        console.print()
        console.print(
            Panel.fit(
                f"[bold green]✓ Scan Complete![/bold green]\n"
                f"[dim]Duration: {scan_result.scan_duration:.1f}s[/dim]",
                border_style="green",
            )
        )
        console.print()

        # Summary table
        summary_table = Table(show_header=True, header_style="bold cyan", border_style="dim")
        summary_table.add_column("Component", style="cyan")
        summary_table.add_column("Count", justify="right", style="bold")

        summary_table.add_row("Real Plugins", f"{len(scan_result.plugins)}")
        summary_table.add_row("Applications", f"{len(scan_result.applications)}")
        summary_table.add_row("Data Folders", f"{len(scan_result.data_folders)}")
        summary_table.add_row("Registry Entries", f"{scan_result.total_registry_entries}")
        summary_table.add_row("Licenses", f"{len(scan_result.licenses)}")

        console.print(summary_table)
        console.print()

        # Export results
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print("[bold]📁 Exporting Results[/bold]")

        if format in ["csv", "both"]:
            scan_result.export_csv(output_dir)
            console.print(f"  ✓ CSV files → [cyan]{output_dir}/[/cyan]")

        if format in ["excel", "both"]:
            excel_path = output_dir / f"scan_results_{scan_result.scan_id[:8]}.xlsx"
            scan_result.export_excel(excel_path)
            console.print(f"  ✓ Excel file → [cyan]{excel_path.name}[/cyan]")

        # Save scan result as JSON for later use
        import json

        json_path = output_dir / f"scan_result_{scan_result.scan_id[:8]}.json"
        with open(json_path, "w") as f:
            json.dump(scan_result.get_summary_dict(), f, indent=2)
        console.print(f"  ✓ JSON metadata → [cyan]{json_path.name}[/cyan]")
        console.print()

        # Display sample results
        _display_scan_samples(scan_result)

    except MPSMException as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def _display_scan_samples(scan_result: ComprehensiveScanResult):
    """Display sample results from scan."""

    # Sample plugins
    if scan_result.plugins:
        console.print("\n[bold]Sample Plugins (showing first 10):[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Publisher", style="yellow")
        table.add_column("Type", style="green")
        table.add_column("Size", style="blue")

        for plugin in scan_result.plugins[:10]:
            size_mb = round(plugin.file_size / (1024 * 1024), 2)
            table.add_row(
                plugin.name[:40], plugin.publisher[:20], plugin.plugin_type.value, f"{size_mb} MB"
            )
        console.print(table)

    # Sample applications
    if scan_result.applications:
        console.print("\n[bold]Sample Applications (showing first 10):[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Publisher", style="yellow")
        table.add_column("Type", style="green")
        table.add_column("Version", style="blue")

        for app in scan_result.applications[:10]:
            table.add_row(
                app.name[:40], app.publisher[:20], app.app_type.value, app.version or "N/A"
            )
        console.print(table)

    # Sample data folders
    if scan_result.data_folders:
        console.print("\n[bold]Sample Data Folders (showing first 10):[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Owner", style="yellow")
        table.add_column("Type", style="green")
        table.add_column("Size", style="blue")

        for folder in scan_result.data_folders[:10]:
            size_gb = round(folder.total_size / (1024**3), 2)
            table.add_row(
                folder.name[:40], folder.owner[:20], folder.folder_type.value, f"{size_gb} GB"
            )
        console.print(table)
