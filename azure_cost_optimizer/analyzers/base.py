"""Base class for cost analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Category, CostFinding


class BaseAnalyzer(ABC):
    """Abstract base class for Azure cost analyzers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable analyzer name."""

    @property
    @abstractmethod
    def category(self) -> Category:
        """Category of resources this analyzer checks."""

    @abstractmethod
    def analyze(self, resources: dict) -> list[CostFinding]:
        """Analyze resources and return cost findings.

        Args:
            resources: Dict of resource data (from Azure API or demo mock).

        Returns:
            List of CostFinding objects with recommendations.
        """
