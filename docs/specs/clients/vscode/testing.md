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

### LSP Feature Smoke Tests

- Compile the VS Code client before execution.
- Verify the `robotframework` document selector includes file and untitled documents.
- Verify default server startup uses `python -m robot_lsp` style arguments.
- Verify explicit `robot-lsp.languageServer.command` bypasses default Python startup.
- Verify client settings map to the server `robot.lsp` configuration shape.
- Verify initialization options and workspace configuration use the same configuration bridge.

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

VS Code client validation:

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
