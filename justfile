set shell := ["pwsh", "-NoLogo", "-NoProfile", "-Command"]

test:
    uv run pytest

test-unit:
    uv run pytest tests/unit

test-integration:
    uv run pytest tests/integration

test-coverage:
    uv run pytest --cov=src/robot_lsp

lint:
    uv run python -m compileall src tests

run:
    uv run python -m robot_lsp

install-dev:
    uv sync --dev

freeze:
    uv pip freeze > requirements.txt
