# Stage 02 — LSP Lifecycle

## Status

done

## Goal

Implement the basic LSP lifecycle: initialize, initialized, shutdown, and exit, with server states and minimal capabilities.

## Scope

- `initialize` request: process ClientCapabilities and return ServerCapabilities
- `initialized` notification
- `shutdown` request: prepare server for shutdown
- `exit` notification: terminate process
- States: `uninitialized`, `running`, `shuttingDown`, `exited`
- Validation: messages before `initialize` return an error; messages after `shutdown` return an error
- Minimal capabilities:
- `textDocumentSync`: Full
- `completionProvider`: triggerCharacters=[" "], resolveProvider=false
- `hoverProvider`: true

## Out Of Scope

- Functional diagnostics, completion, or hover (only declare capabilities)

## Deliverables

- `src/robot_lsp/protocol/server.py` with `LspServer`
- `src/robot_lsp/protocol/lsp_types.py` with auxiliary types
- LSP session tests through in-memory transport

## Acceptance Criteria

- Server responds to `initialize` with correct `capabilities`
- ServerCapabilities include `textDocumentSync: { openClose: true, change: Full }`
- `initialized` does not generate a response (it is a notification)
- `shutdown` returns `null`
- `exit` terminates the process
- Requests before `initialize` return error `-32002` (server not initialized)
- Requests after `shutdown` return error `-32003` (server shutting down)

## Tests

- `test_initialize`
- `test_initialized`
- `test_shutdown`
- `test_exit`
- `test_request_before_initialize`
- `test_request_after_shutdown`
- `test_capabilities_format`

## Risks

- Shutdown state must be atomic to avoid race conditions

## Dependencies

- Stage 01

## Notes

- Stage completed with `LspServer`, `ServerState`, `TextDocumentSyncKind`, and initial capabilities.
- `textDocumentSync` returns `{ "openClose": true, "change": Full }` according to the acceptance criteria.
- `exit` sets `exit_code=0` only after `shutdown`; otherwise it sets `exit_code=1`.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
