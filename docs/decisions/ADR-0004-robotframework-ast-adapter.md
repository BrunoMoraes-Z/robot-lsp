# ADR-0004 — Robot Framework AST Adapter

## Status

accepted

## Context

The Robot Framework AST changes between versions (for example, `Return` -> `ReturnSetting` in 7.0, `Group` added in 7.2). We need to isolate the LSP core from those changes.

## Decision

Create an adapter layer in `infrastructure/robotframework/` that:

1. Uses only public APIs from `robot.api.parsing` (never `robot.parsing.*`).
2. Defines custom intermediate models in `domain/models.py`.
3. Maps RF AST nodes -> intermediate models.
4. Keeps the LSP core working only with intermediate models.

### Intermediate Models
- `RobotSuite`, `RobotSettings`, `RobotVariable`, `RobotImport`
- `RobotTestCase`, `RobotKeyword`, `RobotStep`, `RobotArg`
- `RobotDiagnostic`

### Versioning
- `FeatureSet` contains flags based on the RF version.
- New AST nodes are mapped conditionally when available.

## Consequences

- RF AST changes affect only the adapter.
- Adapter tests fail first when RF changes, protecting the rest of the code.
- The LSP core remains stable across RF versions.

## Alternatives Considered

- Use the RF AST directly: rejected because of breakage risk between versions.
- Monkey-patching the AST: rejected because it is fragile.
