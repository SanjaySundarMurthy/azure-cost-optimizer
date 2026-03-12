"""Tests for the scanner orchestrator."""

from __future__ import annotations

from azure_cost_optimizer.demo import get_demo_resources, get_demo_subscription
from azure_cost_optimizer.scanner import CostScanner


class TestCostScanner:
    def test_scanner_has_all_analyzers(self):
        scanner = CostScanner()
        assert len(scanner.analyzers) == 5

    def test_scan_with_demo_data(self):
        scanner = CostScanner()
        sub = get_demo_subscription()
        resources = get_demo_resources()
        report = scanner.scan(resources, sub)

        assert report.subscription == sub
        assert len(report.findings) > 0
        assert report.scan_duration >= 0
        assert report.total_monthly_savings > 0

    def test_scan_empty_resources(self):
        scanner = CostScanner()
        sub = get_demo_subscription()
        report = scanner.scan({}, sub)
        assert len(report.findings) == 0

    def test_findings_sorted_by_severity(self):
        scanner = CostScanner()
        sub = get_demo_subscription()
        resources = get_demo_resources()
        report = scanner.scan(resources, sub)

        if len(report.findings) > 1:
            for i in range(len(report.findings) - 1):
                assert (
                    report.findings[i].severity.sort_key
                    <= report.findings[i + 1].severity.sort_key
                )
