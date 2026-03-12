# Azure Cost Optimizer

A powerful CLI tool that analyzes Azure resources and identifies cost optimization opportunities. Provides actionable recommendations with projected savings across compute, storage, networking, and database services.

[![CI](https://github.com/SanjaySundarMurthy/azure-cost-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/SanjaySundarMurthy/azure-cost-optimizer/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Features

- **30 cost checks** across 5 categories (Compute, Storage, Networking, Database, General)
- **Severity classification** — HIGH, MEDIUM, LOW with effort estimates
- **Beautiful terminal output** — Rich tables, panels, color-coded findings
- **Export reports** — JSON and CSV formats for stakeholder sharing
- **Demo mode** — Try instantly without Azure credentials
- **Filtering** — By severity level or resource category
- **Optimization grading** — Letter grade (A-F) based on savings potential

## Quick Start

### Install

```bash
pip install -e .
```

### Run Demo

```bash
azure-cost scan --demo
```

### See All Checks

```bash
azure-cost summary
```

## Usage

### Scan with Demo Data

```bash
# Full scan with demo data
azure-cost scan --demo

# Filter by severity
azure-cost scan --demo --severity HIGH

# Filter by category
azure-cost scan --demo --category COMPUTE

# Export JSON report
azure-cost scan --demo --export-json report.json

# Export CSV report
azure-cost scan --demo --export-csv findings.csv

# Combine filters and export
azure-cost scan --demo --severity HIGH --category DATABASE --export-json critical-db.json
```

### Available Commands

| Command | Description |
|---------|-------------|
| `azure-cost scan --demo` | Run cost analysis with demo data |
| `azure-cost summary` | Show all 30 checks the tool performs |
| `azure-cost --version` | Show version |

## What It Checks

### Compute (7 checks)
| Check | Severity | Potential Savings |
|-------|----------|-------------------|
| Stopped but allocated VMs | HIGH | ~85% |
| Idle VMs (< 5% CPU) | HIGH | ~95% |
| Underutilized VMs (< 20% CPU) | MEDIUM | ~40% |
| Dev/test VMs without auto-shutdown | MEDIUM | ~65% |
| Reserved Instance candidates | LOW | ~38% |
| Scale sets with fixed instance count | MEDIUM | ~30% |
| Overprovisioned App Services | HIGH | ~60% |

### Storage (5 checks)
| Check | Severity | Potential Savings |
|-------|----------|-------------------|
| Unattached managed disks | HIGH | 100% |
| Premium disks with low IOPS | MEDIUM | ~65% |
| Old snapshots (> 90 days) | MEDIUM | 100% |
| Aging snapshots (> 30 days) | LOW | ~80% |
| Hot storage with infrequent access | MEDIUM | ~45% |

### Networking (5 checks)
| Check | Severity | Potential Savings |
|-------|----------|-------------------|
| Orphaned public IP addresses | HIGH | 100% |
| Load balancers with no backends | HIGH | 100% |
| Load balancers with no rules | MEDIUM | ~50% |
| Unused NAT Gateways | HIGH | 100% |
| Oversized Application Gateways | MEDIUM | ~35% |

### Database (8 checks)
| Check | Severity | Potential Savings |
|-------|----------|-------------------|
| Oversized SQL Databases (low DTU) | HIGH | ~55% |
| SQL storage over-provisioned | LOW | ~10% |
| Dev/test DBs on production SKUs | HIGH | ~80% |
| Idle Cosmos DB accounts | HIGH | ~90% |
| Over-provisioned Cosmos DB RUs | MEDIUM | ~45% |
| Oversized Redis Cache | MEDIUM | ~50% |
| Idle Redis Cache | HIGH | ~95% |
| Underutilized MySQL servers | MEDIUM | ~45% |

### General (5 checks)
| Check | Severity | Potential Savings |
|-------|----------|-------------------|
| Empty resource groups | LOW | — |
| High-cost untagged resources | MEDIUM | — |
| Untagged resources | LOW | — |
| Resources in expensive regions | LOW | ~20% |
| Long-running resources (> 1 year) | LOW | — |

## Architecture

```
azure_cost_optimizer/
├── cli.py              # Click CLI entry point
├── scanner.py          # Orchestrator — runs all analyzers
├── models.py           # Data models (Severity, Category, CostFinding, etc.)
├── demo.py             # Demo mode with realistic mock data
├── analyzers/
│   ├── base.py         # Abstract base analyzer
│   ├── compute.py      # VM, scale set, app service checks
│   ├── storage.py      # Disk, snapshot, storage account checks
│   ├── networking.py   # Public IP, load balancer, NAT gateway checks
│   ├── database.py     # SQL, Cosmos DB, Redis, MySQL checks
│   └── misc.py         # Resource groups, tags, regions
└── output/
    ├── console.py      # Rich terminal rendering
    └── report.py       # JSON/CSV export
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run linter
ruff check .

# Run with demo
azure-cost scan --demo
```

## Tech Stack

- **Python 3.9+** — Core runtime
- **Click** — CLI framework
- **Rich** — Terminal formatting and tables
- **pytest** — Testing framework
- **ruff** — Linting

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**Sanjay S** — Senior DevOps Engineer

- GitHub: [@SanjaySundarMurthy](https://github.com/SanjaySundarMurthy)
- Portfolio: [sanjaysundarmurthy-portfolio.vercel.app](https://sanjaysundarmurthy-portfolio.vercel.app/)
