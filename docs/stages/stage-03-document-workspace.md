# Stage 03 — Document & Workspace

## Status

done

## Goal

Implement document synchronization (didOpen, didChange, didClose) and workspace management.

## Scope

- `textDocument/didOpen`: receive document, store it, start tracking
- `textDocument/didChange` (Full sync): replace full content
- `textDocument/didClose`: remove document from tracking
- `DocumentStore`: repository for open documents
- `Document`: URI, path, text, version, languageId
- URI helpers: `file://` -> path, path -> `file://`
- LSP position conversion:
- Line: 0-based
- Character: 0-based UTF-16 code units
- Range operations: calculate text for a range, split by lines

## Out Of Scope

- Incremental sync (deferred)
- Diagnostics (Stage 05)
- Dynamic workspace folders (deferred to Stage 13)

## Deliverables

- `src/robot_lsp/domain/positions.py` (LspPosition, LspRange, UTF-16 calculations)
- `src/robot_lsp/application/document_store.py` (DocumentStore, Document)
- Unit tests for positions, conversions, and store

## Acceptance Criteria

- `didOpen` adds document to `DocumentStore`
- `didChange` with `textDocumentSyncKind.Full` replaces content and increments version
- `didClose` removes document
- URI `file:///c:/projects/test.robot` maps to the correct path
- UTF-16 conversion works for strings with emoji (2 code units) and accented characters (1 code unit)
- `LspRange` correctly calculates text for a range

## Tests

- `test_did_open`
- `test_did_change_full`
- `test_did_close`
- `test_document_version`
- `test_uri_to_path`
- `test_path_to_uri`
- `test_lsp_position_utf16_ascii`
- `test_lsp_position_utf16_accent`
- `test_lsp_position_utf16_emoji`
- `test_range_text_extraction`

## Risks

- Incorrect UTF-16 conversion causes position bugs across all LSP features
- URIs with percent encoding must be decoded

## Dependencies

- Stage 02

## Notes

- Stage completed with `DocumentStore`, `Document`, URI helpers, UTF-16 conversion, and document sync LSP handlers.
- `didChange` uses full sync according to ADR-0005 and synchronization specs.
- `position_to_utf16_offset` handles empty text, accented characters, and emoji (2 UTF-16 code units).
- Validation executed with `just test` and `uv run python -m compileall src tests`.
