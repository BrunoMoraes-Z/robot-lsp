# Stage 13 — Configuration

## Status

done

## Goal

Add server configuration through initialization options and runtime changes, with safe defaults and integration into existing features.

## Scope

- `initializationOptions`
- `workspace/didChangeConfiguration`
- Internal configuration model
- Feature flag for diagnostics
- Additional import paths
- Configuration capabilities

## Out Of Scope

- Outbound `workspace/configuration` request
- Workspace-folder-specific configuration
- Configuration persistence
- Structured logging based on `logLevel`
- Configurable completion snippets in the LSP response

## Deliverables

- `src/robot_lsp/application/configuration.py`
- `workspace/didChangeConfiguration` handler
- `workspace.didChangeConfiguration` capability
- `diagnostics.enable` integration in the server
- `importPaths` integration in `WorkspaceIndex`
- Unit tests for service, handler, and import resolution

## Acceptance Criteria

- Defaults work without configuration
- `initializationOptions` applies initial configuration
- `workspace/didChangeConfiguration` updates configuration at runtime
- Diagnostics can be disabled
- Disabling diagnostics clears existing diagnostics for open documents
- `robot.lsp.importPaths` resolves `Resource` and `Variables` imports
- Invalid values are ignored without crashing

## Tests

- `test_default_config`
- `test_update_from_direct_settings`
- `test_update_from_nested_robot_lsp_settings`
- `test_invalid_values_keep_previous_config`
- `test_resolve_resource_import_from_configured_import_path`
- `test_initialize_applies_initialization_options`
- `test_did_change_configuration_updates_settings`
- `test_diagnostics_disabled_does_not_schedule_on_did_open`
- `test_disabling_diagnostics_clears_open_document_diagnostics`

## Risks

- `workspace/configuration` is not used yet because the server does not have an outbound request loop to the client.
- `completion.snippets` only changes section completions, which are the only current snippets.
- `importPaths` is global in the index, not workspace-folder-specific.

## Dependencies

- Stage 03
- Stage 05
- Stage 09

## Notes

- The accepted format is direct (`importPaths`) or nested (`robot.lsp` / `robot: { lsp: ... }`).
