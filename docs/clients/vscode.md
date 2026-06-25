# VS Code Client

## Goal

Provide a first-party VS Code extension that starts `robot-lsp`, connects through `vscode-languageclient`, and exposes Robot Framework language features, run/debug support, and Test Explorer integration.

## Scope

- Language activation for `.robot` and `.resource` files.
- LSP startup over stdio.
- Python interpreter resolution that respects the active workspace.
- Configuration bridge from VS Code settings to `robot.lsp` server configuration.
- Static Robot variable injection through settings.
- Syntax highlighting and language configuration.
- Test Explorer discovery, run, and debug support.
- Custom debug adapter support for Robot Framework and Python library breakpoints.

## Settings Prefix

All VS Code settings use the `robot-lsp.*` prefix to avoid conflicts with existing Robot Framework extensions.

Examples:

```json
{
  "robot-lsp.languageServer.python": "",
  "robot-lsp.runtime.python": "",
  "robot-lsp.variables": {
    "EXECDIR": "${workspaceFolder}"
  }
}
```

## Implementation Strategy

The VS Code client will be implemented in TypeScript under `clients/vscode`. The extension must not mix all logic in `extension.ts`; it should use a Clean Architecture structure documented in `docs/specs/clients/vscode/clean-architecture.md`.

## Initial Execution Model

In development, the extension can start the server with:

```powershell
uv run python -m robot_lsp
```

For normal users, the extension should resolve a Python interpreter and run:

```powershell
python -m robot_lsp
```

The selected Python must be able to import both `robot_lsp` and `robotframework`.

## Related Specs

- `docs/specs/clients/vscode/clean-architecture.md`
- `docs/specs/clients/vscode/python-resolution.md`
- `docs/specs/clients/vscode/settings.md`
- `docs/specs/clients/vscode/language-client.md`
- `docs/specs/clients/vscode/test-explorer.md`
- `docs/specs/clients/vscode/debug-adapter.md`
