# ADR-0005 — Document Sync Strategy

## Status

accepted

## Context

LSP needs to synchronize documents between client and server. The protocol supports `None`, `Full`, and `Incremental` sync.

## Decision

Start with `TextDocumentSyncKind.Full` (send the full text on each `didChange`).

### Rationale
- Simplicity: no need to apply diffs.
- Safety: document state never becomes inconsistent.
- Robot Framework `.robot` files usually have hundreds of lines, not thousands, so sending the full text is acceptable.
- We can evolve to `Incremental` later if performance requires it.

## Consequences

- Higher bandwidth usage for very large documents.
- Parsing is always full, simple, and has no residual state.
- A future transition to incremental sync is compatible by changing the `textDocumentSync` capability.

## Alternatives Considered

- Incremental sync: more complex, diff state, corruption risk. Deferred to Stage 12.
