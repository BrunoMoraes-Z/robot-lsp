# Robot LSP VS Code Client

VS Code extension client for `robot-lsp`.

This package currently contains the Stage 01 scaffold: extension metadata, language contribution, settings contribution, and a Clean Architecture TypeScript source layout.

## Development

```powershell
npm install
npm run compile
```

## Current Scope

- Registers the `robotframework` language for `.robot` and `.resource` files.
- Contributes `robot-lsp.*` settings.
- Registers placeholder commands for future language server restart and interpreter selection.
- Does not start the Python language server yet.
- Compiles with strict TypeScript settings.

See `docs/roadmap.md` for the staged implementation plan.
