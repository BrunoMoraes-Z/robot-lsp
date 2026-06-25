# Roadmap

## Current Stage

**MVP Complete**
Status: `done`

## Verification Summary

All 14 stages planned for the MVP have been implemented and validated by the current test suite.

Most recent local validation:
- `uv run pytest` — 202 tests passing

The items below do not block the MVP, but remain pending for post-MVP evolution because they were explicitly deferred in stage/spec documents or belong to release hardening beyond the first functional version.

## Post-MVP Pending Roadmap

| Order | Item | Source | Status |
|---|---|---|---|
| 01 | Run the real Robot Framework 7.x compatibility matrix, not only the installed version | Stage 14 / compatibility matrix | done |
| 02 | Automate release publishing/distribution, including build artifacts and PyPI if applicable | Stage 14 | done |
| 03 | Implement structured logging applied to `robot.lsp.logLevel` at runtime | Stage 13 / Stage 14 | done |
| 04 | Apply `robot.lsp.completion.snippets` to completion items and configurable snippets | Stage 13 | done |
| 05 | Implement outbound `workspace/configuration` request and workspace-folder-specific configuration | Stage 13 / workspace configuration spec | done |
| 06 | Add worker pool/real cancellation for long-running operations when metrics justify it | Stage 12 / performance specs | done |
| 07 | Evaluate subprocess isolation for indexing/heavy analysis with dedicated integration tests | Stage 12 / Stage 14 risks | done |
| 08 | Add progress reporting (`$/progress`, `window/workDoneProgress/create`) for long-running operations | protocol progress spec | done |
| 09 | Expand CI to new targets when needed, such as macOS and Python 3.13 | compatibility matrix | done |
| 10 | Implement semantic diagnostics/warnings beyond Robot Framework parse errors | diagnostics rules spec | done |

---

## Stage Status

| Stage | Name | Status |
|---|---|---|
| 00 | Foundation | done |
| 01 | JSON-RPC | done |
| 02 | LSP Lifecycle | done |
| 03 | Document Workspace | done |
| 04 | Robot Framework Model | done |
| 05 | Diagnostics | done |
| 06 | Completion | done |
| 07 | Hover | done |
| 08 | Navigation | done |
| 09 | Workspace Index | done |
| 10 | Refactoring | done |
| 11 | Formatting & Code Actions | done |
| 12 | Performance & Isolation | done |
| 13 | Configuration | done |
| 14 | Release Hardening | done |

---

## Stage Details

### Stage 00 — Foundation

**Expected**
- Create project with `uv`
- Define package structure (Clean Architecture)
- Create `justfile` with PowerShell
- Create initial directory architecture
- Create base documentation (`docs/`, ADRs, stages, specs)
- Configure `pytest`
- Empty `python -m robot_lsp` entrypoint

**Done**
- Project created with `uv`
- Clean Architecture directory structure established
- `pyproject.toml` configured with dependencies and build system
- Working `justfile` with PowerShell
- Complete `docs/`: roadmap, architecture, ADRs, stages (00-07), specs (protocol, text-document, RF, testing, performance)
- Working `python -m robot_lsp` entrypoint
- Import test for all modules passing
- `pytest` configured
- `.gitignore` created

**Acceptance Criteria**
- ✅ `uv run pytest` runs and passes
- ✅ `just test` runs and passes
- ✅ `src/robot_lsp/` structure exists with `domain/`, `application/`, `infrastructure/`, `protocol/`, `adapters/` layers
- ✅ `tests/` structure exists with `unit/` and `integration/`
- ✅ `python -m robot_lsp` runs without error
- ✅ `docs/` is populated with roadmap, architecture, ADRs, stages, and specs
- ✅ `just test` runs `uv run pytest`
- ✅ `uv run python -m robot_lsp` prints info to stderr

---

### Stage 01 — JSON-RPC

**Expected**
- Implement JSON-RPC 2.0: request, response, notification, error
- Implement LSP framing (`Content-Length`)
- Implement reader/writer over `stdio`
- Implement method dispatch
- Support `$/cancelRequest`
- Unit tests for framing and messages

