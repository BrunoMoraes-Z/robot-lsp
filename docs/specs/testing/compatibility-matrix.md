# Compatibility Matrix

## Stage

Stage 14 — Release Hardening

## RF Versions

| RF Version | Status | Notes |
|---|---|---|
| 7.0.x | Target | Mínimo suportado |
| 7.1.x | Target | |
| 7.2.x | Target | Group/END |
| 7.3.x | Target | |
| 7.4.2 | Locally validated | Versão instalada no ambiente atual |

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
- Installed Robot Framework version from project dependency resolution
