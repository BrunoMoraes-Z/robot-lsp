# Stage 07 — Hover

## Status

planned

## Goal

Implementar hover para mostrar informações sobre símbolos sob o cursor: keywords, variáveis e imports.

## Scope

- `textDocument/hover` handler
- `HoverContext`: posição do cursor, documento, modelo parseado
- Providers:
  - **KeywordHoverProvider**: mostra assinatura (nome + args) e docstring de keywords locais
  - **VariableHoverProvider**: mostra tipo (scalar/list/dict/secret) e valor bruto
  - **ImportHoverProvider**: mostra tipo do import (Library/Resource/Variables) e caminho
- `Hover` response com `contents` (MarkupContent) e `range`
- Formatação Markdown para `contents`
- `null` se não encontrar nada no hover

## Out Of Scope

- Hover em keywords de bibliotecas externas (Stage 09)
- Hover em variáveis de escopo global ou arguments de keywords

## Deliverables

- `src/robot_lsp/application/hover_service.py`
- Providers em módulos internos
- Testes para cada provider

## Acceptance Criteria

- Hover em keyword local: retorna `**Nome(args)**\n\ndocstring` em markdown
- Hover em variável: retorna `**Tipo**: valor`
- Hover em import: retorna `**Library**: Nome` ou similar
- `range` no hover cobre o símbolo sob o cursor
- Retorna `null` se cursor não está sobre símbolo conhecido
- Markdown é formatado corretamente (cabeçalho, code, etc.)

## Tests

- `test_hover_local_keyword`
- `test_hover_variable`
- `test_hover_import`
- `test_hover_empty`
- `test_hover_range`
- `test_hover_markdown_format`

## Risks

- Identificar o símbolo exato sob o cursor requer análise de linha e coluna
- Docstrings multi-line precisam ser formatadas corretamente em markdown

## Dependencies

- Stage 04 (modelo RF)
