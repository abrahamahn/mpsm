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
from src.models.plugin import Plugin, PluginType, PluginCategory
from src.models.scan_result import ComprehensiveScanResult
from src.registry.registry_reader import RegistryReader
from src.registry.manager import RegistryManager
from src.registry.validator import PathValidator
from src.organizer.structure_builder import StructureBuilder
from src.organizer.file_mover import FileMover
from src.organizer.consolidator import Consolidator

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
def scan(config, output, format):
    """Scan system for music production software."""
    console.print("[bold cyan]MPSM Scanner[/bold cyan]")
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

        # Initialize scanner
        console.print(f"\n[bold]Initializing scanner...[/bold]")
        scanner = FileScanner(
            exclude_paths=config_manager.get_exclude_paths(),
            max_workers=config_manager.get('scan.max_workers', 4),
            verbose=True
        )

        metadata_extractor = MetadataExtractor()

        # Get scan paths
        scan_paths = config_manager.get_scan_paths()
        console.print(f"[green]✓[/green] Scanner initialized")
        console.print(f"Scan paths: {', '.join(scan_paths)}")

        # Get plugin extensions
        vst2_ext = config_manager.get('scan.extensions.plugins.vst2', ['.dll'])
        vst3_ext = config_manager.get('scan.extensions.plugins.vst3', ['.vst3'])
        all_extensions = vst2_ext + vst3_ext

        console.print(f"Extensions: {', '.join(all_extensions)}")

        # Start scan
        console.print(f"\n[bold]Scanning for plugins...[/bold]")
        start_time = datetime.now()

        # Scan for plugins
        plugin_files = scanner.scan_parallel(scan_paths, all_extensions)

        # Create scan result
        scan_result = ComprehensiveScanResult(
            scan_id=str(uuid.uuid4()),
            scan_date=datetime.now(),
            scan_duration=(datetime.now() - start_time).total_seconds(),
        )

        console.print(f"\n[green]✓[/green] Found {len(plugin_files)} plugin files")

        # Extract metadata and create plugin objects
        console.print(f"\n[bold]Extracting metadata...[/bold]")

        for file_path in plugin_files:
            try:
                # Extract metadata
                metadata = metadata_extractor.extract_file_metadata(file_path)
                plugin_type = metadata_extractor.detect_plugin_type(file_path)
                publisher = metadata_extractor.identify_publisher(file_path)
                product_name = metadata_extractor.get_product_name(file_path)

                # Create plugin object
                plugin = Plugin(
                    name=product_name,
                    publisher=publisher,
                    plugin_type=plugin_type,
                    file_path=file_path,
                    file_size=metadata['file_size'],
                    file_hash=metadata['file_hash'],
                )

                scan_result.plugins.append(plugin)

            except Exception as e:
                logger.warning(f"Failed to extract metadata from {file_path}: {e}")

        # Update statistics
        scan_result.total_files_scanned = scanner.files_scanned
        scan_result.calculate_statistics()

        # Display summary
        console.print(f"\n[bold green]Scan Complete![/bold green]")
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

        # Display sample plugins
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
                    plugin.name,
                    plugin.publisher,
                    plugin.plugin_type.value,
                    f"{size_mb} MB"
                )

            console.print(table)

        console.print(f"\n[bold green]✓ Scan completed successfully![/bold green]")

    except MPSMException as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


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


if __name__ == '__main__':
    cli()
