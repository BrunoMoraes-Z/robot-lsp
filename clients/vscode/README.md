# Robot LSP VS Code Client

VS Code extension client for `robot-lsp`.

This package currently contains the Stage 03 Python resolution implementation.

## Development

```powershell
npm install
npm run compile
```

## Current Scope

- Registers the `robotframework` language for `.robot` and `.resource` files.
- Contributes `robot-lsp.*` settings.
- Starts `robot-lsp` over stdio using `vscode-languageclient`.
- Supports `robot-lsp.languageServer.*` command overrides.
- Resolves Python from explicit setting, VS Code Python extension, workspace virtual environment, or PATH.
- Validates that the selected Python can import `robot_lsp` and `robotframework>=7.0`.
- Registers a restart command for the language server.
- Leaves configuration bridge refinement for Stage 04.
- Compiles with strict TypeScript settings.

See `docs/roadmap.md` for the staged implementation plan.
