"""Report export — JSON and CSV output formats."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import OptimizationReport


def export_json(report: OptimizationReport, output_path: str) -> Path:
    """Export the optimization report as a JSON file."""
    path = Path(output_path)
    data = report.to_dict()
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return path


def export_csv(report: OptimizationReport, output_path: str) -> Path:
    """Export the findings as a CSV file."""
    path = Path(output_path)
    fieldnames = [
        "severity",
        "category",
        "title",
        "resource_name",
        "resource_group",
        "resource_type",
        "region",
        "current_cost_monthly",
        "projected_savings_monthly",
        "annual_savings",
        "savings_pct",
        "recommendation",
        "effort",
        "description",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for finding in report.findings:
            writer.writerow({
                "severity": finding.severity.value,
                "category": finding.category.value,
                "title": finding.title,
                "resource_name": finding.resource_name,
                "resource_group": finding.resource_group,
                "resource_type": finding.resource_type,
                "region": finding.region,
                "current_cost_monthly": f"{finding.current_cost_monthly:.2f}",
                "projected_savings_monthly": f"{finding.projected_savings_monthly:.2f}",
                "annual_savings": f"{finding.annual_savings:.2f}",
                "savings_pct": f"{finding.savings_pct:.1f}",
                "recommendation": finding.recommendation,
                "effort": finding.effort,
                "description": finding.description,
            })

    return path
