"""Networking cost analyzer — public IPs, load balancers, NAT gateways."""

from __future__ import annotations

from ..models import Category, CostFinding, Severity
from .base import BaseAnalyzer


class NetworkingAnalyzer(BaseAnalyzer):
    """Analyze networking resources for cost optimization opportunities."""

    @property
    def name(self) -> str:
        return "Networking Analyzer"

    @property
    def category(self) -> Category:
        return Category.NETWORKING

    def analyze(self, resources: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []

        for ip in resources.get("public_ips", []):
            findings.extend(self._check_public_ip(ip))

        for lb in resources.get("load_balancers", []):
            findings.extend(self._check_load_balancer(lb))

        for nat in resources.get("nat_gateways", []):
            findings.extend(self._check_nat_gateway(nat))

        for agw in resources.get("app_gateways", []):
            findings.extend(self._check_app_gateway(agw))

        return findings

    def _check_public_ip(self, ip: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = ip.get("name", "unknown")
        rg = ip.get("resource_group", "unknown")
        region = ip.get("region", "")
        monthly_cost = ip.get("monthly_cost", 0.0)
        associated = ip.get("associated", False)
        sku = ip.get("sku", "Standard")

        if not associated:
            findings.append(CostFinding(
                title="Orphaned public IP address",
                description=(
                    f"Public IP '{name}' ({sku} SKU) is not associated with any resource. "
                    "Unused Standard public IPs are billed at ~$3.65/month. "
                    "Delete if no longer needed."
                ),
                severity=Severity.HIGH if sku == "Standard" else Severity.MEDIUM,
                category=Category.NETWORKING,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Network/publicIPAddresses",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost,
                recommendation="Delete the orphaned public IP address.",
                effort="Low",
                region=region,
            ))

        return findings

    def _check_load_balancer(self, lb: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = lb.get("name", "unknown")
        rg = lb.get("resource_group", "unknown")
        region = lb.get("region", "")
        monthly_cost = lb.get("monthly_cost", 0.0)
        backend_count = lb.get("backend_pool_count", 0)
        rule_count = lb.get("rule_count", 0)

        if backend_count == 0:
            findings.append(CostFinding(
                title="Load balancer with no backends",
                description=(
                    f"Load Balancer '{name}' has no backend pools configured. "
                    "It's incurring charges without serving any traffic."
                ),
                severity=Severity.HIGH,
                category=Category.NETWORKING,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Network/loadBalancers",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost,
                recommendation="Configure backend pools or delete the unused load balancer.",
                effort="Low",
                region=region,
            ))
        elif rule_count == 0:
            findings.append(CostFinding(
                title="Load balancer with no rules",
                description=(
                    f"Load Balancer '{name}' has backends but no load balancing rules. "
                    "No traffic is being routed."
                ),
                severity=Severity.MEDIUM,
                category=Category.NETWORKING,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Network/loadBalancers",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.50,
                recommendation="Add load balancing rules or delete if unused.",
                effort="Low",
                region=region,
            ))

        return findings

    def _check_nat_gateway(self, nat: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = nat.get("name", "unknown")
        rg = nat.get("resource_group", "unknown")
        region = nat.get("region", "")
        monthly_cost = nat.get("monthly_cost", 0.0)
        subnet_count = nat.get("associated_subnets", 0)

        if subnet_count == 0:
            findings.append(CostFinding(
                title="NAT Gateway not associated with any subnet",
                description=(
                    f"NAT Gateway '{name}' is not associated with any subnet. "
                    "It's being billed (~$32/month) without providing any connectivity."
                ),
                severity=Severity.HIGH,
                category=Category.NETWORKING,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Network/natGateways",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost,
                recommendation="Associate with a subnet or delete if unused.",
                effort="Low",
                region=region,
            ))

        return findings

    def _check_app_gateway(self, agw: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = agw.get("name", "unknown")
        rg = agw.get("resource_group", "unknown")
        region = agw.get("region", "")
        monthly_cost = agw.get("monthly_cost", 0.0)
        tier = agw.get("tier", "Standard_v2")
        avg_connections = agw.get("avg_active_connections", 0)

        if tier == "WAF_v2" and avg_connections < 50:
            findings.append(CostFinding(
                title="Oversized Application Gateway (WAF v2)",
                description=(
                    f"App Gateway '{name}' runs WAF_v2 tier with only "
                    f"~{avg_connections} avg active connections. "
                    "Consider downgrading to Standard_v2 if WAF is not required."
                ),
                severity=Severity.MEDIUM,
                category=Category.NETWORKING,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Network/applicationGateways",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.35,
                recommendation="Downgrade from WAF_v2 to Standard_v2 or reduce capacity.",
                effort="Medium",
                region=region,
            ))

        return findings
