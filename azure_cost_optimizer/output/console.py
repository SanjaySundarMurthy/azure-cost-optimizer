"""Rich console output — beautiful terminal rendering of cost reports."""

from __future__ import annotations

import io
import sys
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from ..models import OptimizationReport


def _ensure_utf8() -> None:
    """Force UTF-8 on Windows to avoid emoji encoding errors."""
    if sys.platform != "win32":
        return
    try:
        if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "") != "utf-8":
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
        if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "") != "utf-8":
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf-8", errors="replace"
            )
    except (AttributeError, ValueError):
        pass


def _severity_style(severity_name: str) -> str:
    styles = {
        "HIGH": "bold red",
        "MEDIUM": "bold yellow",
        "LOW": "bold cyan",
    }
    return styles.get(severity_name, "white")


def _grade(savings_pct: float) -> tuple[str, str]:
    """Return a letter grade and color based on savings percentage."""
    if savings_pct >= 40:
        return "F", "bold red"
    if savings_pct >= 25:
        return "D", "bold red"
    if savings_pct >= 15:
        return "C", "bold yellow"
    if savings_pct >= 8:
        return "B", "bold green"
    return "A", "bold green"


def render_report(report: OptimizationReport) -> None:
    """Render the full optimization report to the terminal."""
    _ensure_utf8()
    console = Console()
    sub = report.subscription

    # ── Header ─────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                f"[bold cyan]Azure Cost Optimizer[/bold cyan]\n"
                f"Subscription: [white]{sub.subscription_name}[/white]  "
                f"([dim]{sub.subscription_id}[/dim])\n"
                f"Resources: [white]{sub.resource_count}[/white]  |  "
                f"Resource Groups: [white]{sub.resource_group_count}[/white]  |  "
                f"Regions: [white]{sub.region_count}[/white]"
            ),
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # ── Cost Breakdown by Service ──────────────────────────────
    if sub.cost_by_service:
        svc_table = Table(
            title="Monthly Cost by Service",
            show_header=True,
            header_style="bold magenta",
            border_style="dim",
            padding=(0, 1),
        )
        svc_table.add_column("Service", style="white", min_width=25)
        svc_table.add_column("Monthly Cost", style="green", justify="right")
        svc_table.add_column("% of Total", justify="right")

        total = sub.total_monthly_cost or 1.0
        sorted_services = sorted(
            sub.cost_by_service.items(), key=lambda x: x[1], reverse=True
        )
        for svc, cost in sorted_services:
            pct = (cost / total) * 100
            bar_len = int(pct / 3)
            bar = "[green]" + "|" * bar_len + "[/green]"
            svc_table.add_row(svc, f"${cost:,.2f}", f"{pct:.1f}% {bar}")

        svc_table.add_section()
        svc_table.add_row(
            "[bold]Total[/bold]",
            f"[bold]${total:,.2f}[/bold]",
            "[bold]100.0%[/bold]",
        )
        console.print(svc_table)
        console.print()

    # ── Summary Metrics ────────────────────────────────────────
    grade, grade_style = _grade(report.savings_pct)
    savings_panel_text = (
        f"[bold]Optimization Grade:[/bold] [{grade_style}]{grade}[/{grade_style}]\n\n"
        f"[bold]Total Findings:[/bold]  {len(report.findings)}\n"
        f"  [red]HIGH[/red]:   {len(report.high_findings)}\n"
        f"  [yellow]MEDIUM[/yellow]: {len(report.medium_findings)}\n"
        f"  [cyan]LOW[/cyan]:    {len(report.low_findings)}\n\n"
        f"[bold]Current Monthly Spend:[/bold]  [white]${sub.total_monthly_cost:,.2f}[/white]\n"
        f"[bold]Potential Monthly Savings:[/bold]  [green]${report.total_monthly_savings:,.2f}[/green]\n"
        f"[bold]Potential Annual Savings:[/bold]   [green]${report.total_annual_savings:,.2f}[/green]\n"
        f"[bold]Savings Opportunity:[/bold]        [{grade_style}]{report.savings_pct:.1f}%[/{grade_style}]"
    )
    console.print(
        Panel(
            Text.from_markup(savings_panel_text),
            title="Optimization Summary",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()

    # ── Savings by Category ────────────────────────────────────
    cat_table = Table(
        title="Savings by Category",
        show_header=True,
        header_style="bold blue",
        border_style="dim",
    )
    cat_table.add_column("Category", style="white", min_width=15)
    cat_table.add_column("Findings", justify="center")
    cat_table.add_column("Monthly Savings", style="green", justify="right")
    cat_table.add_column("Annual Savings", style="green", justify="right")

    for cat, cat_savings in sorted(
        report.savings_by_category.items(), key=lambda x: x[1], reverse=True
    ):
        cat_findings = report.findings_by_category.get(cat, [])
        cat_table.add_row(
            cat.value,
            str(len(cat_findings)),
            f"${cat_savings:,.2f}",
            f"${cat_savings * 12:,.2f}",
        )

    console.print(cat_table)
    console.print()

    # ── Detailed Findings ──────────────────────────────────────
    if not report.findings:
        console.print(
            Panel(
                "[bold green]No optimization findings! Your Azure spend looks efficient.[/bold green]",
                border_style="green",
            )
        )
        return

    findings_table = Table(
        title=f"Detailed Findings ({len(report.findings)})",
        show_header=True,
        header_style="bold white",
        border_style="dim",
        show_lines=True,
        padding=(0, 1),
    )
    findings_table.add_column("#", style="dim", width=3, justify="right")
    findings_table.add_column("Sev", width=8, justify="center")
    findings_table.add_column("Category", width=12)
    findings_table.add_column("Resource", style="white", min_width=20)
    findings_table.add_column("Finding", min_width=30)
    findings_table.add_column("Savings/mo", justify="right", style="green")
    findings_table.add_column("Effort", width=8, justify="center")

    for i, f in enumerate(report.findings, 1):
        sev_text = Text(f"{f.severity.icon} {f.severity.value}")
        sev_text.stylize(_severity_style(f.severity.value))

        findings_table.add_row(
            str(i),
            sev_text,
            f"{f.category.icon} {f.category.value}",
            f.resource_name,
            f.title,
            f"${f.projected_savings_monthly:,.2f}",
            f.effort,
        )

    console.print(findings_table)
    console.print()

    # ── Top Recommendations ────────────────────────────────────
    top = [f for f in report.findings if f.projected_savings_monthly > 0][:5]
    if top:
        rec_table = Table(
            title="Top 5 Recommendations (by savings)",
            show_header=True,
            header_style="bold green",
            border_style="dim",
            show_lines=True,
        )
        rec_table.add_column("#", width=3, justify="right", style="dim")
        rec_table.add_column("Resource", min_width=20)
        rec_table.add_column("Recommendation", min_width=40)
        rec_table.add_column("Savings/mo", justify="right", style="green")
        rec_table.add_column("Effort", width=8, justify="center")

        for i, f in enumerate(top, 1):
            rec_table.add_row(
                str(i),
                f.resource_name,
                f.recommendation,
                f"${f.projected_savings_monthly:,.2f}",
                f.effort,
            )

        console.print(rec_table)

    # ── Footer ─────────────────────────────────────────────────
    console.print()
    console.print(
        f"[dim]Scan completed in {report.scan_duration:.2f}s  |  "
        f"azure-cost-optimizer v0.1.0[/dim]"
    )
    console.print()
