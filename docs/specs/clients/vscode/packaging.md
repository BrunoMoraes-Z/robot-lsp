# VS Code Packaging

## Goal

Package the VS Code extension as a VSIX while keeping the Python language server distribution explicit.

## Initial Packaging Model

The extension does not bundle Python or a virtual environment.

Users must provide a Python environment that can run:

```powershell
python -m robot_lsp
```

This keeps the extension small and respects project-specific environments.

## Future Packaging Options

| Option | Pros | Cons |
|---|---|---|
| User-managed Python | Small extension, project-aware | Requires setup |
| Bundled wheel | Easier install | Still needs Python and dependencies |
| Bundled virtualenv | Best out-of-box startup | Large package, platform complexity |
| Native executable | Best isolation | Build/release complexity |

## VSIX Contents

- TypeScript extension output
- Language configuration
- TextMate grammar
- README and changelog
- License file
- Runtime `node_modules` dependencies required by the extension
- No Python virtual environment in MVP

## Exclusions

- TypeScript source files
- Tests
- Client docs
- Source maps
- Generated VSIX artifacts
- Lockfile and TypeScript project files

## Release Checks

- Compile TypeScript
- Run extension unit tests
- Run package smoke checks
- Package VSIX
- Smoke-test extension host startup
- Verify startup error when Python dependencies are missing

## Commands

```powershell
cd clients/vscode
npm run check
npm test
npm run package:check
npm run package
```

The generated `robot-lsp-vscode.vsix` is a release artifact and should not be committed.
