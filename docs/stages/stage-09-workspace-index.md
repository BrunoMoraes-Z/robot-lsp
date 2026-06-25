# Stage 09 — Workspace Index

## Status

done

## Goal

Index `.robot` and `.resource` workspace files to allow basic cross-file import, keyword, and variable resolution.

## Scope

- Index `.robot` and `.resource` files
- `WorkspaceEntry` with URI, path, suite, mtime, and content hash
- Search keywords and variables by name
- Basic import resolution for `Resource`, `Variables`, and `Library`
- Simple cache by mtime + content hash
- Optional integration with completion/navigation for symbols from imported resources

## Out Of Scope

- File watching through `workspace/didChangeWatchedFiles`
- Disk cache
- Asynchronous indexing/worker pool
- Full libspec for Python libraries
- Global references across the whole workspace

## Deliverables

- `src/robot_lsp/application/workspace.py`
- Unit tests for indexing, resolution, and integration with navigation/completion

## Acceptance Criteria

- `scan(root)` indexes `.robot` and `.resource`
- `find_keyword(name)` returns indexed keywords
- `find_variable(name)` returns indexed variables
- `resolve_import()` resolves `Resource` and `Variables` relative to the current file
- `resolve_import()` resolves standard Python/Robot libraries when possible
- `CompletionService` can include keywords/variables from imported resources
- `NavigationService.definition()` can point to a keyword/variable in an imported resource

## Tests

- `test_scan_indexes_robot_and_resource_files`
- `test_find_keyword_and_variable`
- `test_resolve_resource_import`
- `test_resolve_variables_import`
- `test_resolve_library_import`
- `test_imported_keyword_locations`
- `test_imported_variable_locations`
- `test_update_file_reuses_cache_when_unchanged`
- `test_completion_includes_imported_resource_keyword`
- `test_definition_points_to_imported_resource_keyword`

## Risks

- Library resolution still does not replace full libdoc/libspec support.
- Synchronous indexing can become heavy in large workspaces; Stage 12 will address performance/isolation.

## Dependencies

- Stage 04
- Stage 06
- Stage 08

## Notes

- Stage completed with local synchronous indexing and in-memory cache.
- `Library` resolution uses `importlib.util.find_spec()` and falls back to `robot.libraries.<name>`.
- Initial cross-file resolution covers imported resources, which is sufficient for the Stage 10+ foundation.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
