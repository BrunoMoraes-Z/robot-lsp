# VS Code Launch Configuration

## Debug Type

```json
{
  "type": "robot-lsp"
}
```

## Minimal Launch Configuration

```json
{
  "type": "robot-lsp",
  "request": "launch",
  "name": "Robot Framework: Current File",
  "target": "${file}",
  "cwd": "${workspaceFolder}"
}
```

## Full Launch Configuration

```json
{
  "type": "robot-lsp",
  "request": "launch",
  "name": "Robot Framework: Launch",
  "target": "${file}",
  "suiteTarget": "",
  "cwd": "${workspaceFolder}",
  "args": [],
  "env": {},
  "variables": {},
  "python": "",
  "pythonPath": [],
  "terminal": "integrated",
  "makeSuite": true,
  "noDebug": true
}
```

## Fields

| Field | Type | Default | Purpose |
|---|---|---|---|
| `target` | string or array | `${file}` | File, folder, suite, or test target |
| `suiteTarget` | string or array | `""` | Optional suite target used when generating suites |
| `cwd` | string | `${workspaceFolder}` | Runtime working directory |
| `args` | array | `[]` | Extra Robot Framework command-line arguments |
| `env` | object | `{}` | Launch-specific environment variables |
| `variables` | object | `{}` | Launch-specific Robot variables |
| `python` | string | `""` | Launch-specific Python override |
| `pythonPath` | array | `[]` | Launch-specific Python path entries |
| `terminal` | enum | `integrated` | Terminal mode |
| `makeSuite` | boolean | `true` | Whether to execute using suite-oriented behavior |
| `noDebug` | boolean | `true` for Run | Whether the generated launch is a run session rather than a debug session |

## Merge Order

1. Generated command/test target
2. Launch configuration
3. Launch template
4. Workspace settings
5. User settings
6. Defaults