**Done**
- Implemented JSON-RPC 2.0 parser/serializer in `src/robot_lsp/protocol/jsonrpc.py`
- Implemented `JsonRpcMessage`, `JsonRpcError`, and `JsonRpcProtocolError` protocol error models
- Implemented helpers for request, notification, response, and error response
- Implemented standard JSON-RPC error codes and initial internal LSP codes
- Implemented LSP `Content-Length` framing in `src/robot_lsp/protocol/transport_stdio.py`
- Implemented binary reader/writer with thread-safe writes
- Implemented `MethodDispatcher` in `src/robot_lsp/protocol/dispatch.py`
- Implemented cooperative cancellation through `$/cancelRequest`
- Created unit tests for JSON-RPC, transport, and dispatcher

**Acceptance Criteria**
- ✅ Requests, notifications, and responses serialize/deserialize correctly
- ✅ Standard JSON-RPC errors are emitted for invalid messages
- ✅ `Content-Length` header is read/written correctly
- ✅ Messages larger than the buffer are read correctly
- ✅ Request cancellation works

---

### Stage 02 — LSP Lifecycle

**Expected**
- `initialize`
- `initialized`
- `shutdown`
- `exit`
- Server states (uninitialized, running, shuttingDown, exited)
- Minimal capabilities (textDocumentSync, completionProvider, hoverProvider)
- Minimal LSP session tests through in-memory transport

**Done**
- Implemented `LspServer` in `src/robot_lsp/protocol/server.py`
- Implemented states `uninitialized`, `running`, `shuttingDown`, `exited`
- Implemented `initialize`, `initialized`, `shutdown`, `exit` handlers
- Implemented validation for messages before `initialize` with error `-32002`
- Implemented validation for requests after `shutdown` with error `-32003`
- Implemented `serverInfo` with server name and version
- Implemented initial capabilities in `src/robot_lsp/protocol/lsp_types.py`
- Created lifecycle unit tests in `tests/unit/protocol/test_server.py`

**Acceptance Criteria**
- ✅ Server responds to `initialize` with correct capabilities
- ✅ `initialized` is accepted as a notification
- ✅ `shutdown` + `exit` terminates the server
- ✅ Messages before `initialize` are rejected
- ✅ Messages after `shutdown` are rejected

---

### Stage 03 — Document & Workspace

**Expected**
- `textDocument/didOpen`
- `textDocument/didChange` (sync full)
- `textDocument/didClose`
- `DocumentStore`: manages open documents
- URI/path helpers
- LSP position conversion (UTF-16 code units)
- Ranges: 0-based line, 0-based UTF-16 column

**Done**
- Fixed and completed `DocumentStore` in `src/robot_lsp/application/document_store.py`
- Implemented `Document` with `lines` and text extraction by `LspRange`
- Implemented `uri_to_path` and `path_to_uri` helpers
- Improved UTF-16 conversion in `src/robot_lsp/domain/positions.py`
- Implemented `range_text` for extraction by LSP ranges
- Implemented `textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose` handlers in `LspServer`
- Created tests for `DocumentStore`, URI/path, UTF-16 positions, and document sync

**Acceptance Criteria**
- ✅ Document opened through `didOpen` becomes available in `DocumentStore`
- ✅ `didChange` with full text replaces content
- ✅ `didClose` removes document
- ✅ UTF-16 conversions work with multibyte characters (accents, emoji)
- ✅ `file://` URI is converted to system path
- ✅ `LspRange` calculates range text correctly

---

### Stage 04 — Robot Framework Model

**Expected**
- Robot Framework version detector (`robot.version.VERSION`)
- `FeatureSet` with version-based capabilities
- Parser using only `robot.api.parsing`
- Custom intermediate model (decoupled from the RF AST)
- Adapter that maps the RF AST to the intermediate model
- `.robot` fixtures for tests

**Done**
- Implemented missing intermediate models: `RobotDocument`, `RobotDiagnostic`, `ParseResult`
- Implemented version detector in `src/robot_lsp/infrastructure/robotframework/version.py`
- Implemented `FeatureSet` for RF >= 7.0 with `has_group` and `has_secret_variables` flags
- Implemented parser in `src/robot_lsp/infrastructure/robotframework/parser.py` using only `robot.api.parsing`
- Implemented AST adapter in `src/robot_lsp/infrastructure/robotframework/adapter.py`
- Implemented error collection visitor in `visitors.py`
- Extracted settings, metadata, imports, variables, test cases, keywords, args, and steps
- Created real `.robot` and `.resource` fixtures in `tests/integration/fixtures/`
- Created tests for versioning, parser, adapter, and RF import isolation

