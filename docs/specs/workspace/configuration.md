# Configuration

## Stage

**Done** (Stage 13)

## LSP Methods

- `workspace/didChangeConfiguration`
- `workspace/configuration` (deferred)

## Configuration Options

- `robot.lsp.importPaths`: additional paths for import resolution
- `robot.lsp.logLevel`: log level
- `robot.lsp.diagnostics.enable`: enable/disable diagnostics
- `robot.lsp.completion.snippets`: enable snippets

## Notes

- Configuration may come from `initializationOptions` or `workspace/configuration`
- Sensible defaults to work without configuration

## Implemented

- Initial configuration through `initializationOptions`.
- Runtime updates through `workspace/didChangeConfiguration`.
- Settings accepted in direct format, `robot.lsp`, or `robot: { lsp: ... }`.
- `diagnostics.enable` controls diagnostic scheduling and clears published diagnostics when disabled.
- `importPaths` is used by `WorkspaceIndex` to resolve file imports.
- `logLevel` controls the `robot_lsp` logger during `initialize` and `workspace/didChangeConfiguration`.
- `completion.snippets` controls whether section completions use `insertTextFormat: Snippet`.

## Deferred

- Request server-to-client `workspace/configuration`.
- Workspace-folder-specific configuration.
