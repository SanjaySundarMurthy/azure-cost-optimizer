"""Database cost analyzer — SQL databases, Cosmos DB, Redis Cache."""

from __future__ import annotations

from ..models import Category, CostFinding, Severity
from .base import BaseAnalyzer


class DatabaseAnalyzer(BaseAnalyzer):
    """Analyze database resources for cost optimization opportunities."""

    @property
    def name(self) -> str:
        return "Database Analyzer"

    @property
    def category(self) -> Category:
        return Category.DATABASE

    def analyze(self, resources: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []

        for db in resources.get("sql_databases", []):
            findings.extend(self._check_sql_database(db))

        for cosmos in resources.get("cosmos_accounts", []):
            findings.extend(self._check_cosmos_account(cosmos))

        for redis in resources.get("redis_caches", []):
            findings.extend(self._check_redis_cache(redis))

        for mysql in resources.get("mysql_servers", []):
            findings.extend(self._check_mysql_server(mysql))

        return findings

    def _check_sql_database(self, db: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = db.get("name", "unknown")
        server = db.get("server", "unknown")
        rg = db.get("resource_group", "unknown")
        region = db.get("region", "")
        monthly_cost = db.get("monthly_cost", 0.0)
        sku = db.get("sku", "")
        dtu_used_pct = db.get("avg_dtu_used_pct", 100.0)
        max_size_gb = db.get("max_size_gb", 0)
        used_size_gb = db.get("used_size_gb", 0)
        is_dev = db.get("is_dev_test", False)

        display_name = f"{server}/{name}"

        # Oversized SQL database — very low DTU/CPU usage
        if dtu_used_pct < 15 and monthly_cost > 50:
            findings.append(CostFinding(
                title="Oversized SQL Database (low DTU utilization)",
                description=(
                    f"SQL DB '{display_name}' uses only {dtu_used_pct:.0f}% of "
                    f"provisioned DTUs on '{sku}' tier. "
                    "Downsize to a smaller SKU to match actual usage."
                ),
                severity=Severity.HIGH,
                category=Category.DATABASE,
                resource_name=display_name,
                resource_group=rg,
                resource_type="Microsoft.Sql/servers/databases",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.55,
                recommendation=f"Rightsize from '{sku}' to a lower tier matching ~{dtu_used_pct:.0f}% utilization.",
                effort="Medium",
                region=region,
            ))

        # Storage over-provisioned
        if max_size_gb > 0 and used_size_gb > 0:
            usage_ratio = used_size_gb / max_size_gb
            if usage_ratio < 0.20 and max_size_gb >= 100:
                findings.append(CostFinding(
                    title="SQL Database storage over-provisioned",
                    description=(
                        f"SQL DB '{display_name}' uses only {used_size_gb} GB "
                        f"of {max_size_gb} GB allocated ({usage_ratio:.0%} utilization). "
                        "Reduce max size to save on storage costs."
                    ),
                    severity=Severity.LOW,
                    category=Category.DATABASE,
                    resource_name=display_name,
                    resource_group=rg,
                    resource_type="Microsoft.Sql/servers/databases",
                    current_cost_monthly=monthly_cost * 0.15,
                    projected_savings_monthly=monthly_cost * 0.10,
                    recommendation="Reduce max database size to match actual data usage.",
                    effort="Low",
                    region=region,
                ))

        # Dev/test database on production SKU
        if is_dev and sku in ("Premium", "BusinessCritical", "P1", "P2", "P4"):
            findings.append(CostFinding(
                title="Dev/test database on production SKU",
                description=(
                    f"SQL DB '{display_name}' appears to be a dev/test database "
                    f"but runs on '{sku}' tier. Use Basic/Standard for non-production."
                ),
                severity=Severity.HIGH,
                category=Category.DATABASE,
                resource_name=display_name,
                resource_group=rg,
                resource_type="Microsoft.Sql/servers/databases",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.80,
                recommendation=f"Downgrade '{display_name}' from '{sku}' to Basic or Standard tier.",
                effort="Low",
                region=region,
            ))

        return findings

    def _check_cosmos_account(self, cosmos: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = cosmos.get("name", "unknown")
        rg = cosmos.get("resource_group", "unknown")
        region = cosmos.get("region", "")
        monthly_cost = cosmos.get("monthly_cost", 0.0)
        provisioned_rus = cosmos.get("provisioned_rus", 0)
        avg_ru_usage_pct = cosmos.get("avg_ru_usage_pct", 100.0)
        autoscale_enabled = cosmos.get("autoscale_enabled", True)
        request_count_24h = cosmos.get("request_count_24h", 1000)

        # Idle Cosmos DB (very few requests)
        if request_count_24h < 100 and monthly_cost > 25:
            findings.append(CostFinding(
                title="Idle Cosmos DB account",
                description=(
                    f"Cosmos DB '{name}' had only {request_count_24h} requests "
                    "in the last 24 hours but costs "
                    f"${monthly_cost:.0f}/month. Consider serverless tier or deletion."
                ),
                severity=Severity.HIGH,
                category=Category.DATABASE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.DocumentDB/databaseAccounts",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.90,
                recommendation="Switch to serverless tier or delete if unused.",
                effort="Medium",
                region=region,
            ))

        # Over-provisioned RUs without autoscale
        if not autoscale_enabled and avg_ru_usage_pct < 25 and provisioned_rus >= 1000:
            findings.append(CostFinding(
                title="Over-provisioned Cosmos DB RUs (no autoscale)",
                description=(
                    f"Cosmos DB '{name}' uses only {avg_ru_usage_pct:.0f}% of "
                    f"{provisioned_rus} provisioned RU/s. Enable autoscale to "
                    "scale down during low-usage periods."
                ),
                severity=Severity.MEDIUM,
                category=Category.DATABASE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.DocumentDB/databaseAccounts",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.45,
                recommendation=f"Enable autoscale or reduce from {provisioned_rus} RU/s.",
                effort="Medium",
                region=region,
            ))

        return findings

    def _check_redis_cache(self, redis: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = redis.get("name", "unknown")
        rg = redis.get("resource_group", "unknown")
        region = redis.get("region", "")
        monthly_cost = redis.get("monthly_cost", 0.0)
        sku = redis.get("sku", "Standard")
        memory_used_pct = redis.get("memory_used_pct", 100.0)
        connections_avg = redis.get("avg_connections", 100)

        # Oversized Redis
        if sku in ("Premium", "Enterprise") and memory_used_pct < 20:
            findings.append(CostFinding(
                title="Oversized Redis Cache",
                description=(
                    f"Redis Cache '{name}' ({sku}) uses only {memory_used_pct:.0f}% "
                    "of available memory. Downsize to a smaller tier."
                ),
                severity=Severity.MEDIUM,
                category=Category.DATABASE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Cache/Redis",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.50,
                recommendation=f"Downgrade from '{sku}' to Standard tier.",
                effort="Medium",
                region=region,
            ))

        # Idle Redis
        if connections_avg < 5 and monthly_cost > 15:
            findings.append(CostFinding(
                title="Idle Redis Cache (very few connections)",
                description=(
                    f"Redis Cache '{name}' averages only {connections_avg} "
                    "connections. It may no longer be needed."
                ),
                severity=Severity.HIGH,
                category=Category.DATABASE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.Cache/Redis",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.95,
                recommendation="Delete the idle Redis Cache or consolidate workloads.",
                effort="Low",
                region=region,
            ))

        return findings

    def _check_mysql_server(self, mysql: dict) -> list[CostFinding]:
        findings: list[CostFinding] = []
        name = mysql.get("name", "unknown")
        rg = mysql.get("resource_group", "unknown")
        region = mysql.get("region", "")
        monthly_cost = mysql.get("monthly_cost", 0.0)
        sku = mysql.get("sku", "")
        cpu_pct = mysql.get("avg_cpu_pct", 100.0)

        if cpu_pct < 10 and monthly_cost > 30:
            findings.append(CostFinding(
                title="Underutilized MySQL Flexible Server",
                description=(
                    f"MySQL server '{name}' ({sku}) averages only {cpu_pct:.0f}% CPU. "
                    "Rightsize to a smaller compute tier."
                ),
                severity=Severity.MEDIUM,
                category=Category.DATABASE,
                resource_name=name,
                resource_group=rg,
                resource_type="Microsoft.DBforMySQL/flexibleServers",
                current_cost_monthly=monthly_cost,
                projected_savings_monthly=monthly_cost * 0.45,
                recommendation=f"Downsize '{name}' from '{sku}' to a Burstable B-series tier.",
                effort="Medium",
                region=region,
            ))

        return findings