**Acceptance Criteria**
- ✅ Version 7.0+ is detected and reported correctly
- ✅ `FeatureSet` reflects the installed version
- ✅ `.robot` suite is parsed to the intermediate model
- ✅ LSP core never imports `robot.api.parsing` or `robot.parsing` directly
- ✅ RF parse errors are captured without crashing
- ✅ Tests with real `.robot` fixtures

---

### Stage 05 — Diagnostics

**Expected**
- Parse/syntax diagnostics through Robot Framework
- `textDocument/publishDiagnostics` notification
- Diagnostics debounce (for example, 300 ms)
- Pending diagnostic cancellation by URI
- RF range conversion (1-based) -> LSP (0-based)
- Fallback to the whole line when range is unavailable

**Done**
- Implemented `ParseService` in `src/robot_lsp/application/parse_service.py`
- Implemented `DiagnosticService` in `src/robot_lsp/application/diagnostic_service.py`
- Implemented LSP serialization for `LspDiagnostic` in `domain/diagnostics.py`
- Integrated `DiagnosticService` into `LspServer` through optional injection
- Implemented `textDocument/publishDiagnostics` as an outgoing notification
- `didOpen` and `didChange` schedule diagnostics with debounce
- `didClose` clears diagnostics and cancels pending timers
- Implemented pending diagnostic cancellation by URI
- Implemented deduplication to avoid publishing identical diagnostics
- Created unit tests for parse diagnostics, clear, debounce, cancel, publication, and ranges

**Acceptance Criteria**
- ✅ Invalid document triggers `publishDiagnostics`
- ✅ Fixed document clears diagnostics
- ✅ Debounce avoids flooding during fast typing
- ✅ Cancelled diagnostics are not published
- ✅ Parsing does not break the server on severe error
- ✅ Correct severity: error for parse error

---

### Stage 06 — Completion

**Expected**
- Complete sections (`*** Settings ***`, etc.)
- Complete settings (`Library`, `Resource`, `Suite Setup`, etc.)
- Complete local keywords (same file)
- Complete local variables
- Simple `InsertTextFormat.PlainText` and `Snippet`

**Done**
- Implemented `CompletionService` in `src/robot_lsp/application/completion_service.py`
- Implemented `CompletionItem`, `CompletionList`, `CompletionContext`, and `CompletionItemKind` types
- Implemented section completion
- Implemented settings completion in `*** Settings ***`
- Implemented local keyword completion in test case/keyword bodies
- Implemented local variable completion with `$`, `@`, `&`, `%` triggers
- Integrated `textDocument/completion` handler into `LspServer`
- Created unit tests for service and LSP handler

**Acceptance Criteria**
- ✅ Cursor after an empty line completes sections
- ✅ Cursor in `*** Settings ***` completes known settings
- ✅ Cursor in `*** Keywords ***` completes file keywords
- ✅ Cursor where a variable is expected completes file variables
- ✅ Completion items have label, kind, detail, and documentation when applicable

---

### Stage 07 — Hover

**Expected**
- Hover on local keyword (shows docstring/args)
- Hover on local variable (shows type and value)
- Hover on import (shows import type)
- Markdown formatting
- Range of the symbol under the cursor

**Done**
- Implemented `HoverService` in `src/robot_lsp/application/hover_service.py`
- Implemented `MarkupContent`, `Hover`, and `HoverContext` types
- Implemented hover for local keywords with signature, arguments, and documentation
- Implemented hover for local variables with type and value
- Implemented hover for imports with type, name, alias, and arguments
- Integrated `textDocument/hover` handler into `LspServer`
- Created unit tests for service and LSP handler

**Acceptance Criteria**
- ✅ Hover on local keyword returns signature and documentation
- ✅ Hover on variable returns type and value
- ✅ Hover on import returns type and path
- ✅ Response respects `MarkupKind.Markdown`
- ✅ `null`/`None` if nothing is found for hover
- ✅ Hover range covers the symbol under the cursor

