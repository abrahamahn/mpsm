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
from src.core.exceptions import MPSMException
from src.scanner.file_scanner import FileScanner
from src.scanner.metadata_extractor import MetadataExtractor
from src.models.plugin import Plugin, PluginType, PluginCategory
from src.models.scan_result import ComprehensiveScanResult

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


if __name__ == '__main__':
    cli()
