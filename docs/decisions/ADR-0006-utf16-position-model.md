# ADR-0006 — UTF-16 Position Model

## Status

accepted

## Context

O protocolo LSP especifica que posições (line, column) usam line como 0-based integer e column como 0-based UTF-16 code units. Python strings usam índices baseados em code points, e caracteres como emoji (que ocupam 2 UTF-16 code units) causam discrepância se ignorados.

## Decision

Adotar UTF-16 code units para todas as posições LSP, com uma camada de conversão dedicada:

- `LspPosition.line`: 0-based line number.
- `LspPosition.character`: 0-based UTF-16 code unit offset.
- Implementar funções de conversão `robot_lsp.domain.positions`:
  - `utf16_offset_to_position(text, offset)`
  - `position_to_utf16_offset(text, line, character)`
  - `calculate_lsp_range(text, start_line, start_col, end_line, end_col)`
- Testar com caracteres ASCII, acentos (1 code unit) e emoji (2 code units).

## Consequences

- Posições enviadas ao cliente LSP estarão corretas independente do conteúdo.
- Complexidade extra na conversão, mas isolada em `domain/positions.py`.
- Testes específicos para caracteres multi-byte.

## Alternatives Considered

- Ignorar UTF-16 e usar índices Python diretos: rejeitado — causa bugs com emoji e acentos em editores.
- Usar biblioteca externa: rejeitado para evitar dependência em funcionalidade simples.
