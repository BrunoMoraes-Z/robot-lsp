# Diagnostics

## Stage

Stage 05 — Diagnostics

## LSP Methods

- `textDocument/publishDiagnostics` (server -> client notification)

## Initial Scope

- Parse/syntax diagnostics from Robot Framework
- Semantic diagnostics for missing imports, unknown keywords, and undefined variables
- 300 ms debounce
- Pending diagnostic cancellation by URI
- Error range when available; fallback to the whole line

## Implementation

### LspDiagnostic

```python
@dataclass
class LspDiagnostic:
    range: LspRange
    severity: DiagnosticSeverity
    message: str
    source: str = "robot-lsp"
    code: str | None = None
```

### DiagnosticService

```python
class DiagnosticService:
    _parse_service: ParseService
    _debounce_timers: dict[str, threading.Timer]
    _last_diagnostics: dict[str, list[LspDiagnostic]]
    DEBOUNCE_SECONDS = 0.3

    def schedule_diagnostics(uri: str) -> None
    def _compute_and_publish(uri: str) -> None
    def cancel_pending(uri: str) -> None
```

### Flow

1. `didChange` → `schedule_diagnostics(uri)`
2. If a timer already exists for uri, cancel it
3. Schedule a new timer for `DEBOUNCE_SECONDS`
4. Timer runs: parse + collect diagnostics + publish
5. Publication through `server.publish_diagnostics(uri, diagnostics)`
6. If diagnostics are identical to the last published diagnostics, do not publish

### RF Range Conversion

- Robot Framework: 1-based line/column
- LSP: 0-based line, 0-based UTF-16 column
- If RF does not provide column, use column 0
- If RF does not provide end line/col, use start line/col (point diagnostic)

## Future Scope

- Integration with robocop or external linter
- Diagnostic tags (unnecessary, deprecated)
- Additional semantic rules such as argument ordering and template validation

## Tests

- Parse error -> diagnostic published
- Fix -> diagnostics cleared
- Debounce -> does not publish if timer has not expired yet
- Cancellation -> old timer does not publish
- Range 1-based → 0-based
- Missing import -> `import_not_found`
- Missing keyword -> `keyword_not_found`
- Missing variable -> `variable_not_found`
