"""Tests for data models."""

from __future__ import annotations

from azure_cost_optimizer.models import (
    Category,
    CostFinding,
    OptimizationReport,
    Severity,
)


class TestSeverity:
    def test_values(self):
        assert Severity.HIGH.value == "HIGH"
        assert Severity.MEDIUM.value == "MEDIUM"
        assert Severity.LOW.value == "LOW"

    def test_sort_key_ordering(self):
        assert Severity.HIGH.sort_key < Severity.MEDIUM.sort_key
        assert Severity.MEDIUM.sort_key < Severity.LOW.sort_key

    def test_icon_not_empty(self):
        for sev in Severity:
            assert sev.icon


class TestCategory:
    def test_values(self):
        assert Category.COMPUTE.value == "Compute"
        assert Category.STORAGE.value == "Storage"
        assert Category.NETWORKING.value == "Networking"
        assert Category.DATABASE.value == "Database"
        assert Category.GENERAL.value == "General"

    def test_icon_not_empty(self):
        for cat in Category:
            assert cat.icon


class TestCostFinding:
    def test_savings_pct(self, sample_finding):
        assert sample_finding.savings_pct == 80.0

    def test_savings_pct_zero_cost(self):
        f = CostFinding(
            title="t", description="d", severity=Severity.LOW,
            category=Category.GENERAL, resource_name="r",
            resource_group="rg", resource_type="rt",
            current_cost_monthly=0, projected_savings_monthly=0,
            recommendation="r",
        )
        assert f.savings_pct == 0.0

    def test_annual_savings(self, sample_finding):
        assert sample_finding.annual_savings == 80.0 * 12


class TestSubscriptionSummary:
    def test_fields(self, sample_subscription):
        assert sample_subscription.subscription_name == "Test-Subscription"
        assert sample_subscription.total_monthly_cost == 5000.00
        assert sample_subscription.resource_count == 50
        assert len(sample_subscription.top_regions) == 2


class TestOptimizationReport:
    def test_total_monthly_savings(self, sample_report):
        assert sample_report.total_monthly_savings == 80.0

    def test_total_annual_savings(self, sample_report):
        assert sample_report.total_annual_savings == 80.0 * 12

    def test_savings_pct(self, sample_report):
        assert sample_report.savings_pct == (80.0 / 5000.0) * 100

    def test_high_findings(self, sample_report):
        assert len(sample_report.high_findings) == 1

    def test_medium_findings(self, sample_report):
        assert len(sample_report.medium_findings) == 0

    def test_low_findings(self, sample_report):
        assert len(sample_report.low_findings) == 0

    def test_findings_by_category(self, sample_report):
        by_cat = sample_report.findings_by_category
        assert Category.COMPUTE in by_cat
        assert len(by_cat[Category.COMPUTE]) == 1

    def test_savings_by_category(self, sample_report):
        by_cat = sample_report.savings_by_category
        assert by_cat[Category.COMPUTE] == 80.0

    def test_to_dict(self, sample_report):
        d = sample_report.to_dict()
        assert d["subscription"]["name"] == "Test-Subscription"
        assert d["summary"]["total_findings"] == 1
        assert d["summary"]["high"] == 1
        assert len(d["findings"]) == 1

    def test_empty_report(self, sample_subscription):
        report = OptimizationReport(
            subscription=sample_subscription, findings=[], scan_duration=0.1
        )
        assert report.total_monthly_savings == 0
        assert report.savings_pct == 0.0
