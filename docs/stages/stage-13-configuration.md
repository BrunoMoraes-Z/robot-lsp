# Stage 13 — Configuration

## Status

done

## Goal

Adicionar configuração do servidor via opções de inicialização e mudanças em runtime, com defaults seguros e integração nos recursos já existentes.

## Scope

- `initializationOptions`
- `workspace/didChangeConfiguration`
- Modelo de configuração interno
- Feature flag para diagnostics
- Caminhos adicionais de import
- Capabilities de configuração

## Out Of Scope

- Request outbound `workspace/configuration`
- Configuração específica por workspace folder
- Persistência de configuração
- Logging estruturado baseado em `logLevel`
- Completion snippets configuráveis na resposta LSP

## Deliverables

- `src/robot_lsp/application/configuration.py`
- Handler `workspace/didChangeConfiguration`
- Capability `workspace.didChangeConfiguration`
- Integração de `diagnostics.enable` no servidor
- Integração de `importPaths` no `WorkspaceIndex`
- Testes unitários de service, handler e import resolution

## Acceptance Criteria

- Defaults funcionam sem configuração
- `initializationOptions` aplica configuração inicial
- `workspace/didChangeConfiguration` atualiza configuração em runtime
- Diagnostics podem ser desabilitados
- Desabilitar diagnostics limpa diagnostics existentes dos documentos abertos
- `robot.lsp.importPaths` resolve imports `Resource` e `Variables`
- Valores inválidos são ignorados sem crash

## Tests

- `test_default_config`
- `test_update_from_direct_settings`
- `test_update_from_nested_robot_lsp_settings`
- `test_invalid_values_keep_previous_config`
- `test_resolve_resource_import_from_configured_import_path`
- `test_initialize_applies_initialization_options`
- `test_did_change_configuration_updates_settings`
- `test_diagnostics_disabled_does_not_schedule_on_did_open`
- `test_disabling_diagnostics_clears_open_document_diagnostics`

## Risks

- `workspace/configuration` ainda não é usado porque o servidor não tem loop de request outbound para o cliente.
- `logLevel` e `completion.snippets` são armazenados, mas ainda não alteram comportamento.
- `importPaths` é global no index, não específico por workspace folder.

## Dependencies

- Stage 03
- Stage 05
- Stage 09

## Notes

- O formato aceito é direto (`importPaths`) ou aninhado (`robot.lsp` / `robot: { lsp: ... }`).
