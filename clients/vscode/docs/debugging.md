# VS Code Client Debugging

## Planned Debug Support

The extension will contribute a debug type named `robot-lsp`.

## Minimal Launch Configuration

```json
{
  "type": "robot-lsp",
  "request": "launch",
  "name": "Robot Framework: Current File",
  "target": "${file}",
  "cwd": "${workspaceFolder}"
}
```

## Planned Capabilities

- Run current file
- Run current test
- Debug current file
- Debug current test
- Breakpoints in `.robot` and `.resource`
- Breakpoints in `.py` through `debugpy`
- Stack traces for suites, tests, and keywords
- Debug console evaluation

## Security

Keyword execution through debug console evaluation is disabled by default and controlled by `robot-lsp.debug.allowKeywordEvaluate`.
