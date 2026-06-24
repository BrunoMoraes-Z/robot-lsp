# ADR-0005 — Document Sync Strategy

## Status

accepted

## Context

O LSP precisa sincronizar documentos entre cliente e servidor. O protocolo suporta `None`, `Full` e `Incremental` sync.

## Decision

Começar com `TextDocumentSyncKind.Full` (envio do texto completo a cada `didChange`).

### Justificativa
- Simplicidade: não precisa aplicar diffs.
- Segurança: estado do documento nunca fica inconsistente.
- Robot Framework arquivos `.robot` costumam ter centenas de linhas, não milhares — enviar completo é aceitável.
- Podemos evoluir para `Incremental` depois se performance exigir.

## Consequences

- Maior uso de banda em documentos muito grandes.
- Parse é always full, simples e sem estado residual.
- Transição para incremental no futuro é compatível mudando `textDocumentSync` capability.

## Alternatives Considered

- Incremental sync: mais complexo, estado diff, risco de corrupção. Deixado para Stage 12.