---

### Stage 08 — Navigation

**Expected**
- `textDocument/definition`
- `textDocument/references`
- `textDocument/documentSymbol`
- `textDocument/foldingRange`
- `textDocument/selectionRange`

**Done**
- Implemented `NavigationService` in `src/robot_lsp/application/navigation_service.py`
- Implemented `textDocument/definition` for local symbols
- Implemented `textDocument/references` with `includeDeclaration` support
- Implemented `textDocument/documentSymbol` for imports, variables, test cases, and keywords
- Implemented `textDocument/foldingRange` for sections, test cases, and keywords
- Implemented `textDocument/selectionRange` with symbol range and line parent
- Integrated navigation capabilities in `initialize`
- Created unit tests for service and LSP handlers

**Acceptance Criteria**
- ✅ `definition` returns local locations
- ✅ `references` returns local occurrences and respects `includeDeclaration`
- ✅ `documentSymbol` returns document structure
- ✅ `foldingRange` returns foldable ranges
- ✅ `selectionRange` returns ranges by position
- ✅ Handlers return empty lists when service/document does not exist

---

### Stage 09 — Workspace Index

**Expected**
- Index `.robot` and `.resource` files in the workspace
- Import resolution (`Library`, `Resource`, `Variables`)
- Keywords from imported libraries
- Variables from imported resources
- Workspace cache

**Done**
- Implemented `WorkspaceIndex` in `src/robot_lsp/application/workspace.py`
- Implemented `WorkspaceEntry`, `SymbolLocation`, and `ImportResolution`
- Implemented scanning for `.robot` and `.resource` files
- Implemented `find_keyword` and `find_variable` searches
- Implemented basic `Resource`, `Variables`, and `Library` import resolution
- Implemented simple cache by mtime + content hash
- Optionally integrated `WorkspaceIndex` into `CompletionService`
- Optionally integrated `WorkspaceIndex` into `NavigationService`
- Created tests for indexing, resolution, and cross-file integration through resources

**Acceptance Criteria**
- ✅ Indexing of `.robot` and `.resource` files
- ✅ Basic import resolution for `Library`, `Resource`, `Variables`
- ✅ Keywords from imported resources are available for completion/definition
- ✅ Variables from imported resources are available for completion
- ✅ In-memory cache by mtime + content hash

---

### Stage 10 — Refactoring

**Expected**
- `textDocument/rename`
- `textDocument/prepareRename`
- `workspace/workspaceEdit`

**Done**
- Implemented `RefactoringService` in `src/robot_lsp/application/refactoring_service.py`
- Implemented `textDocument/prepareRename`
- Implemented `textDocument/rename`
- Implemented `WorkspaceEdit` with `changes`
- Implemented local rename for variables, keywords, and test cases
- Implemented textual rename in indexed files when `WorkspaceIndex` is available
- Added `renameProvider` capability with `prepareProvider: true`
- Created unit tests for service and LSP handlers

**Acceptance Criteria**
- ✅ `prepareRename` returns range and placeholder
- ✅ `prepareRename` returns `null` for unknown symbol
- ✅ `rename` returns `WorkspaceEdit`
- ✅ Local rename changes occurrences in the open document
- ✅ Rename with `WorkspaceIndex` includes indexed files
- ✅ Handler returns `null` when service is not configured

---

### Stage 11 — Formatting & Code Actions

**Expected**
- `textDocument/formatting`
- `textDocument/rangeFormatting`
- `textDocument/codeAction`
- Quick fixes for common diagnostics

**Done**
- Implemented `FormattingService` in `src/robot_lsp/application/formatting_service.py`
- Implemented `textDocument/formatting`
- Implemented `textDocument/rangeFormatting`
- Implemented initial spacing normalization between cells to 4 spaces
- Implemented trailing whitespace removal per line
- Implemented `CodeActionService` in `src/robot_lsp/application/code_action_service.py`
- Implemented `textDocument/codeAction`
- Added `documentFormattingProvider`, `documentRangeFormattingProvider`, and `codeActionProvider` capabilities
- Created unit tests for services and LSP handlers

