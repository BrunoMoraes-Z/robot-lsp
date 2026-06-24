# Code Action

## Stage

**Done** (Stage 11)

## LSP Methods

- `textDocument/codeAction`

## Notes

Quick actions iniciais para diagnostics conhecidos.

## Behavior

- `textDocument/codeAction` retorna lista vazia quando o documento não está aberto.
- Diagnostics com `code: parse_error` retornam uma action `quickfix` informativa.
- Diagnostics com `code: import_not_found` retornam uma action `quickfix` informativa.
- Actions incluem o diagnostic original em `diagnostics`.

## Out Of Scope

- Aplicar edits automáticos para corrigir parse errors.
- Resolver imports ausentes por busca no workspace.
- Corrigir variáveis não definidas.
- `codeAction/resolve`.
