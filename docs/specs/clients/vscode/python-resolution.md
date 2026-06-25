# VS Code Python Resolution

## Goal

Resolve the Python interpreter used to start `robot-lsp` and the Python interpreter used for Robot runtime/debug execution.

These may be different. The language server Python must import `robot_lsp` and `robotframework`. The runtime Python must represent the user's project environment and contain project libraries.

## Language Server Python Order

1. `robot-lsp.languageServer.python`
2. Python selected by the VS Code Python extension
3. Workspace virtual environment candidates such as `.venv`, `venv`, or `.env`
4. `python` on Windows or `python3`/`python` on Linux and macOS
5. Show an actionable startup error

## Runtime Python Order

1. `robot-lsp.runtime.python`
2. Python selected by the VS Code Python extension
3. Resolved language server Python
4. PATH fallback
5. Show an actionable run/debug error

## Validation

The resolved language server Python should pass:

```powershell
python -c "import robot_lsp, robot; print(robot.version.VERSION)"
```

The extension should verify that Robot Framework is at least 7.0.

## Variable Expansion

Interpreter settings may contain:

- `${workspaceFolder}`
- `${env:NAME}`
- `~`

Expansion happens in the VS Code client before process startup.

## Errors

Startup errors should include:

- Resolved command
- Workspace folder
- Failed import or version check
- Suggested fix, such as installing `robot-lsp` and `robotframework>=7.0` into the selected interpreter
