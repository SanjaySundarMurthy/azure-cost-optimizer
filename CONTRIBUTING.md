# Contributing to Azure Cost Optimizer

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/SanjaySundarMurthy/azure-cost-optimizer.git
cd azure-cost-optimizer

# Install in development mode
pip install -e ".[dev]"

# Verify installation
azure-cost --version
```

## Running Tests

```bash
pytest -v
```

## Code Quality

```bash
# Run linter
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

## Adding a New Analyzer Check

1. Open the appropriate analyzer in `azure_cost_optimizer/analyzers/`
2. Add a new `_check_*` method that returns `list[CostFinding]`
3. Call it from the `analyze()` method
4. Add corresponding test cases in `tests/test_analyzers.py`
5. Update the checks table in `README.md`
6. Add demo data in `azure_cost_optimizer/demo.py`

## Pull Request Guidelines

- All tests must pass (`pytest -v`)
- No linting errors (`ruff check .`)
- Include tests for new functionality
- Update README if adding new checks

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
