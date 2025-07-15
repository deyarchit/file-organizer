lint:
	@echo "Running ruff..."
	uv run ruff check --fix
	@echo "Running mypy..."
	mypy --python-executable .venv/bin/python . --show-error-end --check-untyped-defs --disallow-incomplete-defs

test:
	@echo "Running tests..."
	.venv/bin/python -m pytest

generate-integ-data:
	@echo "Generating integration test data..."
	.venv/bin/python tests/data_generator.py

pr: lint test

.PHONY: *