# Robot LSP VS Code Client

VS Code extension client for `robot-lsp`.

The extension does not bundle Python or a virtual environment. Configure or select a Python environment that can run `python -m robot_lsp` and has `robotframework>=7.0` installed.

## Development

```powershell
npm install
npm run compile
npm test
npm run package:check
```

## Current Scope

- Registers the `robotframework` language for `.robot` and `.resource` files.
- Contributes `robot-lsp.*` settings.
- Starts `robot-lsp` over stdio using `vscode-languageclient`.
- Resolves Python from explicit setting, VS Code Python extension, workspace virtual environment, or PATH.
- Provides syntax highlighting and Robot-aware language configuration.
- Bridges VS Code settings to the server `robot.lsp` configuration shape.
- Adds Test Explorer discovery for Robot tests and tasks.
- Supports run current file/test through generated `robot-lsp` launch configurations.
- Provides a no-debug Robot execution adapter MVP.
- Compiles with strict TypeScript settings.

## Packaging

```powershell
npm run package
```

The generated VSIX keeps the Python language server as an explicit user-managed dependency.

See `docs/roadmap.md` for the staged implementation plan.
