#!/usr/bin/env python3
"""
MPSM - Music Production Software Manager
Main CLI entry point
"""

import sys
from datetime import datetime
from pathlib import Path
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.table import Table

from src.core.config import ConfigManager
from src.core.logger import get_logger
from src.core.exceptions import MPSMException, RegistryException
from src.scanner.file_scanner import FileScanner
from src.scanner.metadata_extractor import MetadataExtractor
from src.scanner.application_scanner import ApplicationScanner
from src.scanner.folder_scanner import FolderScanner
from src.models.plugin import Plugin, PluginType, PluginCategory
from src.models.scan_result import ComprehensiveScanResult
from src.registry.registry_reader import RegistryReader
from src.registry.manager import RegistryManager
from src.registry.validator import PathValidator
from src.organizer.structure_builder import StructureBuilder
from src.organizer.file_mover import FileMover
from src.organizer.consolidator import Consolidator
from src.license.license_scanner import LicenseScanner
from src.license.ilok_manager import iLokManager
from src.license.license_validator import LicenseValidator

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """MPSM - Music Production Software Manager

    \b
    A comprehensive tool for managing VST plugins, DAWs, and music production software.
    Scans, organizes, and tracks all your music production components.
    """
    pass


@cli.command()
@click.option('--path', default=None, help='Custom config path')
@click.option('--auto-detect', is_flag=True, help='Auto-detect existing plugin directories')
def init(path, auto_detect):
    """Initialize MPSM configuration."""
    try:
        config_path = Path(path) if path else Path('config.yaml')

        if config_path.exists():
            console.print(f"[yellow]Config file already exists: {config_path}[/yellow]")
            if not click.confirm('Overwrite?'):
                return

        # Use create_if_missing=True to allow init to create new config
        config = ConfigManager(config_path, create_if_missing=True)
        config.create_default_config()

        console.print(f"[green]✓[/green] Created configuration file: {config_path}")

        # Auto-detect existing paths if requested
        if auto_detect:
            console.print("\n[bold]Auto-detecting existing directories...[/bold]")
            detected_paths = _auto_detect_scan_paths()

            if detected_paths:
                console.print(f"[green]✓[/green] Detected {len(detected_paths)} existing directories")

                # Show detected paths
                for path_str in detected_paths[:10]:
                    console.print(f"  • {path_str}")
                if len(detected_paths) > 10:
                    console.print(f"  ... and {len(detected_paths) - 10} more")

                console.print("\n[dim]Run 'python mpsm.py config optimize' to update config with detected paths[/dim]")
            else:
                console.print("[yellow]⚠[/yellow] No standard plugin directories found")

        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Edit config.yaml and replace 'YOUR_USERNAME' with your actual username")
        console.print("2. Add any custom plugin/sample library directories you use")
        console.print("3. Run 'python mpsm.py scan' to scan your system")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _auto_detect_scan_paths() -> list:
    """Auto-detect existing plugin and audio software directories."""
    import platform
    import os

    detected = []
    is_windows = platform.system() == 'Windows'

    # Common plugin directories to check
    common_paths = [
        "C:\\Program Files\\VSTPlugins",
        "C:\\Program Files\\Steinberg",
        "C:\\Program Files\\Common Files\\VST3",
        "C:\\Program Files\\Common Files\\Avid",
        "C:\\Program Files (x86)\\VSTPlugins",
        "C:\\Program Files (x86)\\Steinberg",
        "C:\\Program Files (x86)\\Common Files\\VST3",
        "C:\\Program Files\\Image-Line",
        "C:\\Program Files\\Ableton",
        "C:\\Program Files\\Avid",
        "C:\\Program Files\\PreSonus",
        "C:\\Program Files\\Native Instruments",
        "C:\\Program Files\\Spectrasonics",
        "C:\\Program Files\\Waves",
        "C:\\Program Files\\iZotope",
        "C:\\Program Files\\FabFilter",
        "C:\\Program Files\\Arturia",
    ]

    # Add user-specific paths
    if is_windows:
        username = os.getenv('USERNAME')
        if username:
            common_paths.extend([
                f"C:\\Users\\{username}\\Documents",
                f"C:\\Users\\{username}\\AppData\\Roaming",
                f"C:\\Users\\{username}\\AppData\\Local",
            ])

    # Check which paths exist
    for path_str in common_paths:
        path = Path(path_str)
        if path.exists() and path.is_dir():
            detected.append(path_str)

    return detected


