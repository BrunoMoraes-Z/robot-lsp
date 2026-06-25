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

### Test Explorer Smoke Tests

- Verify fallback discovery reads top-level tests under `*** Test Cases ***`.
- Verify fallback discovery reads top-level tasks under `*** Tasks ***`.
- Verify keyword definitions and indented steps are not exposed as tests.

### Run Support Smoke Tests

- Verify generated current-file run configurations use `noDebug: true`.
- Verify runtime Python, environment, Python path, and Robot variables are copied into generated run configurations.
- Verify generated current-test run configurations add `--test <name>` arguments.
- Verify current-test lookup selects the nearest top-level test or task for a cursor line.

### Debug Adapter Design Smoke Tests

- Verify generated debug launch configurations use `type: "robot-lsp"` and `request: "launch"`.
- Verify generated debug launch configurations use `noDebug: false`.
- Verify the VS Code manifest contributes debug type `robot-lsp` for `robotframework` files.
- Verify initial debug configuration and snippet target the current file.

### Debug Adapter MVP Smoke Tests

- Verify the adapter maps launch `python` to the process command.
- Verify `pythonPath` entries become `--pythonpath` Robot arguments.
- Verify Robot variables become `--variable name:value` arguments.
- Verify launch args are preserved before target paths.
- Verify string-array targets are appended to the Robot command.

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
