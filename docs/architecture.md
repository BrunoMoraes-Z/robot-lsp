# Architecture

## Overview

Clean Architecture with explicit layer separation. Data flow always points inward: protocol -> application -> domain, with infrastructure injected at the edges.

```
  ┌─────────────────────────────────────────┐
  │              Protocol Layer              │
  │  JSON-RPC, LSP Framing, Transport stdio │
  │  Server, Dispatch                       │
  └────────────────┬────────────────────────┘
                   │ LSP Methods
  ┌────────────────▼────────────────────────┐
  │           Application Layer              │
  │  DocumentStore, Workspace               │
  │  ParseService, DiagnosticService        │
  │  CompletionService, HoverService        │
  └────────────────┬────────────────────────┘
                   │ Domain Calls
  ┌────────────────▼────────────────────────┐
  │             Domain Layer                 │
  │  Models, Positions, Ranges, Diagnostics │
  │  FeatureFlags, Contracts                │
  └─────────────────────────────────────────┘
  ┌─────────────────────────────────────────┐
  │          Infrastructure Layer            │
  │  RobotFramework Parser, Adapter,        │
  │  Version Detector, Visitors             │
  └─────────────────────────────────────────┘
```

## Layer Rules

### Domain Layer (`src/robot_lsp/domain/`)
- Pure Python with `dataclasses` and standard types.
- No external dependencies (not Robot Framework, LSP, or JSON-RPC).
- Intermediate LSP models: `LspRange`, `LspPosition`, `LspDiagnostic`.
- Intermediate Robot models: `RobotSuite`, `RobotTestCase`, `RobotKeyword`, `RobotVariable`, `RobotStep`, `RobotImport`, `RobotSettings`, `RobotArg`.
- `FeatureSet`: Robot Framework version information and active capabilities.

### Application Layer (`src/robot_lsp/application/`)
- LSP use cases.
- Depends only on `domain/`.
- `DocumentStore`: manages open documents.
- `Workspace`: manages workspace files.
- `ParseService`: coordinates parsing through infrastructure.
- `DiagnosticService`: coordinates diagnostic generation and publication.
- `CompletionService`: coordinates completion.
- `HoverService`: coordinates hover.

### Protocol Layer (`src/robot_lsp/protocol/`)
- Pure JSON-RPC 2.0.
- LSP framing over `stdio`.
- `Endpoint`: request/notification routing.
- `Dispatch`: maps LSP methods to handlers.
- `Server`: LSP server state and lifecycle handlers.
- Depends on `application/` and `domain/`.

### Infrastructure Layer (`src/robot_lsp/infrastructure/`)
- Concrete implementations: Robot Framework parser, AST adapter.
- The only layer that imports `robotframework`.
- `robotframework/version.py`: version detector.
- `robotframework/parser.py`: parsing through `robot.api.parsing`.
- `robotframework/adapter.py`: maps RF AST -> intermediate model.
- `robotframework/visitors.py`: visitors for extracting AST information.

## Dependency Rule

- Outer layers depend on inner layers.
- `domain/` depends on nothing.
- `application/` depends only on `domain/`.
- `protocol/` depends on `application/` and `domain/`.
- `infrastructure/` depends on `domain/` (returns models).
- No outer layer knows the internal implementation of another outer layer.

## Project Layout

```
src/robot_lsp/
  __init__.py
  __main__.py          # python -m robot_lsp
  main.py               # bootstrap, DI, startup

  domain/
    __init__.py
    models.py           # RobotSuite, RobotTestCase, RobotKeyword, etc.
    positions.py        # LspPosition, LspRange, conversion
    diagnostics.py      # LspDiagnostic, DiagnosticSeverity
    features.py         # FeatureSet, VersionInfo

  application/
    __init__.py
    document_store.py   # DocumentStore, Document
    workspace.py        # Workspace
    parse_service.py    # ParseService
    diagnostic_service.py  # DiagnosticService
    completion_service.py  # CompletionService
    hover_service.py       # HoverService

  infrastructure/
    __init__.py
    robotframework/
      __init__.py
      version.py        # RobotFrameworkVersionDetector
      parser.py         # RobotFrameworkParser
      adapter.py        # RobotFrameworkASTAdapter
      visitors.py       # specialized AST visitors

  protocol/
    __init__.py
    jsonrpc.py          # JsonRpcMessage, encode/decode
    transport_stdio.py  # TransportStdio (Content-Length reader/writer)
    endpoint.py         # Endpoint (dispatch/cancellation)
    dispatch.py         # MethodDispatcher
    lsp_types.py        # auxiliary LSP types
    server.py           # LspServer (lifecycle, handlers)

  adapters/
    __init__.py
    cli.py              # CLI bootstrap

tests/
  conftest.py
  unit/
    domain/
    application/
    protocol/
    infrastructure/
  integration/
    conftest.py
    fixtures/
      basic_suite.robot
      settings.robot
      variables.robot
      keywords.robot
      syntax_error.robot
      resource.robot
      group_rf72.robot
```

## Client Extensibility

Editor clients live under `clients/` and adapt editor-specific APIs to the core LSP server.

```text
clients/
  vscode/
    docs/
```

Clients are responsible for:

- Starting the LSP process.
- Managing editor-specific language client integration.
- Mapping editor settings to `robot.lsp` server configuration.
- Providing editor UI such as commands, status, Test Explorer, and debug launch contributions.
- Packaging and release workflows for each editor.

The VS Code client follows its own Clean Architecture plan documented in `docs/specs/clients/vscode/clean-architecture.md`.

The core server under `src/robot_lsp/` must remain editor-agnostic.
