"""Scanner — orchestrates all analyzers and produces an OptimizationReport."""

from __future__ import annotations

import time

from .analyzers.compute import ComputeAnalyzer
from .analyzers.database import DatabaseAnalyzer
from .analyzers.misc import GeneralAnalyzer
from .analyzers.networking import NetworkingAnalyzer
from .analyzers.storage import StorageAnalyzer
from .models import CostFinding, OptimizationReport, SubscriptionSummary


class CostScanner:
    """Run all cost analyzers against a set of Azure resources."""

    def __init__(self) -> None:
        self.analyzers = [
            ComputeAnalyzer(),
            StorageAnalyzer(),
            NetworkingAnalyzer(),
            DatabaseAnalyzer(),
            GeneralAnalyzer(),
        ]

    def scan(
        self,
        resources: dict,
        subscription_summary: SubscriptionSummary,
    ) -> OptimizationReport:
        """Execute every analyzer and collect findings into a report."""
        start = time.time()
        findings: list[CostFinding] = []

        for analyzer in self.analyzers:
            analyzer_findings = analyzer.analyze(resources)
            findings.extend(analyzer_findings)

        # Sort: HIGH first, then MEDIUM, then LOW
        findings.sort(key=lambda f: f.severity.sort_key)

        duration = time.time() - start

        return OptimizationReport(
            subscription=subscription_summary,
            findings=findings,
            scan_duration=duration,
        )
