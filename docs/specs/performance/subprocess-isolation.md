# Subprocess Isolation

## Stage

**Deferred** (Stage 12 decision)

## Motivation

In the MVP, the server runs everything in the same process. If workspace index or heavy analysis blocks the event loop, completion/hover become slow.

## Strategy

- **Do not implement subprocesses in the MVP**
- Monitor performance with real files
- If necessary, add a subprocess only for heavy operations

## Possible Architecture

```
Main Process (LSP lifecycle, completion, hover)
  └── Subprocess (workspace index, lint, analysis)
```

## Communication

- Subprocess also uses JSON-RPC over stdio (pipe) for communication
- Main process serializa requests e responses
- Subprocesso pode ser restartado independentemente

## Lessons from robotframework-lsp

- O LSP existente usa 3 subprocessos (api/lint/others)
- Para um MVP menor, 1 subprocesso suficiente
- Complexidade alta: gerenciar lifecycle, restart, timeout
- Defer until metrics justify it

## Notes

- Cross-process cancellation is more complex
- Pipe communication with JSON-RPC framing reuses existing code
- Subprocess needs its own `DocumentStore` (synchronized through `didOpen`/`didChange`)
- Stage 12 does not implement a subprocess because the operational cost is not yet justified by metrics.
