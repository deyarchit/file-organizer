lint:
	@echo "Running ruff..."
	uv run ruff check
	@echo "Running mypy..."
	uv run mypy . --show-error-end --check-untyped-defs --disallow-incomplete-defs

format:
	@echo "Cleaning up using ruff..."
	uv run ruff check --fix

test:
	@echo "Running tests..."
	.venv/bin/python -m pytest

generate-integ-data:
	@echo "Generating integration test data..."
	.venv/bin/python tests/data_generator.py

ci: lint test
pr: lint format test

.PHONY: *