# Stage 12 — Performance & Isolation

## Status

done

## Goal

Reduce repeated work in common requests and record isolation decisions before adding concurrency or subprocesses.

## Scope

- Parse cache for open documents
- Invalidation by URI, version, and text hash
- Configurable LRU limit
- Review of the existing workspace cache
- Explicit decision about worker pool and subprocess isolation

## Out Of Scope

- Moving existing LSP handlers to worker execution without metrics
- Subprocess for indexing
- Persistent disk cache
- Detailed telemetry or profiling

## Deliverables

- LRU cache in `src/robot_lsp/application/parse_service.py`
- Optional worker execution support in `src/robot_lsp/protocol/dispatch.py`
- Unit tests for cache and invalidation
- Performance spec updates

## Acceptance Criteria

- Unchanged document reuses the same `ParseResult`
- Text changes trigger a new parse
- Version changes trigger a new parse
- Cache respects the configurable LRU limit
- Cache can be cleared by URI
- Workspace index keeps cache by mtime + hash
- Dispatcher can run explicitly registered methods in a worker pool and suppress cancelled responses
- Subprocess isolation remains documented as a future metrics-based decision

## Tests

- `test_parse_document_reuses_cached_result_for_unchanged_document`
- `test_parse_document_invalidates_cache_when_text_changes`
- `test_parse_document_invalidates_cache_when_version_changes`
- `test_parse_cache_evicts_least_recently_used_entry`
- `test_clear_uri_removes_cached_entry`
- `test_update_file_reuses_cache_when_unchanged`
- `test_worker_request_can_be_canceled_while_running`

## Risks

- The cache stores `ParseResult` in memory and may retain large document models until eviction.
- Existing LSP handlers remain synchronous until a measured hot path justifies opt-in worker execution.
- There is no disk cache; large workspaces still depend on in-memory cache.

## Dependencies

- Stage 03
- Stage 04
- Stage 09

## Notes

- The optimization was applied in `ParseService`, so diagnostics, completion, hover, navigation, and refactoring benefit without local changes.
- Worker pool infrastructure exists in `MethodDispatcher`, but current LSP handlers are not moved to it to avoid premature thread-safety complexity.
- Subprocesses remain postponed until metrics justify them.