@cli.command()
@click.option('--config', default='config.yaml', help='Config file path')
@click.option('--output', default='data', help='Output directory for results')
@click.option('--format', type=click.Choice(['csv', 'excel', 'both']), default='both', help='Export format')
@click.option('--skip-plugins', is_flag=True, help='Skip plugin file scanning')
@click.option('--skip-apps', is_flag=True, help='Skip application scanning')
@click.option('--skip-folders', is_flag=True, help='Skip data folder scanning')
@click.option('--skip-registry', is_flag=True, help='Skip registry scanning')
@click.option('--skip-licenses', is_flag=True, help='Skip license scanning')
@click.option('--enable-vst-host', is_flag=True, help='Enable VST host for plugin_id extraction (slower, may crash on unstable plugins)')
@click.option('--enable-registry', is_flag=True, default=True, help='Enable Windows registry metadata extraction')
def scan(config, output, format, skip_plugins, skip_apps, skip_folders, skip_registry, skip_licenses, enable_vst_host, enable_registry):
    """Comprehensive scan for music production software, plugins, DAWs, and data."""
    from rich.panel import Panel
    from rich.table import Table

    # Header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]MPSM Comprehensive Scanner[/bold cyan]\n"
        "[dim]Music Production Software Manager[/dim]",
        border_style="cyan"
    ))
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

        # Initialize logger (suppress console output during scan)
        logger = get_logger(
            level=config_manager.get('logging.level', 'INFO'),
            log_to_console=False,  # Suppress logger console output
            log_to_file=config_manager.get('logging.log_to_file', True),
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
                max_workers=config_manager.get('scan.max_workers', 4),
                verbose=False
            )
            metadata_extractor = MetadataExtractor(
                enable_vst_host=enable_vst_host,
                enable_registry=enable_registry
            )

            # Show metadata extraction settings
            if enable_vst_host:
                console.print("  [yellow]⚠ VST Host enabled[/yellow] - May be slower, can crash on unstable plugins")
            if enable_registry:
                console.print("  [cyan]ℹ Registry scanning enabled[/cyan]")

            # Get all plugin extensions
            vst2_ext = config_manager.get('scan.extensions.plugins.vst2', ['.dll'])
            vst3_ext = config_manager.get('scan.extensions.plugins.vst3', ['.vst3'])
            aax_ext = config_manager.get('scan.extensions.plugins.aax', ['.aax'])
            clap_ext = config_manager.get('scan.extensions.plugins.clap', ['.clap'])
            all_extensions = vst2_ext + vst3_ext + aax_ext + clap_ext

            console.print(f"  Extensions: [dim]{', '.join(all_extensions)}[/dim]")

            # Get validation settings
            min_size = config_manager.get('scan.validation.min_plugin_size_mb', 0.1)
            max_size = config_manager.get('scan.validation.max_plugin_size_mb', 500)

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
            plugin_files = scanner.scan_parallel(plugin_paths, all_extensions, progress_callback=show_scan_progress)
            sys.stdout.write("\r" + " " * 120 + "\r")  # Clear progress line
            console.print(f"  ✓ Found [cyan]{len(plugin_files)}[/cyan] candidate files")

            # Validate and extract metadata
            console.print("  🔬 Validating plugins...")
            validated_count = 0
            filtered_count = 0

            for i, file_path in enumerate(plugin_files):
                try:
                    # Show progress for every file
                    if len(plugin_files) > 0:
                        percent = int((i + 1) / len(plugin_files) * 100)
                        sys.stdout.write(
                            f"\r  🔬 Validating: {percent:3d}% ({i+1:,}/{len(plugin_files):,}) | "
                            f"✓ {validated_count:,} valid | ✗ {filtered_count:,} filtered" + " " * 10
                        )
                        sys.stdout.flush()

                    # CRITICAL: Validate file before processing
                    if not metadata_extractor.is_valid_plugin_file(file_path, min_size, max_size):
                        filtered_count += 1
                        continue

                    # Basic file metadata
                    metadata = metadata_extractor.extract_file_metadata(file_path)
                    plugin_type = metadata_extractor.detect_plugin_type(file_path)
                    product_name = metadata_extractor.get_product_name(file_path)
                    architecture = metadata_extractor.detect_architecture(file_path)

                    # Extract additional metadata (conservative approach)
                    version = metadata_extractor.extract_version_from_pe(file_path)
                    category_str = metadata_extractor.detect_plugin_category(file_path, product_name, "")

                    # Only set publisher if we can reliably detect it from path
                    publisher = metadata_extractor.identify_publisher(file_path)
                    if publisher == "Unknown":
                        publisher = ""  # Leave empty instead of "Unknown"

                    # Extract plugin_id using VST host if enabled (VST2 only)
                    plugin_id = None
                    if enable_vst_host and plugin_type == PluginType.VST2:
                        try:
                            vst_metadata = metadata_extractor._get_vst_host_metadata(file_path)
                            if vst_metadata and 'plugin_id' in vst_metadata:
                                plugin_id = vst_metadata['plugin_id']
                                # Update publisher from VST host if available
                                if not publisher and 'vst_vendor' in vst_metadata:
                                    publisher = vst_metadata['vst_vendor']
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
                        file_size=metadata['file_size'],
                        file_hash=metadata['file_hash'],
                        architecture=architecture,
                        registry_key=registry_key,
                        license_status="unknown",  # Explicitly unknown
                        license_path=None,  # Leave empty
                    )
                    scan_result.plugins.append(plugin)
                    validated_count += 1

                except Exception as e:
                    filtered_count += 1

            sys.stdout.write("\r" + " " * 120 + "\r")  # Clear progress line
            scan_result.total_files_scanned = scanner.files_scanned

            console.print(f"  ✓ [green bold]{len(scan_result.plugins)} real plugins[/green bold] validated")
            if filtered_count > 0:
                console.print(f"  ⚠ [yellow]{filtered_count} files filtered[/yellow] (helpers, installers, etc.)")
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
                scan_result.total_registry_entries = sum(len(entries) for entries in registry_entries.values())

                console.print(f"  ✓ Found [cyan]{len(registry_entries)}[/cyan] registry keys ([cyan]{scan_result.total_registry_entries}[/cyan] entries)")
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
        console.print(Panel.fit(
            f"[bold green]✓ Scan Complete![/bold green]\n"
            f"[dim]Duration: {scan_result.scan_duration:.1f}s[/dim]",
            border_style="green"
        ))
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

        if format in ['csv', 'both']:
            scan_result.export_csv(output_dir)
            console.print(f"  ✓ CSV files → [cyan]{output_dir}/[/cyan]")

        if format in ['excel', 'both']:
            excel_path = output_dir / f"scan_results_{scan_result.scan_id[:8]}.xlsx"
            scan_result.export_excel(excel_path)
            console.print(f"  ✓ Excel file → [cyan]{excel_path.name}[/cyan]")

        # Save scan result as JSON for later use
        import json
        json_path = output_dir / f"scan_result_{scan_result.scan_id[:8]}.json"
        with open(json_path, 'w') as f:
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
        console.print(f"\n[bold]Sample Plugins (showing first 10):[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Publisher", style="yellow")
        table.add_column("Type", style="green")
        table.add_column("Size", style="blue")

        for plugin in scan_result.plugins[:10]:
            size_mb = round(plugin.file_size / (1024 * 1024), 2)
            table.add_row(
                plugin.name[:40],
                plugin.publisher[:20],
                plugin.plugin_type.value,
                f"{size_mb} MB"
            )
        console.print(table)

    # Sample applications
    if scan_result.applications:
        console.print(f"\n[bold]Sample Applications (showing first 10):[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Publisher", style="yellow")
        table.add_column("Type", style="green")
        table.add_column("Version", style="blue")

        for app in scan_result.applications[:10]:
            table.add_row(
                app.name[:40],
                app.publisher[:20],
                app.app_type.value,
                app.version or "N/A"
            )
        console.print(table)

    # Sample data folders
    if scan_result.data_folders:
        console.print(f"\n[bold]Sample Data Folders (showing first 10):[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Owner", style="yellow")
        table.add_column("Type", style="green")
        table.add_column("Size", style="blue")

        for folder in scan_result.data_folders[:10]:
            size_gb = round(folder.total_size / (1024 ** 3), 2)
            table.add_row(
                folder.name[:40],
                folder.owner[:20],
                folder.folder_type.value,
                f"{size_gb} GB"
            )
        console.print(table)


