# Stage 00 — Foundation

## Status

in-progress

## Goal

Estabelecer a base do projeto: estrutura de diretórios, sistema de build, ferramentas de desenvolvimento, documentação inicial e entrypoint.

## Scope

- Criar projeto Python com `uv`
- Configurar `pyproject.toml`
- Criar `justfile` com suporte PowerShell
- Definir estrutura de pacotes `src/robot_lsp/`
- Criar camadas: `domain/`, `application/`, `infrastructure/`, `protocol/`, `adapters/`
- Criar entrypoint vazio `__main__.py`
- Criar `tests/` com estrutura `unit/` e `integration/`
- Configurar `pytest`
- Criar `docs/` com roadmap, architecture, ADRs, stages e specs
- Criar `.gitkeep` para diretórios vazios

## Out Of Scope

- Qualquer lógica de LSP, JSON-RPC ou parse

## Deliverables

- `pyproject.toml` configurado
- `justfile` funcional
- `src/robot_lsp/` com `__init__.py`, `__main__.py`, `main.py`
- `src/robot_lsp/domain/`, `application/`, `infrastructure/robotframework/`, `protocol/`, `adapters/` com `__init__.py`
- `tests/conftest.py`, `tests/unit/`, `tests/integration/`
- `docs/` completo
- `.gitignore` inicial

## Acceptance Criteria

- `uv run pytest` executa e passa
- `just test` executa e passa
- `python -m robot_lsp` executa sem erro
- Estrutura de diretórios reflete Clean Architecture

## Tests

- Teste de importação de todos os módulos (vazio)

## Risks

- Nenhum

## Dependencies

- Nenhuma

## Notes

- Usar `uv` como gerenciador de projeto
- Suporte mínimo Python 3.10+
