# VS Code Client Testing

## Test Layers

### Unit Tests

- Domain models and pure helpers
- Variable expansion
- Python resolution ordering with fake adapters
- Settings normalization
- Launch configuration merge

### Integration Tests

- Language client server options construction
- VS Code configuration adapter
- Test explorer tree creation
- Debug configuration provider

### Extension Host Tests

- Extension activates for `.robot` files
- Language client starts with a fake server command
- Commands are registered
- Test controller is registered
- Debug type is contributed

### Manual Smoke Tests

- Open `.robot` file
- Verify diagnostics
- Verify completion
- Verify hover
- Verify document symbols and folding
- Run current file
- Run current test
- Debug current test

## CI Commands

Expected future commands:

```powershell
cd clients/vscode
npm install
npm run compile
npm test
```

Core validation remains:

```powershell
uv run pytest
uv run python -m compileall src tests
```
