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

Stage 09 covers the extension-side debug type, launch snippets, and debug configuration provider contract. Stage 10 adds a minimal Node-based debug adapter runtime for no-debug Robot execution. A Python debug adapter with breakpoints is deferred.

## VS Code Contribution

- Debug type: `robot-lsp`
- Label: `Robot LSP`
- Language: `robotframework`
- Activation: debug sessions activate the extension through `onDebug`
- Initial configuration: current Robot Framework file with `${file}` target and `${workspaceFolder}` cwd
- Configuration snippet: `Robot Framework: Current File`

## Debug Configuration Provider

The provider normalizes launch configurations before VS Code starts a session:

- `type` is forced to `robot-lsp`.
- `request` is forced to `launch`.
- Missing `name` uses a Robot Framework default.
- Missing `target` uses the active Robot Framework editor when available, otherwise `${file}`.
- Missing `cwd` uses the workspace folder when available, otherwise `${workspaceFolder}`.
- Missing `noDebug` defaults to `false` for debug sessions.

### Python Debug Adapter

- Implements DAP request/response/event handling.
- Launches Robot Framework execution.
- Routes `.robot` and `.resource` breakpoints to Robot-aware breakpoint handling.
- Routes `.py` breakpoints to `debugpy`.
- Provides stack traces, scopes, variables, stepping, continue, pause, and evaluate.

The Python debug adapter is not part of the Stage 10 MVP.

### Stage 10 Node Adapter MVP

- Runs as a Node process launched by `DebugAdapterExecutable`.
- Handles `initialize`, `launch`, `setBreakpoints`, `configurationDone`, `threads`, `stackTrace`, `scopes`, `variables`, `evaluate`, `continue`, `disconnect`, and `terminate` requests.
- Supports run sessions with `noDebug: true` and debug sessions with `noDebug: false`.
- Executes Robot Framework as `python -m robot` or with the launch-specific `python` executable.
- Starts a localhost runtime bridge and injects a Robot Framework listener with `--listener`.
- Maps `pythonPath` to `--pythonpath` arguments.
- Maps `variables` to `--variable name:value` arguments.
- Appends launch `args` before the target path or target list.
- Forwards Robot stdout and stderr as DAP output events.
- Forwards listener JSON events as DAP console output events.
- Stops on Robot listener breakpoint events and emits DAP `stopped` events.
- Continues paused Robot execution through the runtime bridge.
- Evaluates Robot variables while execution is paused.
- Emits `exited` and `terminated` when the process closes.

## Robot Runtime Listener

Listener class:

```text
robot_lsp.debug.listener.RobotLspDebugListener
```

The adapter injects it as:

```text
--listener robot_lsp.debug.listener.RobotLspDebugListener:<port>:<token>
```

The listener connects back to the Node adapter over localhost and sends newline-delimited JSON events for suites, tests, and Robot log messages. The token prevents unrelated local connections from being accepted as Robot runtime events.

This bridge is the runtime connection point for breakpoint suspension and evaluate support. The current adapter implements a minimal version based on listener callbacks: breakpoints are checked at Robot keyword start, execution blocks inside the listener, and `continue` resumes the Robot thread.

## Current Limits

- Breakpoints are keyword-line based and depend on Robot Framework listener source/line metadata.
- Stepping is not implemented.
- Evaluate supports Robot variable lookup while paused, not arbitrary keyword execution.
- Python breakpoints through `debugpy` are not implemented.

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
