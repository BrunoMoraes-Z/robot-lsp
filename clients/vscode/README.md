# Robot LSP VS Code Client

VS Code extension client for `robot-lsp`.

This package currently contains the Stage 02 language client startup implementation.

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
- Registers a restart command for the language server.
- Leaves full Python interpreter resolution for Stage 03.
- Compiles with strict TypeScript settings.

See `docs/roadmap.md` for the staged implementation plan.
