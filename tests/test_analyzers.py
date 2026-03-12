"""Tests for all cost analyzers."""

from __future__ import annotations

from azure_cost_optimizer.analyzers.compute import ComputeAnalyzer
from azure_cost_optimizer.analyzers.database import DatabaseAnalyzer
from azure_cost_optimizer.analyzers.misc import GeneralAnalyzer
from azure_cost_optimizer.analyzers.networking import NetworkingAnalyzer
from azure_cost_optimizer.analyzers.storage import StorageAnalyzer
from azure_cost_optimizer.models import Category, Severity


# ── Compute ────────────────────────────────────────────────────────


class TestComputeAnalyzer:
    def setup_method(self):
        self.analyzer = ComputeAnalyzer()

    def test_name_and_category(self):
        assert self.analyzer.name == "Compute Analyzer"
        assert self.analyzer.category == Category.COMPUTE

    def test_stopped_vm(self):
        resources = {
            "virtual_machines": [{
                "name": "vm-stopped",
                "resource_group": "rg",
                "region": "eastus",
                "vm_size": "Standard_D2s_v3",
                "monthly_cost": 200.0,
                "power_state": "stopped",
                "avg_cpu_pct": 0,
                "has_auto_shutdown": False,
                "is_dev_test": False,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1
        assert any("Stopped" in f.title or "stopped" in f.title.lower() for f in findings)
        assert findings[0].severity == Severity.HIGH

    def test_idle_vm(self):
        resources = {
            "virtual_machines": [{
                "name": "vm-idle",
                "resource_group": "rg",
                "region": "eastus",
                "vm_size": "Standard_D4s_v3",
                "monthly_cost": 400.0,
                "power_state": "running",
                "avg_cpu_pct": 2.0,
                "has_auto_shutdown": False,
                "is_dev_test": False,
            }],
        }
        findings = self.analyzer.analyze(resources)
        has_idle = any("idle" in f.title.lower() for f in findings)
        assert has_idle

    def test_healthy_vm_no_findings(self):
        resources = {
            "virtual_machines": [{
                "name": "vm-ok",
                "resource_group": "rg",
                "region": "eastus",
                "vm_size": "Standard_D2s_v3",
                "monthly_cost": 200.0,
                "power_state": "running",
                "avg_cpu_pct": 55.0,
                "has_auto_shutdown": True,
                "is_dev_test": True,
                "reserved_instance": True,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) == 0

    def test_dev_vm_without_autoshutdown(self):
        resources = {
            "virtual_machines": [{
                "name": "vm-dev",
                "resource_group": "rg",
                "region": "eastus",
                "vm_size": "Standard_D2s_v3",
                "monthly_cost": 200.0,
                "power_state": "running",
                "avg_cpu_pct": 30.0,
                "has_auto_shutdown": False,
                "is_dev_test": True,
            }],
        }
        findings = self.analyzer.analyze(resources)
        has_shutdown = any("auto-shutdown" in f.title.lower() or "shutdown" in f.description.lower() for f in findings)
        assert has_shutdown

    def test_scale_set_fixed_count(self):
        resources = {
            "scale_sets": [{
                "name": "vmss-fixed",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 800.0,
                "min_instances": 4,
                "max_instances": 4,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1

    def test_overprovisioned_app_service(self):
        resources = {
            "app_services": [{
                "name": "app-over",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 300.0,
                "plan_tier": "Premium",
                "avg_cpu_pct": 4.0,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1

    def test_empty_resources(self):
        findings = self.analyzer.analyze({})
        assert findings == []


# ── Storage ────────────────────────────────────────────────────────


class TestStorageAnalyzer:
    def setup_method(self):
        self.analyzer = StorageAnalyzer()

    def test_name_and_category(self):
        assert self.analyzer.name == "Storage Analyzer"
        assert self.analyzer.category == Category.STORAGE

    def test_unattached_disk(self):
        resources = {
            "managed_disks": [{
                "name": "disk-orphan",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 50.0,
                "sku": "Premium_LRS",
                "size_gb": 256,
                "attached": False,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1
        assert findings[0].severity == Severity.HIGH

    def test_attached_disk_no_finding(self):
        resources = {
            "managed_disks": [{
                "name": "disk-ok",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 50.0,
                "sku": "Standard_LRS",
                "size_gb": 256,
                "attached": True,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) == 0

    def test_old_snapshot(self):
        resources = {
            "snapshots": [{
                "name": "snap-old",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 10.0,
                "size_gb": 128,
                "age_days": 100,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1

    def test_hot_storage_infrequent_access(self):
        resources = {
            "storage_accounts": [{
                "name": "sttest",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 100.0,
                "access_tier": "Hot",
                "last_access_days": 40,
                "total_size_gb": 500,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1


# ── Networking ─────────────────────────────────────────────────────


class TestNetworkingAnalyzer:
    def setup_method(self):
        self.analyzer = NetworkingAnalyzer()

    def test_name_and_category(self):
        assert self.analyzer.name == "Networking Analyzer"
        assert self.analyzer.category == Category.NETWORKING

    def test_orphaned_public_ip(self):
        resources = {
            "public_ips": [{
                "name": "pip-orphan",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 3.65,
                "sku": "Standard",
                "associated": False,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) == 1
        assert "orphan" in findings[0].title.lower() or "Orphaned" in findings[0].title

    def test_associated_ip_no_finding(self):
        resources = {
            "public_ips": [{
                "name": "pip-ok",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 3.65,
                "sku": "Standard",
                "associated": True,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) == 0

    def test_lb_no_backends(self):
        resources = {
            "load_balancers": [{
                "name": "lb-empty",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 20.0,
                "backend_pool_count": 0,
                "rule_count": 0,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1
        assert findings[0].severity == Severity.HIGH

    def test_nat_gateway_no_subnets(self):
        resources = {
            "nat_gateways": [{
                "name": "nat-unused",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 32.0,
                "associated_subnets": 0,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) == 1
        assert findings[0].severity == Severity.HIGH

    def test_oversized_app_gateway(self):
        resources = {
            "app_gateways": [{
                "name": "agw-big",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 400.0,
                "tier": "WAF_v2",
                "capacity_units": 10,
                "avg_active_connections": 20,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1


# ── Database ───────────────────────────────────────────────────────


class TestDatabaseAnalyzer:
    def setup_method(self):
        self.analyzer = DatabaseAnalyzer()

    def test_name_and_category(self):
        assert self.analyzer.name == "Database Analyzer"
        assert self.analyzer.category == Category.DATABASE

    def test_oversized_sql_db(self):
        resources = {
            "sql_databases": [{
                "name": "db-big",
                "server": "sql-server",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 500.0,
                "sku": "Premium",
                "avg_dtu_used_pct": 5.0,
                "avg_cpu_pct": 3.0,
                "max_size_gb": 500,
                "used_size_gb": 20,
                "is_dev_test": False,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1
        has_oversized = any("oversized" in f.title.lower() or "DTU" in f.title for f in findings)
        assert has_oversized

    def test_dev_db_production_sku(self):
        resources = {
            "sql_databases": [{
                "name": "db-dev",
                "server": "sql-dev",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 400.0,
                "sku": "Premium",
                "avg_dtu_used_pct": 50.0,
                "avg_cpu_pct": 40.0,
                "max_size_gb": 100,
                "used_size_gb": 50,
                "is_dev_test": True,
            }],
        }
        findings = self.analyzer.analyze(resources)
        has_dev = any("dev" in f.title.lower() for f in findings)
        assert has_dev

    def test_idle_cosmos(self):
        resources = {
            "cosmos_accounts": [{
                "name": "cosmos-idle",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 200.0,
                "provisioned_rus": 2000,
                "avg_ru_usage_pct": 5.0,
                "autoscale_enabled": False,
                "request_count_24h": 10,
            }],
        }
        findings = self.analyzer.analyze(resources)
        has_idle = any("idle" in f.title.lower() for f in findings)
        assert has_idle

    def test_idle_redis(self):
        resources = {
            "redis_caches": [{
                "name": "redis-idle",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 100.0,
                "sku": "Premium",
                "memory_used_pct": 5.0,
                "avg_connections": 1,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1

    def test_underutilized_mysql(self):
        resources = {
            "mysql_servers": [{
                "name": "mysql-low",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 150.0,
                "sku": "Standard_D4ds_v4",
                "avg_cpu_pct": 3.0,
                "storage_used_pct": 10.0,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1

    def test_healthy_sql_no_finding(self):
        resources = {
            "sql_databases": [{
                "name": "db-ok",
                "server": "sql-prod",
                "resource_group": "rg",
                "region": "eastus",
                "monthly_cost": 200.0,
                "sku": "Standard",
                "avg_dtu_used_pct": 60.0,
                "avg_cpu_pct": 55.0,
                "max_size_gb": 100,
                "used_size_gb": 60,
                "is_dev_test": False,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) == 0


# ── General ────────────────────────────────────────────────────────


class TestGeneralAnalyzer:
    def setup_method(self):
        self.analyzer = GeneralAnalyzer()

    def test_name_and_category(self):
        assert self.analyzer.name == "General Analyzer"
        assert self.analyzer.category == Category.GENERAL

    def test_empty_resource_group(self):
        resources = {
            "resource_groups": [{
                "name": "rg-empty",
                "region": "eastus",
                "resource_count": 0,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) == 1
        assert "empty" in findings[0].title.lower()

    def test_non_empty_rg_no_finding(self):
        resources = {
            "resource_groups": [{
                "name": "rg-full",
                "region": "eastus",
                "resource_count": 5,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) == 0

    def test_high_cost_untagged(self):
        resources = {
            "untagged_resources": [{
                "name": "vm-untagged",
                "resource_group": "rg",
                "resource_type": "Microsoft.Compute/virtualMachines",
                "region": "eastus",
                "monthly_cost": 500.0,
                "missing_tags": ["cost-center", "owner"],
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1
        assert findings[0].severity == Severity.MEDIUM

    def test_expensive_region(self):
        resources = {
            "expensive_region_resources": [{
                "name": "vm-brazil",
                "resource_group": "rg",
                "resource_type": "Microsoft.Compute/virtualMachines",
                "region": "brazilsouth",
                "monthly_cost": 500.0,
                "suggested_region": "eastus",
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1

    def test_old_resource(self):
        resources = {
            "old_resources": [{
                "name": "vm-old",
                "resource_group": "rg",
                "resource_type": "Microsoft.Compute/virtualMachines",
                "region": "eastus",
                "monthly_cost": 300.0,
                "age_days": 400,
            }],
        }
        findings = self.analyzer.analyze(resources)
        assert len(findings) >= 1
