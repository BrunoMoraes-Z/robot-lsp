# Stage 11 — Formatting & Code Actions

## Status

done

## Goal

Implement initial Robot Framework document formatting and basic code actions for known diagnostics.

## Scope

- `textDocument/formatting`
- `textDocument/rangeFormatting`
- `textDocument/codeAction`
- Initial normalization of spacing between cells
- Quick actions for known diagnostics

## Out Of Scope

- AST-based semantic formatting
- Automatic correction of parse errors
- Search for missing imports in the workspace
- `codeAction/resolve`
- Persistent style configuration

## Deliverables

- `src/robot_lsp/application/formatting_service.py`
- `src/robot_lsp/application/code_action_service.py`
- Handlers in `LspServer`
- Formatting and code action capabilities in `lsp_types.py`
- Unit tests for services and LSP handlers

## Acceptance Criteria

- `textDocument/formatting` returns `TextEdit` when there are changes
- `textDocument/formatting` returns an empty list when the document is already formatted
- `textDocument/rangeFormatting` formats full lines touched by the range
- `textDocument/codeAction` returns quick actions for known diagnostics
- `initialize` advertises formatting and code action capabilities
- Missing services result in empty responses, without errors

## Tests

- `test_format_robot_text_normalizes_cell_spacing`
- `test_format_document_returns_single_full_document_edit`
- `test_format_document_returns_no_edits_when_unchanged`
- `test_format_range_formats_whole_touched_lines`
- `test_parse_error_diagnostic_returns_quick_fix_action`
- `test_text_document_formatting`
- `test_text_document_range_formatting`
- `test_text_document_code_action`

## Risks

- Current formatting is textual and may not cover Robot Framework semantic nuances.
- Initial code actions are informational and do not yet apply automatic fixes.
- `FormattingOptions` does not yet change the produced style.

## Dependencies

- Stage 03
- Stage 04
- Stage 05

## Notes

- Stage completed with independent application services and LSP integration.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
