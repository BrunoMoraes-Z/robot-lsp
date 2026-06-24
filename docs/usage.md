# Usage

## Starting The Server

The language server runs over stdio:

```powershell
uv run python -m robot_lsp
```

Installed script entrypoint:

```powershell
uv run robot-lsp
```

## Version

```powershell
uv run python -m robot_lsp --version
```

## Logging

Logs are written to stderr so stdout remains reserved for LSP messages.

```powershell
uv run python -m robot_lsp --log-level debug
```

Supported levels: `debug`, `info`, `warning`, `error`.

## LSP Configuration

Configuration can be passed through `initializationOptions` or `workspace/didChangeConfiguration`.

```json
{
  "robot": {
    "lsp": {
      "importPaths": ["resources"],
      "logLevel": "info",
      "diagnostics": {"enable": true},
      "completion": {"snippets": true}
    }
  }
}
```

Implemented behavior:

- `importPaths` participates in `Resource` and `Variables` import resolution.
- `diagnostics.enable` controls diagnostic scheduling and clears diagnostics when disabled.
- `logLevel` and `completion.snippets` are stored for future feature integration.
