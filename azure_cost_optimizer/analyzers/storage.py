"""Storage cost analyzer — disks, snapshots, storage accounts."""

from __future__ import annotations

from ..models import Category, CostFinding, Severity
from .base import BaseAnalyzer


class StorageAnalyzer(BaseAnalyzer):
    """Analyze storage resources for cost optimization opportunities."""

    @property
    def name(self) -> str:
        return "Storage Analyzer"

    @property
    def category(self) -> Category:
        return Category.STORAGE

    def analyze(self, resources: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []

        for disk in resources.get("managed_disks", []):
            findings.extend(self._check_disk(disk))

        for snap in resources.get("snapshots", []):
            findings.extend(self._check_snapshot(snap))

        for sa in resources.get("storage_accounts", []):
            findings.extend(self._check_storage_account(sa))

        return findings

    def _check_disk(self, disk: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = disk.get("name", "unknown")
        rg = disk.get("resource_group", "unknown")
        region = disk.get("region", "")
        monthly_cost = disk.get("monthly_cost", 0.0)
        attached = disk.get("attached", True)
        sku = disk.get("sku", "Standard_LRS")
        size_gb = disk.get("size_gb", 0)

        # Unattached disk
        if not attached:
            findings.append(CostFinding(
                title="Unattached managed disk",
                description=(
                    f"Disk '{name}' ({size_gb} GB, {sku}) is not attached to any VM. "
                    "Unattached disks still incur storage charges. "
                    "Snapshot and delete if no longer needed."
                ),
                severity=Severity.HIGH,
                category=Category.STORAGE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Compute/disks",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost,
                recommendation="Take a snapshot (if needed) and delete the unattached disk.",
                effort="Low",
                region=region,
            ))

        # Premium disk on a low-IOPS workload
        if sku.startswith("Premium") and disk.get("avg_iops", 500) < 100:
            std_cost = monthly_cost * 0.35  # Standard is ~65% cheaper
            findings.append(CostFinding(
                title="Premium disk with low IOPS usage",
                description=(
                    f"Disk '{name}' uses {sku} but averages only "
                    f"{disk.get('avg_iops', 0)} IOPS. "
                    "Consider downgrading to Standard SSD."
                ),
                severity=Severity.MEDIUM,
                category=Category.STORAGE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Compute/disks",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost - std_cost,
                recommendation="Change SKU from Premium to Standard SSD (StandardSSD_LRS).",
                effort="Medium",
                region=region,
            ))

        return findings

    def _check_snapshot(self, snap: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = snap.get("name", "unknown")
        rg = snap.get("resource_group", "unknown")
        region = snap.get("region", "")
        monthly_cost = snap.get("monthly_cost", 0.0)
        age_days = snap.get("age_days", 0)
        size_gb = snap.get("size_gb", 0)

        if age_days > 90:
            findings.append(CostFinding(
                title="Old snapshot (> 90 days)",
                description=(
                    f"Snapshot '{name}' ({size_gb} GB) is {age_days} days old. "
                    "Old snapshots accumulate costs over time. "
                    "Review and delete if no longer needed for recovery."
                ),
                severity=Severity.MEDIUM,
                category=Category.STORAGE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Compute/snapshots",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost,
                recommendation="Delete the old snapshot if no longer needed.",
                effort="Low",
                region=region,
            ))
        elif age_days > 30:
            findings.append(CostFinding(
                title="Aging snapshot (> 30 days)",
                description=(
                    f"Snapshot '{name}' ({size_gb} GB) is {age_days} days old. "
                    "Consider moving to a cheaper storage tier or deleting."
                ),
                severity=Severity.LOW,
                category=Category.STORAGE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Compute/snapshots",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.80,
                recommendation="Move to Cool tier or delete if unneeded.",
                effort="Low",
                region=region,
            ))

        return findings

    def _check_storage_account(self, sa: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = sa.get("name", "unknown")
        rg = sa.get("resource_group", "unknown")
        region = sa.get("region", "")
        monthly_cost = sa.get("monthly_cost", 0.0)
        tier = sa.get("access_tier", "Hot")
        last_access_days = sa.get("last_access_days", 0)

        if tier == "Hot" and last_access_days > 30:
            findings.append(CostFinding(
                title="Hot storage with infrequent access",
                description=(
                    f"Storage account '{name}' is on Hot tier but hasn't been accessed "
                    f"in {last_access_days} days. Moving to Cool tier saves ~45% on storage."
                ),
                severity=Severity.MEDIUM,
                category=Category.STORAGE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Storage/storageAccounts",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.45,
                recommendation="Change access tier from Hot to Cool.",
                effort="Low",
                region=region,
            ))

        return findings