@cli.command()
def status():
    """Show MPSM status and configuration."""
    try:
        config = ConfigManager()
        console.print("[bold cyan]MPSM Status[/bold cyan]")
        console.print("="*50)

        console.print(f"\nConfig file: {config.config_path}")
        console.print(f"Root path: {config.get_root_path()}")
        console.print(f"Dry-run mode: {config.is_dry_run()}")

        console.print(f"\n[bold]Scan Configuration:[/bold]")
        console.print(f"  Scan paths: {len(config.get_scan_paths())}")
        console.print(f"  Exclude paths: {len(config.get_exclude_paths())}")
        console.print(f"  Parallel: {config.get('scan.parallel', True)}")
        console.print(f"  Max workers: {config.get('scan.max_workers', 4)}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--scan-file', '-s', type=click.Path(exists=True), help='Scan results file to use')
@click.option('--dry-run/--execute', default=True, help='Dry run mode (default: true)')
@click.option('--approve', is_flag=True, help='Auto-approve execution without prompts')
def organize(scan_file, dry_run, approve):
    """Organize and consolidate plugins into clean structure."""
    try:
        console.print("[bold cyan]Plugin Organizer[/bold cyan]")
        console.print("="*50)

        # Load configuration
        config = ConfigManager()

        # Override dry_run from config if specified
        if not dry_run:
            if not approve and not click.confirm('\n[yellow]This will move files. Continue?[/yellow]'):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Initialize components
        consolidator = Consolidator(config=config, dry_run=dry_run)
        structure_builder = StructureBuilder(config=config)

        # Show target structure
        console.print("\n[bold]Target Structure:[/bold]")
        summary = structure_builder.get_structure_summary()
        console.print(f"Root: {summary['root_path']}")
        console.print(f"Available Space: {summary['available_space_gb']} GB")

        # If no scan file provided, run a new scan
        if not scan_file:
            console.print("\n[bold]No scan file provided. Running new scan...[/bold]")

            # Run quick scan
            scanner = FileScanner(
                exclude_paths=config.get_exclude_paths(),
                max_workers=config.get('scan.max_workers', 4),
                verbose=False
            )

            metadata_extractor = MetadataExtractor()
            scan_paths = config.get_scan_paths()
            vst2_ext = config.get('scan.extensions.plugins.vst2', ['.dll'])
            vst3_ext = config.get('scan.extensions.plugins.vst3', ['.vst3'])
            all_extensions = vst2_ext + vst3_ext

            plugin_files = scanner.scan_parallel(scan_paths, all_extensions)

            # Create scan result
            scan_result = ComprehensiveScanResult(
                scan_id=str(uuid.uuid4()),
                scan_date=datetime.now(),
            )

            for file_path in plugin_files:
                try:
                    metadata = metadata_extractor.extract_file_metadata(file_path)
                    plugin_type = metadata_extractor.detect_plugin_type(file_path)
                    publisher = metadata_extractor.identify_publisher(file_path)
                    product_name = metadata_extractor.get_product_name(file_path)

                    plugin = Plugin(
                        name=product_name,
                        publisher=publisher,
                        plugin_type=plugin_type,
                        file_path=file_path,
                        file_size=metadata['file_size'],
                        file_hash=metadata['file_hash'],
                    )

                    scan_result.plugins.append(plugin)
                except Exception:
                    pass

            scan_result.calculate_statistics()
            console.print(f"Found {len(scan_result.plugins)} plugins")
        else:
            console.print(f"\n[yellow]Loading scan from file not yet implemented[/yellow]")
            console.print("Run without --scan-file to use live scan")
            return

        # Create consolidation plan
        console.print("\n[bold]Creating consolidation plan...[/bold]")
        plan = consolidator.plan_consolidation(scan_result)

        # Display plan summary
        console.print(f"\n{plan.get_summary()}")

        # Display warnings and conflicts
        if plan.warnings:
            console.print(f"\n[yellow]Warnings:[/yellow]")
            for warning in plan.warnings[:10]:
                console.print(f"  - {warning}")
            if len(plan.warnings) > 10:
                console.print(f"  ... and {len(plan.warnings) - 10} more")

        if plan.conflicts:
            console.print(f"\n[red]Conflicts:[/red]")
            for conflict in plan.conflicts[:10]:
                console.print(f"  - {conflict}")
            if len(plan.conflicts) > 10:
                console.print(f"  ... and {len(plan.conflicts) - 10} more")

            console.print(f"\n[red]Cannot proceed with {len(plan.conflicts)} conflicts[/red]")
            return

        # Show operation details
        if plan.move_operations:
            console.print(f"\n[bold]Sample Operations (showing first 5):[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Source", style="cyan")
            table.add_column("Destination", style="green")
            table.add_column("Type", style="yellow")

            for source, dest, is_folder in plan.move_operations[:5]:
                table.add_row(
                    str(source)[-60:],
                    str(dest)[-60:],
                    "Folder" if is_folder else "File"
                )

            console.print(table)

        # Estimate time
        estimated_time = consolidator.estimate_consolidation_time(plan)
        console.print(f"\nEstimated time: {estimated_time:.1f} seconds")

        if dry_run:
            console.print(f"\n[yellow]DRY RUN MODE - No files will be moved[/yellow]")
        else:
            console.print(f"\n[bold red]LIVE MODE - Files will be moved![/bold red]")

        # Confirm execution
        if not dry_run and not approve:
            if not click.confirm('\nProceed with consolidation?'):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Execute consolidation
        console.print("\n[bold]Executing consolidation...[/bold]")
        result = consolidator.execute_consolidation(plan, create_backup=True)

        # Display results
        console.print(f"\n[bold]Consolidation Results:[/bold]")
        result_dict = result.to_dict()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Operations Attempted", str(result.operations_attempted))
        table.add_row("Successful", str(result.operations_successful))
        table.add_row("Failed", str(result.operations_failed))
        table.add_row("Duration", f"{result.duration_seconds:.2f}s")
        table.add_row("Success Rate", f"{result_dict['success_rate']}%")

        console.print(table)

        if result.operations_failed > 0:
            console.print(f"\n[yellow]⚠ Consolidation completed with {result.operations_failed} failures[/yellow]")
        else:
            console.print(f"\n[bold green]✓ Consolidation completed successfully![/bold green]")

    except MPSMException as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.group()
def registry():
    """Registry management commands."""
    pass


@registry.command('backup')
@click.option('--keys', '-k', multiple=True, help='Registry keys to backup')
@click.option('--description', '-d', default='', help='Backup description')
def registry_backup(keys, description):
    """Backup registry keys."""
    try:
        console.print("[bold cyan]Registry Backup[/bold cyan]")
        console.print("="*50)

        # Initialize registry manager
        manager = RegistryManager()

        # If no keys specified, backup all known music production keys
        if not keys:
            reader = RegistryReader()
            console.print("\n[yellow]No keys specified, backing up all known music production keys...[/yellow]")
            keys = []
            for base_key in reader.KNOWN_KEYS:
                for hive in ['HKLM', 'HKCU']:
                    key_path = f"{hive}\\{base_key}"
                    if reader.key_exists(key_path):
                        keys.append(key_path)

        console.print(f"\nBacking up {len(keys)} keys...")

        # Create backup
        backup_id = manager.backup_keys(list(keys), description)

        console.print(f"\n[bold green]✓ Backup created successfully![/bold green]")
        console.print(f"Backup ID: {backup_id}")
        console.print(f"Keys backed up: {len(keys)}")

    except RegistryException as e:
        console.print(f"\n[red]Registry Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@registry.command('restore')
@click.argument('backup_id')
def registry_restore(backup_id):
    """Restore registry from backup."""
    try:
        console.print("[bold cyan]Registry Restore[/bold cyan]")
        console.print("="*50)

        manager = RegistryManager()

        # Get backup info
        backup_info = manager.backup_manager.get_backup_info(backup_id)
        if not backup_info:
            console.print(f"[red]Backup not found: {backup_id}[/red]")
            sys.exit(1)

        console.print(f"\nBackup ID: {backup_id}")
        console.print(f"Date: {backup_info['backup_date']}")
        console.print(f"Keys: {backup_info['keys_count']}")
        console.print(f"Description: {backup_info.get('description', 'N/A')}")

        if not click.confirm('\nAre you sure you want to restore this backup?'):
            console.print("[yellow]Restore cancelled[/yellow]")
            return

        console.print("\nRestoring...")
        success = manager.rollback(backup_id)

        if success:
            console.print(f"\n[bold green]✓ Backup restored successfully![/bold green]")
        else:
            console.print(f"\n[red]✗ Restore failed[/red]")
            sys.exit(1)

    except RegistryException as e:
        console.print(f"\n[red]Registry Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@registry.command('list')
def registry_list():
    """List all registry backups."""
    try:
        manager = RegistryManager()
        backups = manager.list_backups()

        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            return

        console.print(f"\n[bold]Registry Backups ({len(backups)} total)[/bold]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Backup ID", style="cyan")
        table.add_column("Date", style="yellow")
        table.add_column("Keys", style="green")
        table.add_column("Description", style="white")

        for backup in backups:
            table.add_row(
                backup['backup_id'],
                backup['backup_date'][:19],  # Truncate timestamp
                str(backup['keys_count']),
                backup.get('description', '')[:50]  # Truncate long descriptions
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@registry.command('validate')
def registry_validate():
    """Validate registry paths."""
    try:
        console.print("[bold cyan]Registry Path Validation[/bold cyan]")
        console.print("="*50)

        validator = PathValidator()

        console.print("\n[bold]Validating registry paths...[/bold]")
        broken_paths = validator.validate_registry_paths()

        if not broken_paths:
            console.print("\n[bold green]✓ All registry paths are valid![/bold green]")
            return

        console.print(f"\n[bold red]Found {len(broken_paths)} broken paths:[/bold red]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_column("Path", style="red")
        table.add_column("Reason", style="white")

        for broken in broken_paths[:20]:  # Show first 20
            table.add_row(
                broken['key_path'][-50:],  # Truncate long paths
                broken['value_name'],
                broken['path'][-50:],
                broken['reason']
            )

        console.print(table)

        if len(broken_paths) > 20:
            console.print(f"\n[yellow]... and {len(broken_paths) - 20} more[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@registry.command('scan')
@click.option('--export', '-e', type=click.Path(), help='Export to file')
def registry_scan(export):
    """Scan registry for music production software."""
    try:
        console.print("[bold cyan]Registry Scanner[/bold cyan]")
        console.print("="*50)

        reader = RegistryReader()

        console.print("\n[bold]Scanning registry...[/bold]")
        all_entries = reader.scan_all_music_production_keys()

        total_entries = sum(len(entries) for entries in all_entries.values())
        console.print(f"\n[bold green]Found {len(all_entries)} keys with {total_entries} total entries[/bold green]")

        # Display summary
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Registry Key", style="cyan")
        table.add_column("Values", style="yellow")

        for key_path, entries in list(all_entries.items())[:15]:
            table.add_row(key_path[-60:], str(len(entries)))

        console.print(table)

        if len(all_entries) > 15:
            console.print(f"\n[yellow]... and {len(all_entries) - 15} more keys[/yellow]")

        # Export if requested
        if export:
            reader.export_registry_snapshot(Path(export))
            console.print(f"\n[green]✓[/green] Exported to {export}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.group()
def license():
    """License management commands."""
    pass


@license.command('scan')
@click.option('--config', default='config.yaml', help='Config file path')
@click.option('--output', '-o', default='data/licenses.json', help='Output file path')
@click.option('--format', type=click.Choice(['json', 'csv', 'excel']), default='json', help='Output format')
def license_scan(config, output, format):
    """Scan for license files."""
    try:
        console.print("[bold cyan]License Scanner[/bold cyan]")
        console.print("="*50)

        # Load config
        config_manager = ConfigManager(Path(config))
        scanner = LicenseScanner(config=config_manager)

        # Scan for licenses
        console.print("\n[bold]Scanning for licenses...[/bold]")
        result = scanner.scan_for_licenses()

        # Display results
        console.print(f"\n[bold green]Found {result.total_licenses} licenses[/bold green]")

        # Display summary table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Owner", style="cyan")
        table.add_column("Format", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("File Path", style="white", overflow="fold")

        for lic in result.licenses[:15]:
            status_color = "green" if lic.status.value == "active" else "red"
            table.add_row(
                lic.owner,
                lic.license_format.value,
                f"[{status_color}]{lic.status.value}[/{status_color}]",
                str(lic.file_path) if lic.file_path else "N/A"
            )

        console.print(table)

        if result.total_licenses > 15:
            console.print(f"\n[yellow]... and {result.total_licenses - 15} more licenses[/yellow]")

        # Export
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            import json
            with open(output_path, 'w') as f:
                json.dump({
                    'scan_result': result.to_dict(),
                    'licenses': [lic.to_dict() for lic in result.licenses]
                }, f, indent=2)
            console.print(f"\n[green]✓[/green] Exported to {output_path}")

        elif format == 'csv':
            import pandas as pd
            df = pd.DataFrame([lic.to_dict() for lic in result.licenses])
            df.to_csv(output_path.with_suffix('.csv'), index=False)
            console.print(f"\n[green]✓[/green] Exported to {output_path.with_suffix('.csv')}")

        elif format == 'excel':
            import pandas as pd
            df = pd.DataFrame([lic.to_dict() for lic in result.licenses])
            df.to_excel(output_path.with_suffix('.xlsx'), index=False)
            console.print(f"\n[green]✓[/green] Exported to {output_path.with_suffix('.xlsx')}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@license.command('validate')
@click.argument('license_file', type=click.Path(exists=True))
def license_validate(license_file):
    """Validate licenses from scan results."""
    try:
        console.print("[bold cyan]License Validator[/bold cyan]")
        console.print("="*50)

        # Load licenses from file
        import json
        with open(license_file, 'r') as f:
            data = json.load(f)
            licenses_data = data.get('licenses', [])

        # Convert to License objects
        from src.models.license import License, LicenseType, LicenseFormat, LicenseStatus
        licenses = []
        for lic_data in licenses_data:
            licenses.append(License(
                license_id=lic_data['license_id'],
                name=lic_data['name'],
                owner=lic_data['owner'],
                publisher=lic_data['publisher'],
                license_type=LicenseType(lic_data['license_type']),
                license_format=LicenseFormat(lic_data['license_format']),
                status=LicenseStatus(lic_data['status']),
                file_path=Path(lic_data['file_path']) if lic_data.get('file_path') else None,
                file_hash=lic_data.get('file_hash'),
            ))

        console.print(f"\n[bold]Validating {len(licenses)} licenses...[/bold]")

        # Validate
        validator = LicenseValidator()
        stats = validator.batch_validate(licenses)

        # Display results
        console.print(f"\n[bold green]Validation Complete[/bold green]")
        console.print(f"Valid: [green]{stats['valid']}[/green]")
        console.print(f"Invalid: [red]{stats['invalid']}[/red]")
        console.print(f"Expired: [yellow]{stats['expired']}[/yellow]")

        # Find expiring licenses
        expiring = validator.find_expiring_licenses(licenses, days=30)
        if expiring:
            console.print(f"\n[yellow]Warning: {len(expiring)} licenses expiring within 30 days[/yellow]")

        # Generate report
        report = validator.generate_validation_report(licenses)
        report_path = Path('data/license_validation_report.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        console.print(f"\n[green]✓[/green] Validation report saved to {report_path}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@license.command('ilok')
@click.option('--export', '-e', type=click.Path(), help='Export to file')
def license_ilok(export):
    """Scan for iLok licenses."""
    try:
        console.print("[bold cyan]iLok License Scanner[/bold cyan]")
        console.print("="*50)

        manager = iLokManager()

        # Check if iLok is installed
        info = manager.get_ilok_info()
        if not info['installed']:
            console.print("[yellow]iLok License Manager not found[/yellow]")
            console.print("Please install iLok License Manager from https://www.ilok.com/")
            return

        console.print(f"\n[bold]iLok License Manager found[/bold]")
        console.print(f"Path: {info['installation_path']}")

        # Get iLok licenses
        console.print("\n[bold]Scanning for iLok licenses...[/bold]")
        ilok_licenses = manager.get_ilok_licenses()

        console.print(f"\n[bold green]Found {len(ilok_licenses)} iLok licenses[/bold green]")

        # Display table
        if ilok_licenses:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Product", style="cyan")
            table.add_column("Publisher", style="yellow")
            table.add_column("Location", style="green")
            table.add_column("License ID", style="white")

            for lic in ilok_licenses[:20]:
                table.add_row(
                    lic.product_name,
                    lic.publisher,
                    lic.location,
                    lic.license_id[:16] + "..." if len(lic.license_id) > 16 else lic.license_id
                )

            console.print(table)

            if len(ilok_licenses) > 20:
                console.print(f"\n[yellow]... and {len(ilok_licenses) - 20} more licenses[/yellow]")

        # Export if requested
        if export:
            export_path = Path(export)
            manager.export_ilok_licenses(export_path)
            console.print(f"\n[green]✓[/green] Exported to {export_path}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@license.command('info')
@click.argument('license_file', type=click.Path(exists=True))
@click.argument('license_id')
def license_info(license_file, license_id):
    """Show detailed information about a specific license."""
    try:
        console.print("[bold cyan]License Information[/bold cyan]")
        console.print("="*50)

        # Load licenses
        import json
        with open(license_file, 'r') as f:
            data = json.load(f)
            licenses_data = data.get('licenses', [])

        # Find license
        license_data = None
        for lic in licenses_data:
            if lic['license_id'] == license_id:
                license_data = lic
                break

        if not license_data:
            console.print(f"[red]License not found: {license_id}[/red]")
            return

        # Display info
        console.print(f"\n[bold]License: {license_data['name']}[/bold]")
        console.print(f"ID: {license_data['license_id']}")
        console.print(f"Owner: {license_data['owner']}")
        console.print(f"Publisher: {license_data['publisher']}")
        console.print(f"Type: {license_data['license_type']}")
        console.print(f"Format: {license_data['license_format']}")
        console.print(f"Status: {license_data['status']}")

        if license_data.get('file_path'):
            console.print(f"File: {license_data['file_path']}")

        if license_data.get('expiration_date'):
            console.print(f"Expires: {license_data['expiration_date']}")

        if license_data.get('installation_date'):
            console.print(f"Installed: {license_data['installation_date']}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--scan-file', '-s', type=click.Path(exists=True), help='Scan results file (if not provided, will scan now)')
@click.option('--remove-32bit', is_flag=True, help='Remove 32-bit VST2 plugins')
@click.option('--list-only', is_flag=True, help='Only list 32-bit plugins without removing')
@click.option('--dry-run/--execute', default=True, help='Dry run mode (default: true)')
def cleanup(scan_file, remove_32bit, list_only, dry_run):
    """Cleanup plugins: remove 32-bit VST2 plugins and duplicates."""
    try:
        console.print("[bold cyan]Plugin Cleanup[/bold cyan]")
        console.print("="*50)

        # Load or perform scan
        scan_result = None
        if scan_file:
            console.print(f"\n[bold]Loading scan results from {scan_file}...[/bold]")
            import pickle
            with open(scan_file, 'rb') as f:
                scan_result = pickle.load(f)
        else:
            console.print("\n[bold]No scan file provided. Running quick plugin scan...[/bold]")
            # Run a quick scan
            from pathlib import Path
            config_manager = ConfigManager()
            scanner = FileScanner(
                exclude_paths=config_manager.get_exclude_paths(),
                max_workers=config_manager.get('scan.max_workers', 4),
                verbose=False
            )
            metadata_extractor = MetadataExtractor()

            scan_paths = config_manager.get_scan_paths()
            vst2_ext = ['.dll']
            plugin_files = scanner.scan_parallel(scan_paths, vst2_ext)

            console.print(f"   Found {len(plugin_files)} VST2 files")

            # Build scan result
            from src.models.scan_result import ComprehensiveScanResult
            from datetime import datetime
            import uuid
            scan_result = ComprehensiveScanResult(
                scan_id=str(uuid.uuid4()),
                scan_date=datetime.now(),
            )

            for file_path in plugin_files:
                try:
                    metadata = metadata_extractor.extract_file_metadata(file_path)
                    plugin_type = metadata_extractor.detect_plugin_type(file_path)
                    publisher = metadata_extractor.identify_publisher(file_path)
                    product_name = metadata_extractor.get_product_name(file_path)
                    architecture = metadata_extractor.detect_architecture(file_path)

                    plugin = Plugin(
                        name=product_name,
                        publisher=publisher,
                        plugin_type=plugin_type,
                        file_path=file_path,
                        file_size=metadata['file_size'],
                        file_hash=metadata['file_hash'],
                        architecture=architecture,
                    )
                    scan_result.plugins.append(plugin)
                except Exception as e:
                    pass

        # Find 32-bit plugins
        plugins_32bit = [p for p in scan_result.plugins if p.architecture == 'x86']

        console.print(f"\n[bold]Found {len(plugins_32bit)} 32-bit VST2 plugins[/bold]")

        if not plugins_32bit:
            console.print("[green]No 32-bit plugins found![/green]")
            return

        # Display 32-bit plugins
        console.print(f"\n[yellow]32-bit VST2 Plugins:[/yellow]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Publisher", style="yellow")
        table.add_column("Size", style="blue")
        table.add_column("Path", style="dim")

        total_size = 0
        for plugin in plugins_32bit[:20]:  # Show first 20
            size_mb = round(plugin.file_size / (1024 * 1024), 2)
            total_size += plugin.file_size
            table.add_row(
                plugin.name[:30],
                plugin.publisher[:20],
                f"{size_mb} MB",
                str(plugin.file_path)[:50] if plugin.file_path else ""
            )

        console.print(table)

        if len(plugins_32bit) > 20:
            console.print(f"\n[dim]... and {len(plugins_32bit) - 20} more[/dim]")

        total_size_mb = round(total_size / (1024 * 1024), 2)
        console.print(f"\n[bold]Total size of 32-bit plugins: {total_size_mb} MB[/bold]")

        # If only listing, stop here
        if list_only or not remove_32bit:
            console.print("\n[dim]Use --remove-32bit to remove these plugins[/dim]")
            return

        # Remove 32-bit plugins
        if dry_run:
            console.print(f"\n[yellow]DRY RUN MODE - No files will be removed[/yellow]")
        else:
            if not click.confirm(f'\n[bold red]Remove {len(plugins_32bit)} 32-bit VST2 plugins? This cannot be undone![/bold red]'):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

            console.print(f"\n[bold]Removing 32-bit plugins...[/bold]")

        removed_count = 0
        failed_count = 0

        for plugin in plugins_32bit:
            try:
                if not dry_run:
                    import os
                    if plugin.file_path and plugin.file_path.exists():
                        os.remove(plugin.file_path)
                        removed_count += 1
                else:
                    removed_count += 1
            except Exception as e:
                console.print(f"[red]Failed to remove {plugin.file_path}: {e}[/red]")
                failed_count += 1

        console.print(f"\n[green]✓[/green] Removed {removed_count} plugins")
        if failed_count > 0:
            console.print(f"[red]✗[/red] Failed to remove {failed_count} plugins")

        if dry_run:
            console.print("\n[dim]Run with --execute to actually remove files[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    cli()
