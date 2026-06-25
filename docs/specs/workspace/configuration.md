# Configuration

## Stage

**Done** (Stage 13)

## LSP Methods

- `workspace/didChangeConfiguration`
- `workspace/configuration`

## Configuration Options

- `robot.lsp.importPaths`: additional paths for import resolution
- `robot.lsp.logLevel`: log level
- `robot.lsp.diagnostics.enable`: enable/disable diagnostics
- `robot.lsp.completion.snippets`: enable snippets

## Notes

- Configuration may come from `initializationOptions` or `workspace/configuration`
- Sensible defaults to work without configuration
- `workspace/configuration` is requested after `initialized` when the client advertises `workspace.configuration: true`

## Implemented

- Initial configuration through `initializationOptions`.
- Runtime updates through `workspace/didChangeConfiguration`.
- Settings accepted in direct format, `robot.lsp`, or `robot: { lsp: ... }`.
- `diagnostics.enable` controls diagnostic scheduling and clears published diagnostics when disabled.
- `importPaths` is used by `WorkspaceIndex` to resolve file imports.
- `logLevel` controls the `robot_lsp` logger during `initialize` and `workspace/didChangeConfiguration`.
- `completion.snippets` controls whether section completions use `insertTextFormat: Snippet`.
- Outbound `workspace/configuration` requests are queued and flushed through the stdio loop.
- Client responses update global configuration and workspace-folder-specific configuration.
- Workspace-folder-specific `diagnostics.enable` and `completion.snippets` are resolved by matching document URI to the most specific configured folder.

## Deferred

- Per-folder `importPaths` integration in `WorkspaceIndex` resolution.
