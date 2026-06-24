# ADR-0003 — JSON-RPC Without pygls

## Status

accepted

## Context

Precisamos decidir como implementar o protocolo LSP. As opções são usar pygls (biblioteca Python para LSP) ou implementar JSON-RPC e transporte próprios.

## Decision

Implementar JSON-RPC 2.0 e o transporte LSP (`Content-Length` framing sobre `stdio`) como código próprio, sem utilizar `pygls`, `python-lsp-server` ou `robocorp_ls_core`.

## Consequences

### Positive
- Controle total do lifecycle do protocolo.
- Sem acoplamento com versões de terceiros.
- Possibilidade de otimizações específicas (cancelamento, tracing, performance).
- Código mínimo e enxuto para o que realmente precisamos.

### Negative
- Mais código para manter.
- Responsabilidade por compatibilidade com especificação LSP.
- Precisa implementar corretamente edge cases do protocolo.

## Alternatives Considered

- pygls: abstrai JSON-RPC e LSP, mas esconde detalhes de implementação e adiciona dependência pesada.
- python-lsp-server: focado em Python, não se adapta bem ao Robot Framework.
- robocorp_ls_core: reaproveitar o código do LSP existente, mas é proprietário e complexo.
