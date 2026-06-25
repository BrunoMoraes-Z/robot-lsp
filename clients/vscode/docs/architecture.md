# VS Code Client Architecture

## Overview

The VS Code extension is an editor adapter for `robot-lsp`. It starts the Python language server, bridges VS Code settings into server configuration, contributes Robot Framework language metadata, and owns VS Code-specific run/debug/test UI.

## Layers

```text
extension.ts
  application/
    domain/
  infrastructure/vscode/
  presentation/
```

The extension follows the Clean Architecture rules in `docs/specs/clients/vscode/clean-architecture.md`.

## Key Components

- Language client startup
- Python interpreter resolution
- Settings and configuration bridge
- Variable expansion
- Syntax highlighting and language configuration
- Test Explorer integration
- Run/debug commands
- Debug adapter registration

## Boundaries

- The core LSP remains in `src/robot_lsp` and must not import VS Code code.
- VS Code APIs remain in `clients/vscode/src/infrastructure` and `clients/vscode/src/presentation`.
- Application services are testable without the VS Code extension host.
