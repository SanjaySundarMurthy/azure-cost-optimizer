"""Shared test fixtures for azure-cost-optimizer."""

from __future__ import annotations

import pytest

from azure_cost_optimizer.models import (
    Category,
    CostFinding,
    OptimizationReport,
    Severity,
    SubscriptionSummary,
)


@pytest.fixture()
def sample_subscription() -> SubscriptionSummary:
    return SubscriptionSummary(
        subscription_id="test-sub-id",
        subscription_name="Test-Subscription",
        total_monthly_cost=5000.00,
        resource_count=50,
        resource_group_count=10,
        region_count=2,
        top_regions=["eastus", "westeurope"],
        cost_by_service={"Virtual Machines": 3000, "Storage": 2000},
    )


@pytest.fixture()
def sample_finding() -> CostFinding:
    return CostFinding(
        title="Test finding",
        description="Test description",
        severity=Severity.HIGH,
        category=Category.COMPUTE,
        resource_name="vm-test",
        resource_group="rg-test",
        resource_type="Microsoft.Compute/virtualMachines",
        current_cost_monthly=100.00,
        projected_savings_monthly=80.00,
        recommendation="Test recommendation",
        effort="Low",
        region="eastus",
    )


@pytest.fixture()
def sample_report(
    sample_subscription: SubscriptionSummary,
    sample_finding: CostFinding,
) -> OptimizationReport:
    return OptimizationReport(
        subscription=sample_subscription,
        findings=[sample_finding],
        scan_duration=0.5,
    )
