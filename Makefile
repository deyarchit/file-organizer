lint:
	@echo "Running ruff..."
	uv run ruff check
	@echo "Running mypy..."
	mypy --python-executable .venv/bin/python . --show-error-end --check-untyped-defs --disallow-incomplete-defs

test:
	@echo "Running tests..."
	.venv/bin/python -m pytest

tidy: lint test

.PHONY: *