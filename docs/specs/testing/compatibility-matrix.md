# Compatibility Matrix

## Stage

Stage 14 — Release Hardening

Post-MVP 01 — Robot Framework 7.x compatibility matrix

## RF Versions

| RF Version | Status | Notes |
|---|---|---|
| 7.0.1 | CI target | Mínimo suportado |
| 7.1.1 | CI target | |
| 7.2.2 | CI target | Group/END |
| 7.3.2 | CI target | |
| 7.4.2 | CI target + locally validated | Versão instalada no ambiente atual |

## Python Versions

| Python | Status |
|---|---|
| 3.10 | Locally validated |
| 3.11 | CI target |
| 3.12 | CI target |
| 3.13 | Future |

## OS

| OS | Status |
|---|---|
| Windows | Locally validated + CI target |
| Linux | CI target |
| macOS | Future |

## Test Strategy por Versão

```bash
# Criar ambiente para cada versão do RF
uv venv --python 3.12 .venv-rf70
uv pip install robotframework==7.0.1
uv run pytest tests/ -v

uv venv --python 3.12 .venv-rf74
uv pip install robotframework==7.4.2
uv run pytest tests/ -v
```

## Feature Detection Tests

Testes específicos para verificar que cada versão é detectada corretamente e que features ausentes não causam erro.

## Current CI

- `ubuntu-latest` and `windows-latest`
- Python 3.10, 3.11 and 3.12
- Installed Robot Framework version from project dependency resolution for OS/Python coverage
- Fixed Robot Framework compatibility matrix on Ubuntu/Python 3.12: 7.0.1, 7.1.1, 7.2.2, 7.3.2 and 7.4.2
