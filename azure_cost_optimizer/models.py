"""Data models for Azure cost optimization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Severity level of a cost finding."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @property
    def icon(self) -> str:
        return {
            Severity.HIGH: "[red]!!![/red]",
            Severity.MEDIUM: "[yellow]!![/yellow]",
            Severity.LOW: "[blue]![/blue]",
        }[self]

    @property
    def sort_key(self) -> int:
        return {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}[self]


class Category(str, Enum):
    """Category of the Azure resource being analyzed."""

    COMPUTE = "Compute"
    STORAGE = "Storage"
    NETWORKING = "Networking"
    DATABASE = "Database"
    GENERAL = "General"

    @property
    def icon(self) -> str:
        return {
            Category.COMPUTE: "[cyan]VM[/cyan]",
            Category.STORAGE: "[magenta]DSK[/magenta]",
            Category.NETWORKING: "[green]NET[/green]",
            Category.DATABASE: "[yellow]DB[/yellow]",
            Category.GENERAL: "[dim]GEN[/dim]",
        }[self]


@dataclass
class CostFinding:
    """A single cost optimization finding."""

    title: str
    description: str
    severity: Severity
    category: Category
    resource_name: str
    resource_group: str
    resource_type: str
    current_cost_monthly: float
    projected_savings_monthly: float
    recommendation: str
    effort: str = "Low"  # Low | Medium | High
    region: str = ""

    @property
    def savings_pct(self) -> float:
        if self.current_cost_monthly <= 0:
            return 0.0
        return (self.projected_savings_monthly / self.current_cost_monthly) * 100

    @property
    def annual_savings(self) -> float:
        return self.projected_savings_monthly * 12


@dataclass
class SubscriptionSummary:
    """Summary of the Azure subscription being analyzed."""

    subscription_id: str
    subscription_name: str
    total_monthly_cost: float
    resource_count: int
    resource_group_count: int
    region_count: int
    top_regions: list[str] = field(default_factory=list)
    cost_by_service: dict[str, float] = field(default_factory=dict)


@dataclass
class OptimizationReport:
    """Complete cost optimization report."""

    subscription: SubscriptionSummary
    findings: list[CostFinding] = field(default_factory=list)
    scan_duration: float = 0.0

    @property
    def total_monthly_savings(self) -> float:
        return sum(f.projected_savings_monthly for f in self.findings)

    @property
    def total_annual_savings(self) -> float:
        return self.total_monthly_savings * 12

    @property
    def savings_pct(self) -> float:
        if self.subscription.total_monthly_cost <= 0:
            return 0.0
        return (self.total_monthly_savings / self.subscription.total_monthly_cost) * 100

    @property
    def high_findings(self) -> list[CostFinding]:
        return [f for f in self.findings if f.severity == Severity.HIGH]

    @property
    def medium_findings(self) -> list[CostFinding]:
        return [f for f in self.findings if f.severity == Severity.MEDIUM]

    @property
    def low_findings(self) -> list[CostFinding]:
        return [f for f in self.findings if f.severity == Severity.LOW]

    @property
    def findings_by_category(self) -> dict[Category, list[CostFinding]]:
        result: dict[Category, list[CostFinding]] = {}
        for f in self.findings:
            result.setdefault(f.category, []).append(f)
        return result

    @property
    def savings_by_category(self) -> dict[Category, float]:
        result: dict[Category, float] = {}
        for f in self.findings:
            result[f.category] = result.get(f.category, 0) + f.projected_savings_monthly
        return result

    def to_dict(self) -> dict:
        """Serialize report to a dictionary."""
        return {
            "subscription": {
                "id": self.subscription.subscription_id,
                "name": self.subscription.subscription_name,
                "total_monthly_cost": round(self.subscription.total_monthly_cost, 2),
                "resource_count": self.subscription.resource_count,
            },
            "summary": {
                "total_findings": len(self.findings),
                "high": len(self.high_findings),
                "medium": len(self.medium_findings),
                "low": len(self.low_findings),
                "total_monthly_savings": round(self.total_monthly_savings, 2),
                "total_annual_savings": round(self.total_annual_savings, 2),
                "savings_pct": round(self.savings_pct, 1),
            },
            "findings": [
                {
                    "title": f.title,
                    "severity": f.severity.value,
                    "category": f.category.value,
                    "resource_name": f.resource_name,
                    "resource_group": f.resource_group,
                    "resource_type": f.resource_type,
                    "current_cost_monthly": round(f.current_cost_monthly, 2),
                    "projected_savings_monthly": round(f.projected_savings_monthly, 2),
                    "annual_savings": round(f.annual_savings, 2),
                    "recommendation": f.recommendation,
                    "effort": f.effort,
                }
                for f in self.findings
            ],
        }
