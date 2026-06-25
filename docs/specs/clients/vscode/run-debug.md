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
