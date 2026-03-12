"""Tests for report export (JSON and CSV)."""

from __future__ import annotations

import csv
import json

from azure_cost_optimizer.output.report import export_csv, export_json


class TestExportJSON:
    def test_creates_file(self, sample_report, tmp_path):
        out = tmp_path / "report.json"
        path = export_json(sample_report, str(out))
        assert path.exists()

    def test_valid_json(self, sample_report, tmp_path):
        out = tmp_path / "report.json"
        export_json(sample_report, str(out))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "subscription" in data
        assert "findings" in data
        assert data["summary"]["total_findings"] == 1


class TestExportCSV:
    def test_creates_file(self, sample_report, tmp_path):
        out = tmp_path / "report.csv"
        path = export_csv(sample_report, str(out))
        assert path.exists()

    def test_has_header_and_rows(self, sample_report, tmp_path):
        out = tmp_path / "report.csv"
        export_csv(sample_report, str(out))
        with out.open(encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2  # header + 1 finding
        assert "severity" in rows[0]
