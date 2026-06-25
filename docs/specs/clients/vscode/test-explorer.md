# VS Code Test Explorer

## Goal

Expose Robot Framework tests in the VS Code Test Explorer and support run/debug from the tree.

## Test Controller

Controller id:

```text
robot-lsp.testController
```

Display name:

```text
Robot Framework
```

## Discovery Strategy

Preferred discovery:

1. The LSP indexes workspace files.
2. The LSP sends a custom notification such as `$/robotTestsCollected`.
3. The VS Code client maps collected tests to `TestItem` nodes.

Initial fallback discovery:

- Lightweight TypeScript scanner for top-level test cases in `.robot` files.
- Used when the LSP is not yet started or test notifications are unavailable.

## Tree Shape

```text
Workspace Folder
  File.robot
    Test Case Name
```

## Run Profiles

- Run
- Debug

## Run Flow

1. User starts a test from Test Explorer.
2. Extension builds a launch configuration.
3. Extension filters selected tests using environment or arguments.
4. Extension starts VS Code debugging with `noDebug: true` for run mode.
5. Debug adapter reports test events back to VS Code.

## Result Reporting

The debug adapter should emit custom DAP events for:

- suite started
- suite ended
- test started
- test passed
- test failed
- test skipped
- log message

The extension maps those events to `TestRun` state updates.
