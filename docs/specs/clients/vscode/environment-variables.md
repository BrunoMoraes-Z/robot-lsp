# VS Code Environment And Robot Variables

## Goal

Support project-specific runtime context without forcing users to configure global machine state.

## Environment Variables

Environment variables are process-level values.

Language server process environment:

```json
{
  "robot-lsp.languageServer.env": {
    "MY_ENV": "value"
  }
}
```

Runtime/debug process environment:

```json
{
  "robot-lsp.runtime.env": {
    "API_URL": "https://example.local"
  }
}
```

## Robot Variables

Robot variables are Robot Framework variables used for static analysis and run/debug execution.

```json
{
  "robot-lsp.variables": {
    "EXECDIR": "${workspaceFolder}",
    "ENV": "dev"
  }
}
```

Expected run/debug command mapping:

```text
--variable EXECDIR:<expanded workspace folder>
--variable ENV:dev
```

Expected LSP mapping:

- Variables are sent through `workspace/configuration`.
- The server uses them to avoid false undefined-variable diagnostics.
- Completion/hover support for configured variables can be added later using the same configuration source.

## Expansion Rules

The VS Code client expands:

- `${workspaceFolder}`
- `${workspaceFolder:name}` when supported by VS Code APIs
- `${file}` for launch/debug contexts
- `${env:NAME}`
- `~`

## Precedence

1. Launch configuration values
2. Workspace folder settings
3. Workspace settings
4. User settings
5. Defaults
