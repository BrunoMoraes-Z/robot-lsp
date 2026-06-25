# VS Code Client Clean Architecture

## Goal

Keep the VS Code extension maintainable, testable, and isolated from editor APIs outside infrastructure and presentation boundaries.

## Proposed Source Layout

```text
clients/vscode/src/
  extension.ts

  domain/
    models.ts
    settings.ts
    diagnostics.ts

  application/
    activateExtension.ts
    resolvePython.ts
    buildServerOptions.ts
    buildClientOptions.ts
    collectTests.ts
    resolveLaunchConfig.ts

  infrastructure/
    vscode/
      workspaceConfig.ts
      pythonExtension.ts
      languageClient.ts
      testController.ts
      debugAdapter.ts
      variableExpansion.ts
      logging.ts

  presentation/
    commands.ts
    notifications.ts
    statusBar.ts
```

## Layer Rules

### Domain

- Pure TypeScript types and small deterministic helpers.
- No `vscode` imports.
- No `vscode-languageclient` imports.
- Defines contracts such as `PythonExecutable`, `ResolvedPython`, `RobotLspSettings`, `LaunchTarget`, and `RobotTestItem`.

### Application

- Editor-agnostic use cases.
- No direct dependency on `vscode` APIs.
- Coordinates interpreter resolution, server startup planning, configuration normalization, test collection, and launch configuration normalization.

### Infrastructure

- Concrete adapters for VS Code APIs and external extensions.
- Owns `vscode.workspace`, `vscode.extensions`, `vscode-languageclient`, `vscode.tests`, and debug adapter registration.
- Converts VS Code objects into domain/application contracts.

### Presentation

- Commands, notifications, status items, and user-facing messages.
- May depend on VS Code APIs.
- Must delegate business decisions to application services.

### Composition Root

`extension.ts` wires all dependencies and registers activation/deactivation. It should contain minimal logic.

## Dependency Direction

```text
extension.ts -> application -> domain
infrastructure -> application/domain
presentation -> application/domain
```

Infrastructure and presentation may import `vscode`. Domain and application must not.

## Testing Strategy

- Unit-test domain helpers without VS Code.
- Unit-test application services with fake infrastructure ports.
- Integration-test VS Code adapters separately using extension host tests.
- Keep process spawning behind interfaces for deterministic tests.
