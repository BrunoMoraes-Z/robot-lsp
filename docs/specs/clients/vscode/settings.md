# VS Code Settings

## Prefix

All settings use `robot-lsp.*`.

## Language Server Settings

| Setting | Type | Default | Purpose |
|---|---|---|---|
| `robot-lsp.languageServer.python` | string | `""` | Explicit Python executable for the language server |
| `robot-lsp.languageServer.command` | string | `""` | Full command override for starting the server |
| `robot-lsp.languageServer.args` | array | `[]` | Extra or override arguments for the server process |
| `robot-lsp.languageServer.cwd` | string | `""` | Working directory for the server process |
| `robot-lsp.languageServer.env` | object | `{}` | Environment variables for the server process |

## Runtime Settings

| Setting | Type | Default | Purpose |
|---|---|---|---|
| `robot-lsp.runtime.python` | string | `""` | Python executable for run/debug execution |
| `robot-lsp.runtime.env` | object | `{}` | Environment variables for run/debug execution |
| `robot-lsp.runtime.pythonPath` | array | `[]` | Entries added to `PYTHONPATH` or Robot `--pythonpath` |

## Robot Analysis Settings

| Setting | Type | Default | Purpose |
|---|---|---|---|
| `robot-lsp.variables` | object | `{}` | Robot variables injected into static analysis and run/debug |
| `robot-lsp.diagnostics.enable` | boolean | `true` | Enable diagnostics |
| `robot-lsp.completion.snippets` | boolean | `true` | Enable snippet completion |
| `robot-lsp.logLevel` | enum | `"warning"` | Server log level |

## Test And Debug Settings

| Setting | Type | Default | Purpose |
|---|---|---|---|
| `robot-lsp.testExplorer.enabled` | boolean | `true` | Enable VS Code Test Explorer integration |
| `robot-lsp.debug.allowKeywordEvaluate` | boolean | `false` | Allow debug console evaluation that executes Robot keywords |
| `robot-lsp.debug.breakOnFailure` | boolean | `true` | Break on Robot failure logs |
| `robot-lsp.debug.breakOnError` | boolean | `true` | Break on Robot error logs |

## Server Configuration Mapping

The extension maps VS Code settings into the server's `robot.lsp` configuration shape:

```json
{
  "diagnostics": {
    "enable": true
  },
  "completion": {
    "snippets": true
  },
  "logLevel": "warning",
  "variables": {
    "EXECDIR": "${workspaceFolder}"
  }
}
```

## Initial Implementation

Stage 04 implements the configuration bridge in the VS Code client:

- `robot-lsp.*` settings are normalized to the server's `robot.lsp` shape.
- `workspace/configuration` requests for `robot.lsp` are handled by client middleware.
- The same mapping is used for initialization options.
- `${workspaceFolder}` is expanded before values are sent to the server.
- `robot-lsp.variables` is consumed by the core LSP diagnostics engine.
