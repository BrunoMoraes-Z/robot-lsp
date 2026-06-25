# VS Code Run And Debug

## Goal

Run and debug Robot Framework files and individual tests from VS Code commands, editor context, and Test Explorer.

## Commands

- `robot-lsp.runCurrentFile`
- `robot-lsp.runCurrentTest`
- `robot-lsp.debugCurrentFile`
- `robot-lsp.debugCurrentTest`
- `robot-lsp.restartLanguageServer`
- `robot-lsp.selectPythonInterpreter`

## Launch Type

```text
robot-lsp
```

## Terminal Modes

| Mode | Behavior |
|---|---|
| `none` | Run as child process without user terminal |
| `integrated` | Run in VS Code integrated terminal |
| `external` | Run in external terminal |

## Launch Template

The extension should support a user-defined launch template named:

```text
Robot Framework: Launch Template
```

When commands or Test Explorer trigger a run/debug session, the extension merges the template with generated target information.

## Runtime Inputs

- Target file or test
- Workspace folder
- Runtime Python
- Runtime env
- Runtime python path
- Robot variables
- Additional Robot arguments

## Run Support MVP

- `robot-lsp.runCurrentFile` uses the active Robot Framework document as the launch target.
- `robot-lsp.runCurrentTest` uses the nearest discovered top-level test or task at the cursor line.
- Test Explorer Run profile uses the same generated launch configuration path.
- Generated run configurations use `type: "robot-lsp"`, `request: "launch"`, and `noDebug: true`.
- Individual test runs add `--test <name>` to Robot Framework arguments.
- Runtime Python, environment, Python path, and Robot variables come from `robot-lsp.runtime.*` and `robot-lsp.variables` settings.
- Actual debug adapter execution and test result events are implemented in later stages.

## Debug Support

- `robot-lsp.debugCurrentFile` starts a debug launch for the active Robot Framework document.
- `robot-lsp.debugCurrentTest` starts a debug launch for the nearest discovered test or task at the cursor line.
- Test Explorer exposes a Debug profile for discovered test items.
- Debug sessions use the `robot-lsp` debug adapter with `noDebug: false`.
- The adapter injects a Robot Framework listener to connect with the runtime for breakpoints, continue, and variable evaluate.
