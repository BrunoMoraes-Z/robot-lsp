# VS Code Client Usage

## Planned Usage

Install the VS Code extension, open a workspace with `.robot` or `.resource` files, and configure the Python environment if needed.

## Required Python Environment

The selected language server Python must be able to run:

```powershell
python -m robot_lsp
```

It must have:

- `robot-lsp`
- `robotframework>=7.0`

## Common Settings

```json
{
  "robot-lsp.languageServer.python": "",
  "robot-lsp.runtime.python": "",
  "robot-lsp.variables": {
    "EXECDIR": "${workspaceFolder}"
  },
  "robot-lsp.diagnostics.enable": true,
  "robot-lsp.completion.snippets": true
}
```

## Planned Commands

- Restart Language Server
- Select Python Interpreter
- Run Current File
- Run Current Test
- Debug Current File
- Debug Current Test
