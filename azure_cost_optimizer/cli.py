"""CLI entry point — Click commands for azure-cost-optimizer."""

from __future__ import annotations

import click

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="azure-cost-optimizer")
def cli() -> None:
    """Azure Cost Optimizer — Analyze Azure resources and find cost savings."""


@cli.command()
@click.option(
    "--demo",
    is_flag=True,
    default=False,
    help="Run with demo data (no Azure credentials required).",
)
@click.option(
    "--export-json",
    type=click.Path(),
    default=None,
    help="Export results to a JSON file.",
)
@click.option(
    "--export-csv",
    type=click.Path(),
    default=None,
    help="Export findings to a CSV file.",
)
@click.option(
    "--severity",
    type=click.Choice(["HIGH", "MEDIUM", "LOW"], case_sensitive=False),
    default=None,
    help="Filter findings by minimum severity.",
)
@click.option(
    "--category",
    type=click.Choice(
        ["COMPUTE", "STORAGE", "NETWORKING", "DATABASE", "GENERAL"],
        case_sensitive=False,
    ),
    default=None,
    help="Filter findings by category.",
)
def scan(
    demo: bool,
    export_json: str | None,
    export_csv: str | None,
    severity: str | None,
    category: str | None,
) -> None:
    """Scan Azure resources for cost optimization opportunities."""
    from .demo import get_demo_resources, get_demo_subscription
    from .models import Category, Severity
    from .output.console import render_report
    from .output.report import export_csv as do_export_csv
    from .output.report import export_json as do_export_json
    from .scanner import CostScanner

    if not demo:
        click.echo(
            "Live Azure scanning requires azure-identity and azure-mgmt packages.\n"
            "Install with: pip install azure-cost-optimizer[azure]\n\n"
            "For a demo, run: azure-cost scan --demo"
        )
        raise SystemExit(1)

    # Demo mode
    subscription = get_demo_subscription()
    resources = get_demo_resources()

    scanner = CostScanner()
    report = scanner.scan(resources, subscription)

    # Apply severity filter
    if severity:
        min_sev = Severity[severity.upper()]
        report.findings = [
            f for f in report.findings if f.severity.sort_key <= min_sev.sort_key
        ]

    # Apply category filter
    if category:
        target_cat = Category[category.upper()]
        report.findings = [
            f for f in report.findings if f.category == target_cat
        ]

    # Render to terminal
    render_report(report)

    # Export if requested
    if export_json:
        path = do_export_json(report, export_json)
        click.echo(f"JSON report exported to: {path}")

    if export_csv:
        path = do_export_csv(report, export_csv)
        click.echo(f"CSV report exported to: {path}")


@cli.command()
def summary() -> None:
    """Show a quick summary of what azure-cost-optimizer checks."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    console.print()

    table = Table(
        title="Azure Cost Optimizer — Checks Overview",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        show_lines=True,
    )
    table.add_column("Category", style="bold", min_width=12)
    table.add_column("Check", min_width=30)
    table.add_column("Severity", justify="center", width=10)

    checks = [
        ("Compute", "Stopped but allocated VMs", "HIGH"),
        ("Compute", "Idle VMs (< 5% CPU)", "HIGH"),
        ("Compute", "Underutilized VMs (< 20% CPU)", "MEDIUM"),
        ("Compute", "Dev/test VMs without auto-shutdown", "MEDIUM"),
        ("Compute", "Reserved Instance candidates", "LOW"),
        ("Compute", "Scale sets with fixed instance count", "MEDIUM"),
        ("Compute", "Overprovisioned App Services", "HIGH"),
        ("Storage", "Unattached managed disks", "HIGH"),
        ("Storage", "Premium disks with low IOPS", "MEDIUM"),
        ("Storage", "Old snapshots (> 90 days)", "MEDIUM"),
        ("Storage", "Aging snapshots (> 30 days)", "LOW"),
        ("Storage", "Hot storage with infrequent access", "MEDIUM"),
        ("Networking", "Orphaned public IP addresses", "HIGH"),
        ("Networking", "Load balancers with no backends", "HIGH"),
        ("Networking", "Load balancers with no rules", "MEDIUM"),
        ("Networking", "Unused NAT Gateways", "HIGH"),
        ("Networking", "Oversized Application Gateways", "MEDIUM"),
        ("Database", "Oversized SQL Databases", "HIGH"),
        ("Database", "SQL storage over-provisioned", "LOW"),
        ("Database", "Dev/test DBs on production SKUs", "HIGH"),
        ("Database", "Idle Cosmos DB accounts", "HIGH"),
        ("Database", "Over-provisioned Cosmos DB RUs", "MEDIUM"),
        ("Database", "Oversized Redis Cache", "MEDIUM"),
        ("Database", "Idle Redis Cache", "HIGH"),
        ("Database", "Underutilized MySQL servers", "MEDIUM"),
        ("General", "Empty resource groups", "LOW"),
        ("General", "High-cost untagged resources", "MEDIUM"),
        ("General", "Untagged resources", "LOW"),
        ("General", "Resources in expensive regions", "LOW"),
        ("General", "Long-running resources (> 1 year)", "LOW"),
    ]

    severity_styles = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "cyan"}
    for cat, check, sev in checks:
        style = severity_styles.get(sev, "white")
        table.add_row(cat, check, f"[{style}]{sev}[/{style}]")

    console.print(table)
    console.print(f"\n[dim]Total checks: {len(checks)}[/dim]\n")
