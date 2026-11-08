"""Scan reporting, console summary tables, and export helpers."""

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..models.scan_result import ComprehensiveScanResult


def display_scan_summary(console: Console, scan_result: ComprehensiveScanResult) -> None:
    """Display comprehensive scan completion banner and component counts."""
    console.print()
    console.print(
        Panel.fit(
            f"[bold green]✓ Scan Complete![/bold green]\n"
            f"[dim]Duration: {scan_result.scan_duration:.1f}s[/dim]",
            border_style="green",
        )
    )
    console.print()

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


def export_scan_results(
    console: Console,
    scan_result: ComprehensiveScanResult,
    output_dir: Path,
    export_format: str,
) -> None:
    """Export scan results to CSV, Excel, and JSON summary files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print("[bold]📁 Exporting Results[/bold]")

    if export_format in ["csv", "both"]:
        scan_result.export_csv(output_dir)
        console.print(f"  ✓ CSV files → [cyan]{output_dir}/[/cyan]")

    if export_format in ["excel", "both"]:
        excel_path = output_dir / f"scan_results_{scan_result.scan_id[:8]}.xlsx"
        scan_result.export_excel(excel_path)
        console.print(f"  ✓ Excel file → [cyan]{excel_path.name}[/cyan]")

    json_path = output_dir / f"scan_result_{scan_result.scan_id[:8]}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scan_result.get_summary_dict(), f, indent=2)
    console.print(f"  ✓ JSON metadata → [cyan]{json_path.name}[/cyan]")
    console.print()


def display_scan_samples(console: Console, scan_result: ComprehensiveScanResult) -> None:
    """Display sample tables of discovered plugins, applications, and data folders."""
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
                plugin.name[:40],
                plugin.publisher[:20],
                plugin.plugin_type.value,
                f"{size_mb} MB",
            )
        console.print(table)

    if scan_result.applications:
        console.print("\n[bold]Sample Applications (showing first 10):[/bold]")
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
                str(app.version) if app.version else "N/A",
            )
        console.print(table)

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
                (folder.name or "")[:40],
                (folder.owner or "")[:20],
                folder.folder_type.value,
                f"{size_gb} GB",
            )
        console.print(table)
