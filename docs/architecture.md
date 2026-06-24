# Architecture

## Overview

Clean Architecture com separação explícita em camadas. O fluxo de dados sempre aponta para o centro: protocolo → aplicação → domínio, com a infraestrutura sendo injetada nas bordas.

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
- Pure Python com `dataclasses` e tipos padrão.
- Sem dependências externas (nem Robot Framework, nem LSP, nem JSON-RPC).
- Modelos intermediários do LSP: `LspRange`, `LspPosition`, `LspDiagnostic`.
- Modelos intermediários do Robot: `RobotSuite`, `RobotTestCase`, `RobotKeyword`, `RobotVariable`, `RobotStep`, `RobotImport`, `RobotSettings`, `RobotArg`.
- `FeatureSet`: informação da versão do Robot Framework e capacidades ativas.

### Application Layer (`src/robot_lsp/application/`)
- Casos de uso do LSP.
- Depende apenas de `domain/`.
- `DocumentStore`: gerencia documentos abertos.
- `Workspace`: gerencia arquivos do workspace.
- `ParseService`: coordena parse via infraestrutura.
- `DiagnosticService`: coordena geração e publicação de diagnostics.
- `CompletionService`: coordena completion.
- `HoverService`: coordena hover.

### Protocol Layer (`src/robot_lsp/protocol/`)
- JSON-RPC 2.0 puro.
- LSP framing sobre `stdio`.
- `Endpoint`: roteamento de requests/notifications.
- `Dispatch`: mapeamento de método LSP para handler.
- `Server`: estado do servidor LSP e handlers de lifecycle.
- Depende de `application/` e `domain/`.

### Infrastructure Layer (`src/robot_lsp/infrastructure/`)
- Implementações concretas: parser do Robot Framework, adapter AST.
- Única camada que importa `robotframework`.
- `robotframework/version.py`: detector de versão.
- `robotframework/parser.py`: parse via `robot.api.parsing`.
- `robotframework/adapter.py`: mapeia AST RF → modelo intermediário.
- `robotframework/visitors.py`: visitors para extrair informações do AST.

## Dependency Rule

- Camadas externas dependem de camadas internas.
- `domain/` não depende de ninguém.
- `application/` depende só de `domain/`.
- `protocol/` depende de `application/` e `domain/`.
- `infrastructure/` depende de `domain/` (retorna modelos).
- Nenhuma camada externa conhece implementação interna de outra camada externa.

## Project Layout

```
src/robot_lsp/
  __init__.py
  __main__.py          # python -m robot_lsp
  main.py               # bootstrap, DI, startup

  domain/
    __init__.py
    models.py           # RobotSuite, RobotTestCase, RobotKeyword, etc.
    positions.py        # LspPosition, LspRange, conversão
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
      visitors.py       # AST visitors especializados

  protocol/
    __init__.py
    jsonrpc.py          # JsonRpcMessage, encode/decode
    transport_stdio.py  # TransportStdio (Content-Length reader/writer)
    endpoint.py         # Endpoint (dispatch/cancelamento)
    dispatch.py         # MethodDispatcher
    lsp_types.py        # Lsp types auxiliares
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

## Extensibilidade Futura

Extensões IDE (VS Code, Neovim, etc.) serão adaptadores que:
- Disparam o processo LSP.
- Gerenciam transporte `stdio` ou TCP.
- Mapeiam recursos IDE para o protocolo LSP.

Os adaptadores ficarão em um pacote separado (`robot_lsp_ide_vscode`, etc.) sem modificar o core.
