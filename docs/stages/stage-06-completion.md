# Stage 06 — Completion

## Status

done

## Goal

Implement code completion for `.robot` files: sections, settings, local keywords, and local variables.

## Scope

- `textDocument/completion` handler
- `CompletionContext`: cursor position, document, parsed model
- Providers:
- **SectionProvider**: completes `*** Settings ***`, `*** Variables ***`, `*** Test Cases ***`, `*** Keywords ***`
- **SettingProvider**: completes `Library`, `Resource`, `Variables`, `Documentation`, `Metadata`, `Suite Setup`, `Suite Teardown`, `Test Setup`, `Test Teardown`, `Test Tags`, `Test Template`, `Test Timeout`, `Force Tags`, `Default Tags`
- **LocalKeywordProvider**: completes keyword names defined in the same file
- **LocalVariableProvider**: completes variable names defined in the same file ($, @, &, %)
- `CompletionItem` with label, kind, detail, documentation, textEdit, data
- Trigger characters: space (for settings) and `$`, `@`, `&`, `%` (for variables)
- `isIncomplete`: false in the MVP

## Out Of Scope

- Completion for imported libraries (Stage 09)
- Auto-import
- `completionItem/resolve`
- Full snippets

## Deliverables

- `src/robot_lsp/application/completion_service.py`
- Providers in internal modules
- Tests for each provider

## Acceptance Criteria

- On an empty line at the start of the file: completes sections
- In `*** Settings ***`: completes known settings
- In `*** Keywords ***`: completes keywords defined in the same file
- In a keyword call: completes keyword names
- In a variable context: completes variables from the file
- `CompletionItem` has `label`, `kind`, and `detail` populated

## Tests

- `test_completion_sections`
- `test_completion_settings`
- `test_completion_local_keyword`
- `test_completion_local_variable`
- `test_completion_trigger_characters`
- `test_completion_empty_result`

## Risks

- Incorrect context detection (keyword call vs setting value) requires line analysis
- Trigger characters may cause unexpected completions

## Dependencies

- Stage 04 (RF model)

## Notes

- Stage completed with initial completion for sections, settings, local keywords, and local variables.
- `textDocument/completion` was integrated into `LspServer` as an LSP request.
- The service uses `DocumentStore` + `ParseService`, without a direct Robot Framework dependency.
- Completion does not yet resolve imported libraries/resources; that remains for Stage 09.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
