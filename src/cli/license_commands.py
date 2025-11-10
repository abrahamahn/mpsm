"""License commands - manage software licenses."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..core.config import ConfigManager
from ..core.logger import get_logger
from ..license.ilok_manager import iLokManager
from ..license.license_scanner import LicenseScanner
from ..license.license_validator import LicenseValidator

console = Console()


@click.group()
def license():
    """License management commands."""
    pass


@license.command("scan")
@click.option("--config", default="config.yaml", help="Config file path")
@click.option("--output", "-o", default="data/licenses.json", help="Output file path")
@click.option(
    "--format", type=click.Choice(["json", "csv", "excel"]), default="json", help="Output format"
)
def license_scan(config, output, format):
    """Scan for license files."""
    try:
        console.print("[bold cyan]License Scanner[/bold cyan]")
        console.print("=" * 50)

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
                str(lic.file_path) if lic.file_path else "N/A",
            )

        console.print(table)

        if result.total_licenses > 15:
            console.print(f"\n[yellow]... and {result.total_licenses - 15} more licenses[/yellow]")

        # Export
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            import json

            with open(output_path, "w") as f:
                json.dump(
                    {
                        "scan_result": result.to_dict(),
                        "licenses": [lic.to_dict() for lic in result.licenses],
                    },
                    f,
                    indent=2,
                )
            console.print(f"\n[green]✓[/green] Exported to {output_path}")

        elif format == "csv":
            import pandas as pd

            df = pd.DataFrame([lic.to_dict() for lic in result.licenses])
            df.to_csv(output_path.with_suffix(".csv"), index=False)
            console.print(f"\n[green]✓[/green] Exported to {output_path.with_suffix('.csv')}")

        elif format == "excel":
            import pandas as pd

            df = pd.DataFrame([lic.to_dict() for lic in result.licenses])
            df.to_excel(output_path.with_suffix(".xlsx"), index=False)
            console.print(f"\n[green]✓[/green] Exported to {output_path.with_suffix('.xlsx')}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@license.command("validate")
@click.argument("license_file", type=click.Path(exists=True))
def license_validate(license_file):
    """Validate licenses from scan results."""
    try:
        console.print("[bold cyan]License Validator[/bold cyan]")
        console.print("=" * 50)

        # Load licenses from file
        import json

        with open(license_file, "r") as f:
            data = json.load(f)
            licenses_data = data.get("licenses", [])

        # Convert to License objects
        from src.models.license import License, LicenseFormat, LicenseStatus, LicenseType

        licenses = []
        for lic_data in licenses_data:
            licenses.append(
                License(
                    license_id=lic_data["license_id"],
                    name=lic_data["name"],
                    owner=lic_data["owner"],
                    publisher=lic_data["publisher"],
                    license_type=LicenseType(lic_data["license_type"]),
                    license_format=LicenseFormat(lic_data["license_format"]),
                    status=LicenseStatus(lic_data["status"]),
                    file_path=Path(lic_data["file_path"]) if lic_data.get("file_path") else None,
                    file_hash=lic_data.get("file_hash"),
                )
            )

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
            console.print(
                f"\n[yellow]Warning: {len(expiring)} licenses expiring within 30 days[/yellow]"
            )

        # Generate report
        report = validator.generate_validation_report(licenses)
        report_path = Path("data/license_validation_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        console.print(f"\n[green]✓[/green] Validation report saved to {report_path}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@license.command("ilok")
@click.option("--export", "-e", type=click.Path(), help="Export to file")
def license_ilok(export):
    """Scan for iLok licenses."""
    try:
        console.print("[bold cyan]iLok License Scanner[/bold cyan]")
        console.print("=" * 50)

        manager = iLokManager()

        # Check if iLok is installed
        info = manager.get_ilok_info()
        if not info["installed"]:
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
                    lic.license_id[:16] + "..." if len(lic.license_id) > 16 else lic.license_id,
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


@license.command("info")
@click.argument("license_file", type=click.Path(exists=True))
@click.argument("license_id")
def license_info(license_file, license_id):
    """Show detailed information about a specific license."""
    try:
        console.print("[bold cyan]License Information[/bold cyan]")
        console.print("=" * 50)

        # Load licenses
        import json

        with open(license_file, "r") as f:
            data = json.load(f)
            licenses_data = data.get("licenses", [])

        # Find license
        license_data = None
        for lic in licenses_data:
            if lic["license_id"] == license_id:
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

        if license_data.get("file_path"):
            console.print(f"File: {license_data['file_path']}")

        if license_data.get("expiration_date"):
            console.print(f"Expires: {license_data['expiration_date']}")

        if license_data.get("installation_date"):
            console.print(f"Installed: {license_data['installation_date']}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@license.command("cleanup")
@click.option(
    "--scan-file",
    "-s",
    type=click.Path(exists=True),
    help="Scan results file (if not provided, will scan now)",
)
@click.option("--remove-32bit", is_flag=True, help="Remove 32-bit VST2 plugins")
@click.option("--list-only", is_flag=True, help="Only list 32-bit plugins without removing")
@click.option("--dry-run/--execute", default=True, help="Dry run mode (default: true)")
def license_cleanup(scan_file, remove_32bit, list_only, dry_run):
    """Cleanup plugins: remove 32-bit VST2 plugins and duplicates."""
    try:
        console.print("[bold cyan]Plugin Cleanup[/bold cyan]")
        console.print("=" * 50)

        # Load or perform scan
        scan_result = None
        if scan_file:
            console.print(f"\n[bold]Loading scan results from {scan_file}...[/bold]")
            import pickle

            with open(scan_file, "rb") as f:
                scan_result = pickle.load(f)
        else:
            console.print("\n[bold]No scan file provided. Running quick plugin scan...[/bold]")
            # Run a quick scan
            from pathlib import Path

            config_manager = ConfigManager()
            scanner = FileScanner(
                exclude_paths=config_manager.get_exclude_paths(),
                max_workers=config_manager.get("scan.max_workers", 4),
                verbose=False,
            )
            metadata_extractor = MetadataExtractor()

            scan_paths = config_manager.get_scan_paths()
            vst2_ext = [".dll"]
            plugin_files = scanner.scan_parallel(scan_paths, vst2_ext)

            console.print(f"   Found {len(plugin_files)} VST2 files")

            # Build scan result
            import uuid
            from datetime import datetime

            from src.models.scan_result import ComprehensiveScanResult

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
                        file_size=metadata["file_size"],
                        file_hash=metadata["file_hash"],
                        architecture=architecture,
                    )
                    scan_result.plugins.append(plugin)
                except Exception as e:
                    pass

        # Find 32-bit plugins
        plugins_32bit = [p for p in scan_result.plugins if p.architecture == "x86"]

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
                str(plugin.file_path)[:50] if plugin.file_path else "",
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
            if not click.confirm(
                f"\n[bold red]Remove {len(plugins_32bit)} 32-bit VST2 plugins? This cannot be undone![/bold red]"
            ):
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


# Note: This module is imported by src/cli/__init__.py
# Run commands via: python mpsm.py license <subcommand>
