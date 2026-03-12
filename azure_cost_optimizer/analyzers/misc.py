"""General / miscellaneous cost analyzer — resource groups, tags, regions."""

from __future__ import annotations

from ..models import Category, CostFinding, Severity
from .base import BaseAnalyzer

# Azure regions ordered roughly by pricing tier (most expensive first)
EXPENSIVE_REGIONS = {
    "brazilsouth",
    "australiaeast",
    "australiasoutheast",
    "japaneast",
    "japanwest",
    "southafricanorth",
    "uaenorth",
    "switzerlandnorth",
    "norwayeast",
}


class GeneralAnalyzer(BaseAnalyzer):
    """Analyze general resource hygiene for cost optimization."""

    @property
    def name(self) -> str:
        return "General Analyzer"

    @property
    def category(self) -> Category:
        return Category.GENERAL

    def analyze(self, resources: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []

        for rg in resources.get("resource_groups", []):
            findings.extend(self._check_resource_group(rg))

        for res in resources.get("untagged_resources", []):
            findings.extend(self._check_untagged_resource(res))

        for res in resources.get("expensive_region_resources", []):
            findings.extend(self._check_expensive_region(res))

        for res in resources.get("old_resources", []):
            findings.extend(self._check_old_resource(res))

        return findings

    def _check_resource_group(self, rg: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = rg.get("name", "unknown")
        region = rg.get("region", "")
        resource_count = rg.get("resource_count", 0)

        if resource_count == 0:
            findings.append(CostFinding(
                title="Empty resource group",
                description=(
                    f"Resource group '{name}' contains no resources. "
                    "While resource groups are free, empty groups add clutter, "
                    "complicate governance, and may indicate abandoned projects."
                ),
                severity=Severity.LOW,
                category=Category.GENERAL,
                resource_name=name,
                resource_group=name,
                resource_type="Microsoft.Resources/resourceGroups",
                current_cost_monthly=0.0,
                projected_savings_monthly=0.0,
                recommendation="Delete the empty resource group to reduce clutter.",
                effort="Low",
                region=region,
            ))

        return findings

    def _check_untagged_resource(self, res: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = res.get("name", "unknown")
        rg = res.get("resource_group", "unknown")
        resource_type = res.get("resource_type", "")
        region = res.get("region", "")
        monthly_cost = res.get("monthly_cost", 0.0)
        missing_tags = res.get("missing_tags", [])

        tag_list = ", ".join(missing_tags) if missing_tags else "cost-center, environment, owner"

        if monthly_cost > 50:
            findings.append(CostFinding(
                title="High-cost resource missing required tags",
                description=(
                    f"Resource '{name}' ({resource_type}) costs "
                    f"${monthly_cost:.0f}/month but is missing tags: {tag_list}. "
                    "Untagged resources cannot be tracked for cost allocation."
                ),
                severity=Severity.MEDIUM,
                category=Category.GENERAL,
                resource_name=name,
                resource_group=rg,
                resource_type=resource_type,
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=0.0,
                recommendation=f"Add tags ({tag_list}) for cost tracking and governance.",
                effort="Low",
                region=region,
            ))
        elif monthly_cost > 0:
            findings.append(CostFinding(
                title="Resource missing required tags",
                description=(
                    f"Resource '{name}' ({resource_type}) is missing tags: "
                    f"{tag_list}. Tag all resources for cost governance."
                ),
                severity=Severity.LOW,
                category=Category.GENERAL,
                resource_name=name,
                resource_group=rg,
                resource_type=resource_type,
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=0.0,
                recommendation=f"Add tags ({tag_list}) for cost tracking.",
                effort="Low",
                region=region,
            ))

        return findings

    def _check_expensive_region(self, res: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = res.get("name", "unknown")
        rg = res.get("resource_group", "unknown")
        resource_type = res.get("resource_type", "")
        region = res.get("region", "")
        monthly_cost = res.get("monthly_cost", 0.0)
        cheaper_region = res.get("suggested_region", "eastus")

        if region.lower().replace(" ", "") in EXPENSIVE_REGIONS and monthly_cost > 100:
            findings.append(CostFinding(
                title="Resource in expensive region",
                description=(
                    f"Resource '{name}' ({resource_type}) runs in '{region}' "
                    f"at ${monthly_cost:.0f}/month. Moving to '{cheaper_region}' "
                    "could reduce costs by 15-25%."
                ),
                severity=Severity.LOW,
                category=Category.GENERAL,
                resource_name=name,
                resource_group=rg,
                resource_type=resource_type,
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.20,
                recommendation=f"Consider migrating to '{cheaper_region}' for lower pricing.",
                effort="High",
                region=region,
            ))

        return findings

    def _check_old_resource(self, res: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = res.get("name", "unknown")
        rg = res.get("resource_group", "unknown")
        resource_type = res.get("resource_type", "")
        region = res.get("region", "")
        monthly_cost = res.get("monthly_cost", 0.0)
        age_days = res.get("age_days", 0)

        if age_days > 365 and monthly_cost > 20:
            findings.append(CostFinding(
                title="Long-running resource (>1 year) — review needed",
                description=(
                    f"Resource '{name}' ({resource_type}) has been running for "
                    f"{age_days} days at ${monthly_cost:.0f}/month. "
                    "Validate that this resource is still needed."
                ),
                severity=Severity.LOW,
                category=Category.GENERAL,
                resource_name=name,
                resource_group=rg,
                resource_type=resource_type,
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=0.0,
                recommendation="Review and confirm the resource is still required.",
                effort="Low",
                region=region,
            ))

        return findings
