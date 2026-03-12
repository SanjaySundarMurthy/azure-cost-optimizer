"""Compute cost analyzer — VMs, scale sets, app services."""

from __future__ import annotations

from ..models import Category, CostFinding, Severity
from .base import BaseAnalyzer


class ComputeAnalyzer(BaseAnalyzer):
    """Analyze compute resources for cost optimization opportunities."""

    @property
    def name(self) -> str:
        return "Compute Analyzer"

    @property
    def category(self) -> Category:
        return Category.COMPUTE

    def analyze(self, resources: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []

        for vm in resources.get("virtual_machines", []):
            findings.extend(self._check_vm(vm))

        for ss in resources.get("scale_sets", []):
            findings.extend(self._check_scale_set(ss))

        for app in resources.get("app_services", []):
            findings.extend(self._check_app_service(app))

        return findings

    def _check_vm(self, vm: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = vm.get("name", "unknown")
        rg = vm.get("resource_group", "unknown")
        region = vm.get("region", "")
        size = vm.get("vm_size", "")
        monthly_cost = vm.get("monthly_cost", 0.0)
        avg_cpu = vm.get("avg_cpu_pct", 50.0)
        state = vm.get("power_state", "running")
        has_autoshutdown = vm.get("has_auto_shutdown", False)
        is_dev_test = vm.get("is_dev_test", False)

        # Stopped but still allocated (still being billed for compute)
        if state == "stopped":
            findings.append(CostFinding(
                title="VM stopped but still allocated",
                description=(
                    f"VM '{name}' is stopped but not deallocated. "
                    "Azure still charges for the compute allocation. "
                    "Deallocate or delete if no longer needed."
                ),
                severity=Severity.HIGH,
                category=Category.COMPUTE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Compute/virtualMachines",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.85,
                recommendation="Deallocate the VM or delete if unused.",
                effort="Low",
                region=region,
            ))

        # Idle VM — very low CPU
        elif avg_cpu < 5.0 and state == "running":
            findings.append(CostFinding(
                title="Idle VM detected (< 5% CPU)",
                description=(
                    f"VM '{name}' ({size}) has an average CPU utilization of "
                    f"{avg_cpu:.1f}% over the past 14 days. "
                    "This VM appears idle and may be a candidate for shutdown or deletion."
                ),
                severity=Severity.HIGH,
                category=Category.COMPUTE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Compute/virtualMachines",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.95,
                recommendation="Deallocate or delete this idle VM.",
                effort="Low",
                region=region,
            ))

        # Underutilized VM — low CPU, candidate for rightsizing
        elif avg_cpu < 20.0 and state == "running":
            suggested = vm.get("suggested_size", "")
            savings = vm.get("rightsizing_savings", monthly_cost * 0.40)
            desc = (
                f"VM '{name}' ({size}) averages {avg_cpu:.1f}% CPU. "
                "Consider downsizing to a smaller SKU."
            )
            if suggested:
                desc += f" Recommended size: {suggested}."
            findings.append(CostFinding(
                title="Underutilized VM — rightsizing opportunity",
                description=desc,
                severity=Severity.MEDIUM,
                category=Category.COMPUTE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Compute/virtualMachines",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=savings,
                recommendation=f"Resize to {suggested or 'a smaller SKU'}.",
                effort="Medium",
                region=region,
            ))

        # Dev/test VM without auto-shutdown
        if is_dev_test and not has_autoshutdown:
            if state == "running":
                findings.append(CostFinding(
                    title="Dev/Test VM without auto-shutdown",
                    description=(
                        f"VM '{name}' is a dev/test VM but has no auto-shutdown schedule. "
                        "Enabling auto-shutdown during off-hours can save ~65% on compute costs."
                    ),
                    severity=Severity.MEDIUM,
                    category=Category.COMPUTE,
                    resource_name=name,
                    resource_group=rg,
                    resource_type="Microsoft.Compute/virtualMachines",
                    current_cost_monthly=monthly_cost,
                    projected_savings_monthly=monthly_cost * 0.65,
                    recommendation="Enable auto-shutdown schedule (e.g., 7 PM - 7 AM).",
                    effort="Low",
                    region=region,
                ))

        # Reserved Instance opportunity (high-usage production VMs)
        if avg_cpu >= 40.0 and not is_dev_test and state == "running":
            is_ri = vm.get("reserved_instance", False)
            if not is_ri:
                findings.append(CostFinding(
                    title="Reserved Instance candidate",
                    description=(
                        f"VM '{name}' ({size}) runs consistently at {avg_cpu:.1f}% CPU "
                        "in production. A 1-year Reserved Instance can save up to 40%."
                    ),
                    severity=Severity.LOW,
                    category=Category.COMPUTE,
                    resource_name=name,
                    resource_group=rg,
                    resource_type="Microsoft.Compute/virtualMachines",
                    current_cost_monthly=monthly_cost,
                    projected_savings_monthly=monthly_cost * 0.38,
                    recommendation="Purchase a 1-year or 3-year Reserved Instance.",
                    effort="Low",
                    region=region,
                ))

        return findings

    def _check_scale_set(self, ss: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = ss.get("name", "unknown")
        rg = ss.get("resource_group", "unknown")
        region = ss.get("region", "")
        monthly_cost = ss.get("monthly_cost", 0.0)
        min_instances = ss.get("min_instances", 0)
        max_instances = ss.get("max_instances", 0)

        if min_instances == max_instances and min_instances > 1:
            findings.append(CostFinding(
                title="Scale set with fixed instance count",
                description=(
                    f"VMSS '{name}' has min=max={min_instances} instances. "
                    "Consider enabling autoscaling to reduce costs during low-demand periods."
                ),
                severity=Severity.MEDIUM,
                category=Category.COMPUTE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Compute/virtualMachineScaleSets",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.30,
                recommendation="Enable autoscaling with appropriate min/max thresholds.",
                effort="Medium",
                region=region,
            ))

        return findings

    def _check_app_service(self, app: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = app.get("name", "unknown")
        rg = app.get("resource_group", "unknown")
        region = app.get("region", "")
        tier = app.get("plan_tier", "")
        monthly_cost = app.get("monthly_cost", 0.0)
        avg_cpu = app.get("avg_cpu_pct", 50.0)

        if tier.startswith("Premium") and avg_cpu < 15.0:
            findings.append(CostFinding(
                title="Overprovisioned App Service Plan",
                description=(
                    f"App Service '{name}' runs on {tier} but averages {avg_cpu:.1f}% CPU. "
                    "Downgrade to Standard or Basic tier."
                ),
                severity=Severity.HIGH,
                category=Category.COMPUTE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Web/serverFarms",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.60,
                recommendation=f"Downgrade from {tier} to Standard S1.",
                effort="Medium",
                region=region,
            ))

        return findings
