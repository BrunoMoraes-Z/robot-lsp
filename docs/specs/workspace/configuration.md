# Configuration

## Stage

**Done** (Stage 13)

## LSP Methods

- `workspace/didChangeConfiguration`
- `workspace/configuration` (deferred)

## Configuration Options

- `robot.lsp.importPaths`: caminhos adicionais para resolução de imports
- `robot.lsp.logLevel`: nível de log
- `robot.lsp.diagnostics.enable`: ligar/desligar diagnostics
- `robot.lsp.completion.snippets`: habilitar snippets

## Notes

- Configuração pode vir das `initializationOptions` ou `workspace/configuration`
- Valores padrão sensíveis para funcionar sem configuração

## Implemented

- Configuração inicial via `initializationOptions`.
- Atualização em runtime via `workspace/didChangeConfiguration`.
- Settings aceitas em formato direto, `robot.lsp` ou `robot: { lsp: ... }`.
- `diagnostics.enable` controla agendamento de diagnostics e limpa diagnostics publicados quando desligado.
- `importPaths` é usado pelo `WorkspaceIndex` para resolver imports de arquivo.
- `logLevel` controla o logger `robot_lsp` durante `initialize` e `workspace/didChangeConfiguration`.

## Deferred

- Request server-to-client `workspace/configuration`.
- Configuração específica por workspace folder.
- Aplicação de `completion.snippets` nos completion items.
