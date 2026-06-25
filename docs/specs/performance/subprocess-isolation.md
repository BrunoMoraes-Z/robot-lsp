# Subprocess Isolation

## Stage

**Evaluated** (post-MVP 07)

## Motivation

In the MVP, the server runs everything in the same process. If workspace index or heavy analysis blocks the event loop, completion/hover become slow.

## Strategy

- Keep the main LSP server in-process by default.
- Use subprocesses only for isolated heavy operations.
- Validate communication and workspace indexing in a dedicated worker before wiring it into the main server.

## Possible Architecture

```
Main Process (LSP lifecycle, completion, hover)
  └── Subprocess (workspace index, lint, analysis)
```

## Communication

- Subprocess also uses JSON-RPC over stdio (pipe) for communication
- Main process serializes requests and responses
- Subprocess can be restarted independently

## Lessons from robotframework-lsp

- The existing LSP uses 3 subprocesses (api/lint/others)
- For a smaller server, 1 subprocess is enough
- High complexity: lifecycle, restart, timeout management
- Defer until metrics justify it

## Evaluated Implementation

- `python -m robot_lsp.worker` starts an isolated JSON-RPC worker over stdio.
- `worker/ping` validates process communication and process identity.
- `workspace/scan` builds a `WorkspaceIndex` inside the worker and returns file, keyword, and variable counts.
- `shutdown` exits the worker cleanly.

## Integration Tests

- `test_worker_subprocess_ping_and_shutdown`
- `test_worker_subprocess_scans_workspace`

## Decision

- Subprocess isolation is technically viable with the existing JSON-RPC framing.
- Do not route main LSP requests through the worker yet; no measured hot path justifies the added lifecycle and synchronization complexity.
- Future integration should target workspace indexing first, because it has the clearest isolation boundary.

## Notes

- Cross-process cancellation is more complex
- Pipe communication with JSON-RPC framing reuses existing code
- Subprocess needs its own `DocumentStore` (synchronized through `didOpen`/`didChange`)
- Stage 12 did not wire subprocesses into the main server because the operational cost was not justified by metrics.
