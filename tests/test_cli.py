"""Tests for CLI commands."""

from __future__ import annotations

from click.testing import CliRunner

from azure_cost_optimizer.cli import cli


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_version(self):
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "azure-cost-optimizer" in result.output

    def test_scan_without_demo_exits(self):
        result = self.runner.invoke(cli, ["scan"])
        assert result.exit_code != 0

    def test_scan_demo(self):
        result = self.runner.invoke(cli, ["scan", "--demo"])
        assert result.exit_code == 0

    def test_scan_demo_severity_filter(self):
        result = self.runner.invoke(cli, ["scan", "--demo", "--severity", "HIGH"])
        assert result.exit_code == 0

    def test_scan_demo_category_filter(self):
        result = self.runner.invoke(cli, ["scan", "--demo", "--category", "COMPUTE"])
        assert result.exit_code == 0

    def test_scan_demo_export_json(self, tmp_path):
        out = tmp_path / "report.json"
        result = self.runner.invoke(
            cli, ["scan", "--demo", "--export-json", str(out)]
        )
        assert result.exit_code == 0
        assert out.exists()

    def test_scan_demo_export_csv(self, tmp_path):
        out = tmp_path / "report.csv"
        result = self.runner.invoke(
            cli, ["scan", "--demo", "--export-csv", str(out)]
        )
        assert result.exit_code == 0
        assert out.exists()

    def test_summary_command(self):
        result = self.runner.invoke(cli, ["summary"])
        assert result.exit_code == 0
        assert "Checks Overview" in result.output or "checks" in result.output.lower()
