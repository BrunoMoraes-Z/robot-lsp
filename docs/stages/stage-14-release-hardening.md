# Stage 14 — Release Hardening

## Status

done

## Goal

Preparar o MVP para execução real como language server via stdio, com documentação mínima, CI e validações finais.

## Scope

- Runner stdio real
- CLI básica
- Logging em stderr
- CI pipeline
- Documentação de uso
- Changelog inicial
- Matriz de compatibilidade atualizada

## Out Of Scope

- Publicação em PyPI
- Teste real contra todos os Robot Framework 7.x
- Tracing distribuído
- Logs estruturados avançados
- Subprocess integration tests completos

## Deliverables

- `src/robot_lsp/main.py` com loop LSP stdio
- `README.md`
- `docs/usage.md`
- `docs/changelog.md`
- `.github/workflows/ci.yml`
- Testes unitários do runner

## Acceptance Criteria

- `python -m robot_lsp --version` imprime versão
- Runner responde sessão mínima `initialize`, `shutdown`, `exit`
- Runner responde JSON-RPC error para mensagem inválida
- Logs são enviados para stderr
- CI executa pytest e compileall
- Documentação de uso existe
- Changelog inicial existe

## Tests

- `test_main_version`
- `test_run_lsp_loop_handles_minimal_session`
- `test_run_lsp_loop_returns_protocol_error_response`

## Risks

- Diagnostics assíncronos via processo real ainda precisam de teste end-to-end com subprocesso.
- CI testa a versão resolvida de Robot Framework, não uma matriz completa de RF 7.x.
- Publicação/distribuição em PyPI ainda não foi automatizada.

## Dependencies

- Stage 01
- Stage 02
- Stage 05
- Stage 13

## Notes

- O runner injeta um publisher que escreve diagnostics diretamente no transporte, evitando depender apenas de fila em memória.
- stdout é reservado exclusivamente ao protocolo LSP.
