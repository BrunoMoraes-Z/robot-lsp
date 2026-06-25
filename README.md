# Robot LSP

Modern Language Server Protocol implementation for Robot Framework 7.x.

`robot-lsp` speaks JSON-RPC/LSP over stdio using standard `Content-Length` framing. It is designed as a small, testable language server with a clean separation between protocol, application services, Robot Framework parsing, and domain models.

## Highlights

- Native LSP server over stdio
- Robot Framework 7.0+ parser integration through `robot.api.parsing`
- Workspace-aware `.robot` and `.resource` indexing
- Diagnostics from Robot Framework parsing plus semantic checks
- Completion, hover, navigation, rename, formatting, and code actions
- Runtime configuration through initialization options and `workspace/configuration`
- RF 7.x feature support including `VAR`, `GROUP`, typed variables, and secret variables
- Cross-platform CI target coverage for Linux, Windows, macOS, and Python 3.10-3.13

## Requirements

- Python 3.10+
- Robot Framework 7.0+
- `uv` for local development

## Install For Development

```powershell
uv sync --extra dev
```

## Run

```powershell
uv run python -m robot_lsp
```

Useful CLI options:

```powershell
uv run python -m robot_lsp --version
uv run python -m robot_lsp --log-level debug
```

The server expects LSP messages on stdin and writes LSP messages to stdout.

## LSP Features

| Capability | LSP Method |
|---|---|
| Lifecycle | `initialize`, `initialized`, `shutdown`, `exit` |
| Full text sync | `textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose` |
| Diagnostics | `textDocument/publishDiagnostics` |
| Completion | `textDocument/completion` |
| Hover | `textDocument/hover` |
| Definition | `textDocument/definition` |
| References | `textDocument/references` |
| Document symbols | `textDocument/documentSymbol` |
| Folding ranges | `textDocument/foldingRange` |
| Selection ranges | `textDocument/selectionRange` |
| Prepare rename | `textDocument/prepareRename` |
| Rename | `textDocument/rename` |
| Formatting | `textDocument/formatting`, `textDocument/rangeFormatting` |
| Code actions | `textDocument/codeAction` |
| Configuration | `workspace/didChangeConfiguration`, outbound `workspace/configuration` |
| Cancellation | `$/cancelRequest` |
| Progress | `window/workDoneProgress/create`, `$/progress` |

## Robot Framework Support

### Syntax And Model

- Settings, variables, test cases, tasks, keywords, imports, metadata, tags, setup/teardown, templates, timeouts, arguments, and keyword calls
- `.robot` and `.resource` workspace indexing
- Library, resource, and variable imports
- Local and imported keyword/variable lookup
- UTF-16 position handling for LSP correctness

### Robot Framework 7.x Features

| Feature | Version | Support |
|---|---:|---|
| `VAR` syntax | 7.0 | Parsed in test/keyword bodies with value, kind, scope, and lexical visibility |
| `GROUP` syntax | 7.2 | Parsed, traversed for keyword calls, exposed in document symbols and folding ranges |
| Variable type conversion annotations | 7.3 | Parses `${name: type}`, validates built-in and importable dotted Python types, suggests types in completion |
| Secret variables | 7.4 | Supports `${name: Secret}` as secret variable type |

### Diagnostics

- Robot Framework parse errors
- Missing imports: `import_not_found`
- Unknown keywords: `keyword_not_found`
- Undefined variables: `variable_not_found`
- Unknown variable types: `unknown_variable_type`

Semantic diagnostics are intentionally conservative and run only when parsing succeeds.

### Completion

- Section headers, with optional snippets
- Settings names
- Local and imported keywords
- Local, scoped, and imported variables
- Robot Framework variable type annotations such as `int`, `str`, `bool`, `list`, `dict`, `Path`, `Decimal`, `Secret`, and `Any`

### Navigation And Refactoring

- Go to definition for local and imported symbols
- References in the current document
- Document symbols for imports, variables, test cases, keywords, and groups
- Folding ranges for sections, test cases, keywords, and groups
- Rename for supported local/workspace symbols

### Formatting And Code Actions

- Full document formatting
- Range formatting
- Basic quick fixes/code actions for supported diagnostics and style cases

## Configuration

Configuration can be provided through initialization options, `workspace/didChangeConfiguration`, or client-supported `workspace/configuration` requests.

Supported settings under `robot.lsp`:

| Setting | Type | Default |
|---|---|---|
| `diagnostics.enable` | boolean | `true` |
| `completion.snippets` | boolean | `true` |
| `logLevel` | `debug`, `info`, `warning`, `error` | `warning` |

Workspace-folder-specific configuration is supported when the client answers outbound `workspace/configuration` requests.

## Development

Run tests:

```powershell
uv run pytest
```

Compile-check source and tests:

```powershell
uv run python -m compileall src tests
```

If `just` is installed:

```powershell
just test
```

## Package Build

```powershell
uv sync --extra dev
uv build
```

See `docs/release.md` for release artifact validation.

## Project Layout

```text
src/robot_lsp/
  protocol/        JSON-RPC, LSP server, transport, dispatch
  application/     Completion, diagnostics, navigation, formatting, workspace services
  infrastructure/  Robot Framework parser adapter
  domain/          LSP and Robot Framework intermediate models
  adapters/        External entry adapters
```

## Documentation

- `docs/roadmap.md` - implementation stages and validation status
- `docs/architecture.md` - architecture overview
- `docs/specs/` - protocol, Robot Framework, workspace, performance, and testing specs
- `docs/decisions/` - ADRs
- `docs/release.md` - release/build notes

## Current Status

The MVP and post-MVP roadmap items are implemented and validated by the test suite. Current local validation: `202 passed`.
