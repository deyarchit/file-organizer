lint:
	@echo "Running ruff..."
	uv run ruff check
	@echo "Running mypy..."
	uv run mypy .
	@echo "Running pyright..."
	uv run pyright .

format:
	@echo "Cleaning up using ruff..."
	uv run ruff check --fix

test:
	@echo "Running tests..."
	uv run pytest .

generate-mock-test-data:
	@echo "Generating mock test data..."
	.venv/bin/python tests/data_generator.py

ci: lint test
pr: lint format test

.PHONY: *
