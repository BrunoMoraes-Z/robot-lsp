# VS Code Debug Adapter

## Goal

Support Robot Framework debugging from VS Code with breakpoints in Robot files and Python libraries.

## Architecture

```text
VS Code Extension
  -> Debug Adapter Protocol over stdio
Python Debug Adapter
  -> Robot target process
  -> debugpy for Python breakpoints
```

## Responsibilities

### VS Code Extension

- Registers the debug type `robot-lsp`.
- Provides launch configuration snippets.
- Resolves runtime Python and launch settings.
- Starts the Python debug adapter.
- Maps custom DAP test events to Test Explorer results.

### Python Debug Adapter

- Implements DAP request/response/event handling.
- Launches Robot Framework execution.
- Routes `.robot` and `.resource` breakpoints to Robot-aware breakpoint handling.
- Routes `.py` breakpoints to `debugpy`.
- Provides stack traces, scopes, variables, stepping, continue, pause, and evaluate.

### Robot Target Process

- Executes Robot Framework.
- Emits suite/test/keyword events.
- Cooperates with the debug adapter for breakpoint suspension.

## Breakpoint Routing

| File Type | Handler |
|---|---|
| `.robot` | Robot breakpoint engine |
| `.resource` | Robot breakpoint engine |
| `.py` | `debugpy` |

## Evaluate

Supported evaluate modes:

- Robot variable lookup
- Simple expression evaluation
- Optional keyword execution in the current context

Keyword execution must be disabled by default and controlled by:

```json
{
  "robot-lsp.debug.allowKeywordEvaluate": false
}
```

## Risks

- Robot Framework internals may change between versions.
- Keyword evaluation can mutate runtime state.
- Python and Robot breakpoints require coordination between two debug engines.
- `debugpy` must be installed or bundled for Python debugging.

## Initial MVP

- Launch Robot with no-debug mode.
- Support run/test result reporting.
- Add Robot breakpoints after runner integration is stable.
- Add Python breakpoints through `debugpy` after Robot breakpoints work.
