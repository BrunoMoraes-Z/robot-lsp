# Compatibility Matrix

## Stage

Stage 14 — Release Hardening

## RF Versions

| RF Version | CI Status | Notes |
|---|---|---|
| 7.0.1 | ✅ | Mínimo suportado |
| 7.1.1 | ✅ | |
| 7.2.2 | ✅ | Group/END |
| 7.3.2 | ✅ | |
| 7.4.2 | ✅ | Secret variables (default) |

## Python Versions

| Python | CI Status |
|---|---|
| 3.10 | ✅ |
| 3.11 | ✅ |
| 3.12 | ✅ |
| 3.13 | ✅ (quando suportado pelo RF) |

## OS

| OS | CI Status |
|---|---|
| Windows | ✅ |
| Linux | ✅ |
| macOS | 🔄 (futuro) |

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
