# Stage 00 — Foundation

## Status

in-progress

## Goal

Establish the project foundation: directory structure, build system, development tooling, initial documentation, and entrypoint.

## Scope

- Create a Python project with `uv`
- Configure `pyproject.toml`
- Create a `justfile` with PowerShell support
- Define the `src/robot_lsp/` package structure
- Create layers: `domain/`, `application/`, `infrastructure/`, `protocol/`, `adapters/`
- Create an empty `__main__.py` entrypoint
- Create `tests/` with `unit/` and `integration/` structure
- Configure `pytest`
- Create `docs/` with roadmap, architecture, ADRs, stages, and specs
- Create `.gitkeep` files for empty directories

## Out Of Scope

- Any LSP, JSON-RPC, or parsing logic

## Deliverables

- Configured `pyproject.toml`
- Working `justfile`
- `src/robot_lsp/` with `__init__.py`, `__main__.py`, `main.py`
- `src/robot_lsp/domain/`, `application/`, `infrastructure/robotframework/`, `protocol/`, `adapters/` with `__init__.py`
- `tests/conftest.py`, `tests/unit/`, `tests/integration/`
- Complete `docs/`
- Initial `.gitignore`

## Acceptance Criteria

- `uv run pytest` runs and passes
- `just test` runs and passes
- `python -m robot_lsp` runs without error
- Directory structure reflects Clean Architecture

## Tests

- Import test for all modules (empty)

## Risks

- None

## Dependencies

- None

## Notes

- Use `uv` as the project manager
- Minimum Python support: 3.10+
