# Stage 05 — Diagnostics

## Status

done

## Goal

Implement diagnostic generation from Robot Framework parsing and publication through `textDocument/publishDiagnostics`.

## Scope

- Collect syntax errors from the RF parser
- Map errors to `LspDiagnostic` with severity, message, and range
- Convert RF ranges (1-based) to LSP ranges (0-based UTF-16)
- `textDocument/publishDiagnostics`: send diagnostics to the client
- `DiagnosticService`: orchestrate:
- Document parsing
- Diagnostic collection
- Debounce (300 ms) to avoid flooding
- Cancel pending diagnostics by URI when a new didChange arrives
- Publish only if there was a change
- Fallback: when RF does not provide a range, use the whole line

## Out Of Scope

- Semantic analysis (robocop, best-practice rules)
- Code actions

## Deliverables

- `src/robot_lsp/application/diagnostic_service.py`
- `src/robot_lsp/domain/diagnostics.py`
- Integration with `LspServer` to publish diagnostics

## Acceptance Criteria

- Invalid document triggers `publishDiagnostics` with at least 1 diagnostic
- Fixed document clears diagnostics (empty array)
- Debounce avoids publications on every typed character
- Cancelled diagnostics (superseded) are not published
- Diagnostic range covers the error region (or falls back to the line)
- Correct severity: error for parse error

## Tests

- `test_diagnostic_from_parse_error`
- `test_diagnostic_cleared_on_fix`
- `test_diagnostic_debounce`
- `test_diagnostic_cancel`
- `test_diagnostic_range_conversion`
- `test_diagnostic_fallback_range`

## Risks

- RF may not report exact positions for all errors
- Debounce may delay feedback; use 300 ms as the default

## Dependencies

- Stage 04 (RF model)

## Notes

- Stage completed with `ParseService`, `DiagnosticService`, and optional integration with `LspServer`.
- Post-MVP semantic diagnostics now cover missing imports, unknown keywords, and undefined variables.
- The server keeps outgoing notifications in `outgoing_notifications` until the full transport loop exists.
- `didOpen` and `didChange` schedule diagnostics; `didClose` clears diagnostics.
- `DiagnosticService.flush(uri)` was added for deterministic tests and controlled usage.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
