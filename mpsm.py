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
def init(path):
    """Initialize MPSM configuration."""
    try:
        config_path = Path(path) if path else Path('config.yaml')

        if config_path.exists():
            console.print(f"[yellow]Config file already exists: {config_path}[/yellow]")
            if not click.confirm('Overwrite?'):
                return

        config = ConfigManager(config_path)
        config.create_default_config()

        console.print(f"[green]✓[/green] Created configuration file: {config_path}")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Edit config.yaml to customize settings")
        console.print("2. Run 'python mpsm.py scan' to scan your system")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--config', default='config.yaml', help='Config file path')
@click.option('--output', default='data', help='Output directory for results')
@click.option('--format', type=click.Choice(['csv', 'excel', 'both']), default='both', help='Export format')
@click.option('--skip-plugins', is_flag=True, help='Skip plugin file scanning')
@click.option('--skip-apps', is_flag=True, help='Skip application scanning')
@click.option('--skip-folders', is_flag=True, help='Skip data folder scanning')
@click.option('--skip-registry', is_flag=True, help='Skip registry scanning')
@click.option('--skip-licenses', is_flag=True, help='Skip license scanning')
def scan(config, output, format, skip_plugins, skip_apps, skip_folders, skip_registry, skip_licenses):
    """Comprehensive scan for music production software, plugins, DAWs, and data."""
    console.print("[bold cyan]MPSM Comprehensive Scanner[/bold cyan]")
    console.print("="*50)

    try:
        # Load configuration
        console.print(f"\n[bold]Loading configuration...[/bold]")
        config_manager = ConfigManager(Path(config))
        errors = config_manager.validate_config()

        if errors:
            console.print("[red]Configuration errors:[/red]")
            for error in errors:
                console.print(f"  - {error}")
            sys.exit(1)

        console.print("[green]✓[/green] Configuration loaded successfully")

        # Initialize logger
        logger = get_logger(
            level=config_manager.get('logging.level', 'INFO'),
            log_to_console=config_manager.get('logging.log_to_console', True),
            log_to_file=config_manager.get('logging.log_to_file', True),
        )

        # Get scan paths
        scan_paths = config_manager.get_scan_paths()

        # Create scan result
        start_time = datetime.now()
        scan_result = ComprehensiveScanResult(
            scan_id=str(uuid.uuid4()),
            scan_date=datetime.now(),
        )

        console.print(f"\nScan paths: {', '.join(scan_paths)}")

        # ============================================================
        # 1. SCAN FOR PLUGIN FILES (VST2, VST3, AAX, CLAP)
        # ============================================================
        if not skip_plugins:
            console.print(f"\n[bold cyan]1. Scanning for plugin files...[/bold cyan]")

            scanner = FileScanner(
                exclude_paths=config_manager.get_exclude_paths(),
                max_workers=config_manager.get('scan.max_workers', 4),
                verbose=False
            )
            metadata_extractor = MetadataExtractor()

            # Get all plugin extensions
            vst2_ext = config_manager.get('scan.extensions.plugins.vst2', ['.dll'])
            vst3_ext = config_manager.get('scan.extensions.plugins.vst3', ['.vst3'])
            aax_ext = config_manager.get('scan.extensions.plugins.aax', ['.aax'])
            clap_ext = config_manager.get('scan.extensions.plugins.clap', ['.clap'])
            all_extensions = vst2_ext + vst3_ext + aax_ext + clap_ext

            console.print(f"   Extensions: {', '.join(all_extensions)}")

            # Scan for plugins
            plugin_files = scanner.scan_parallel(scan_paths, all_extensions)
            console.print(f"   [green]✓[/green] Found {len(plugin_files)} plugin files")

            # Extract metadata
            console.print(f"   Extracting metadata...")
            for i, file_path in enumerate(plugin_files):
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

                    if (i + 1) % 50 == 0:
                        console.print(f"   Processed {i + 1}/{len(plugin_files)} files...", end='\r')

                except Exception as e:
                    logger.warning(f"Failed to extract metadata from {file_path}: {e}")

            scan_result.total_files_scanned = scanner.files_scanned
            console.print(f"   [green]✓[/green] Processed {len(scan_result.plugins)} plugins")

        # ============================================================
        # 2. SCAN FOR APPLICATIONS (DAWs, Plugin Managers, Standalone)
        # ============================================================
        if not skip_apps:
            console.print(f"\n[bold cyan]2. Scanning for applications (DAWs, plugin managers)...[/bold cyan]")

            app_scanner = ApplicationScanner(config=config_manager)
            applications = app_scanner.scan_for_applications()
            scan_result.applications = applications

            console.print(f"   [green]✓[/green] Found {len(applications)} applications")

            # Show breakdown
            daws = app_scanner.find_daws()
            managers = app_scanner.find_plugin_managers()
            standalone = app_scanner.find_standalone_plugins()

            console.print(f"      - DAWs: {len(daws)}")
            console.print(f"      - Plugin Managers: {len(managers)}")
            console.print(f"      - Standalone Plugins: {len(standalone)}")

        # ============================================================
        # 3. SCAN FOR DATA FOLDERS (Presets, Samples, Libraries)
        # ============================================================
        if not skip_folders:
            console.print(f"\n[bold cyan]3. Scanning for data folders (presets, samples, libraries)...[/bold cyan]")

            folder_scanner = FolderScanner(config=config_manager)
            data_folders = folder_scanner.scan_for_data_folders()
            scan_result.data_folders = data_folders

            console.print(f"   [green]✓[/green] Found {len(data_folders)} data folders")

            # Show breakdown
            presets = folder_scanner.find_preset_folders()
            samples = folder_scanner.find_sample_folders()
            libraries = folder_scanner.find_library_folders()

            console.print(f"      - Presets: {len(presets)}")
            console.print(f"      - Samples: {len(samples)}")
            console.print(f"      - Libraries: {len(libraries)}")

        # ============================================================
        # 4. SCAN REGISTRY (Windows only)
        # ============================================================
        if not skip_registry:
            console.print(f"\n[bold cyan]4. Scanning Windows Registry...[/bold cyan]")

            try:
                registry_reader = RegistryReader()
                registry_entries = registry_reader.scan_all_music_production_keys()
                scan_result.total_registry_entries = sum(len(entries) for entries in registry_entries.values())

                console.print(f"   [green]✓[/green] Found {len(registry_entries)} registry keys with {scan_result.total_registry_entries} entries")
            except Exception as e:
                console.print(f"   [yellow]⚠[/yellow] Registry scanning skipped: {e}")

        # ============================================================
        # 5. SCAN FOR LICENSES
        # ============================================================
        if not skip_licenses:
            console.print(f"\n[bold cyan]5. Scanning for licenses...[/bold cyan]")

            try:
                license_scanner = LicenseScanner(config=config_manager)
                license_result = license_scanner.scan_for_licenses()
                scan_result.licenses = license_result.licenses

                console.print(f"   [green]✓[/green] Found {len(license_result.licenses)} licenses")

                # Show breakdown by format
                if license_result.licenses_by_format:
                    for fmt, count in license_result.licenses_by_format.items():
                        console.print(f"      - {fmt.value}: {count}")
            except Exception as e:
                console.print(f"   [yellow]⚠[/yellow] License scanning skipped: {e}")

        # ============================================================
        # FINALIZE SCAN
        # ============================================================
        scan_result.scan_duration = (datetime.now() - start_time).total_seconds()
        scan_result.calculate_statistics()

        # Display comprehensive summary
        console.print(f"\n[bold green]{'='*50}[/bold green]")
        console.print(f"[bold green]Scan Complete![/bold green]")
        console.print(f"[bold green]{'='*50}[/bold green]")
        console.print(scan_result.generate_summary())

        # Export results
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"\n[bold]Exporting results...[/bold]")

        if format in ['csv', 'both']:
            scan_result.export_csv(output_dir)
            console.print(f"[green]✓[/green] Exported CSV files to {output_dir}/")

        if format in ['excel', 'both']:
            excel_path = output_dir / f"scan_results_{scan_result.scan_id[:8]}.xlsx"
            scan_result.export_excel(excel_path)
            console.print(f"[green]✓[/green] Exported Excel file to {excel_path}")

        # Save scan result as JSON for later use
        import json
        json_path = output_dir / f"scan_result_{scan_result.scan_id[:8]}.json"
        with open(json_path, 'w') as f:
            json.dump(scan_result.get_summary_dict(), f, indent=2)
        console.print(f"[green]✓[/green] Saved scan metadata to {json_path}")

        # Display sample results
        _display_scan_samples(scan_result)

        console.print(f"\n[bold green]✓ Comprehensive scan completed successfully![/bold green]")
        console.print(f"[dim]Duration: {scan_result.scan_duration:.2f}s[/dim]")

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


if __name__ == '__main__':
    cli()
