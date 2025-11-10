"""Organize command - consolidate and organize music production software."""

import sys
import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.config import ConfigManager
from ..core.logger import get_logger
from ..models.scan_result import ComprehensiveScanResult
from ..organizer.structure_builder import StructureBuilder
from ..organizer.file_mover import FileMover
from ..organizer.consolidator import Consolidator

console = Console()
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


