# VS Code Client Testing

## Planned Test Commands

```powershell
cd clients/vscode
npm run compile
npm test
```

## Test Targets

- Unit tests for pure TypeScript modules
- Integration tests for VS Code adapters
- Extension host tests for activation and contributions
- Manual smoke tests against the real Python LSP

## Core Compatibility

The VS Code client must not break core validation:

```powershell
uv run pytest
uv run python -m compileall src tests
```