**Acceptance Criteria**
- ✅ `textDocument/formatting` returns a whole-document `TextEdit` when there are changes
- ✅ `textDocument/formatting` returns an empty list when the document is already formatted
- ✅ `textDocument/rangeFormatting` formats lines touched by the range
- ✅ `textDocument/codeAction` returns quick actions for known diagnostics
- ✅ Formatting and code action capabilities are advertised in `initialize`
- ✅ Handlers return an empty list when services are not configured

---

### Stage 12 — Performance & Isolation

**Expected**
- AST parse cache
- Workspace analysis cache
- Real cancellation for long requests
- Worker pool for heavy operations
- Isolated subprocess for indexing (if needed)

**Done**
- Implemented LRU parse cache in `ParseService`
- Parse cache uses URI, document version, and SHA-256 text hash
- Cache is reused by diagnostics, completion, hover, navigation, and refactoring through `ParseService`
- Added `clear_uri` and `clear` methods for explicit invalidation
- Added configurable `max_cache_entries` limit, default 50
- Kept the existing workspace cache by mtime + content hash
- Worker pool and subprocess remain outside the MVP until metrics justify the complexity

**Acceptance Criteria**
- ✅ Unchanged document is not parsed again
- ✅ Text change invalidates cache
- ✅ Version change invalidates cache
- ✅ Cache respects configurable LRU limit
- ✅ Cache can be invalidated by URI
- ✅ Workspace index keeps cache by mtime + hash
- ✅ Subprocess isolation documented as future work, not needed in the current MVP

---

### Stage 13 — Configuration

**Expected**
- `workspace/configuration`
- LSP settings (feature flags, import paths)
- Workspace-folder-specific configuration
- `didChangeConfiguration`

**Done**
- Implemented `ConfigurationService` in `src/robot_lsp/application/configuration.py`
- Implemented `ServerConfig` model with `importPaths`, `logLevel`, `diagnostics.enable`, and `completion.snippets`
- Implemented `initializationOptions` support
- Implemented `workspace/didChangeConfiguration` handler
- Added `workspace.didChangeConfiguration` capability
- Integrated `diagnostics.enable` into diagnostic scheduling
- Disabling diagnostics clears published diagnostics from open documents
- Integrated `robot.lsp.importPaths` into file import resolution in `WorkspaceIndex`
- Created unit tests for config service, LSP handler, and import paths

**Acceptance Criteria**
- ✅ Defaults work without configuration
- ✅ `initializationOptions` applies initial settings
- ✅ `workspace/didChangeConfiguration` updates settings at runtime
- ✅ Diagnostics can be disabled through configuration
- ✅ Disabling diagnostics clears existing diagnostics
- ✅ `robot.lsp.importPaths` participates in `Resource` and `Variables` resolution
- ✅ Invalid values are ignored without breaking existing configuration
- ✅ `workspace/configuration` is requested from clients that advertise `workspace.configuration`
- ✅ Workspace-folder-specific `diagnostics.enable` and `completion.snippets` are applied by document URI

---

### Stage 14 — Release Hardening

**Expected**
- RF 7.x compatibility matrix
- CI pipeline
- Packaging and distribution
- Structured logging
- Tracing for diagnostics
- Usage documentation
- Changelog

**Done**
- Implemented real stdio runner in `src/robot_lsp/main.py`
- Implemented `create_server()` factory with all MVP services connected
- Implemented `--version`
- Implemented `--log-level` with logs on stderr
- Protocol errors in the stdio loop return JSON-RPC error responses
- Pending notifications are drained by the runner
- Asynchronous diagnostics can publish directly to the runner transport
- Added CI workflow in `.github/workflows/ci.yml`
- Added `README.md`
- Added `docs/usage.md`
- Added `docs/changelog.md`
- Updated compatibility matrix with targets and local validation

**Acceptance Criteria**
- ✅ `python -m robot_lsp --version` returns version
- ✅ Stdio runner responds to minimal LSP session
- ✅ Stdio runner returns JSON-RPC error for invalid message
- ✅ Logs use stderr, preserving stdout for LSP
- ✅ CI pipeline documented in GitHub Actions
- ✅ Usage documentation and initial changelog exist
- ✅ Tests and compileall pass
