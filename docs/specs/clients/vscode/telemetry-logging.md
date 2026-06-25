# VS Code Telemetry And Logging

## Goal

Provide useful diagnostics without collecting user data by default.

## Logging

The extension should create a VS Code output channel named:

```text
Robot LSP
```

Log categories:

- Extension activation
- Python resolution
- Server startup command
- Server stderr
- Configuration changes
- Test discovery
- Run/debug startup
- Debug adapter lifecycle

## Sensitive Data

Logs must avoid printing secrets from:

- Environment variables
- Robot variables
- Launch configuration values known to be sensitive

## Telemetry

Telemetry is disabled by default for MVP.

If telemetry is added later, it must be opt-in and documented.

## User-Facing Errors

Startup errors should include actionable steps, such as:

```text
Robot LSP could not start because the selected Python cannot import robot_lsp.
Install robot-lsp into the selected environment or configure robot-lsp.languageServer.python.
```
