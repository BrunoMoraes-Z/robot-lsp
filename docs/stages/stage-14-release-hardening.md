# Stage 14 — Release Hardening

## Status

done

## Goal

Prepare the MVP for real execution as a language server over stdio, with minimal documentation, CI, and final validation.

## Scope

- Real stdio runner
- Basic CLI
- Logging to stderr
- CI pipeline
- Usage documentation
- Initial changelog
- Updated compatibility matrix

## Out Of Scope

- Publishing to PyPI
- Real testing against every Robot Framework 7.x version
- Distributed tracing
- Advanced structured logs
- Complete subprocess integration tests

## Deliverables

- `src/robot_lsp/main.py` with LSP stdio loop
- `README.md`
- `docs/usage.md`
- `docs/changelog.md`
- `.github/workflows/ci.yml`
- Runner unit tests

## Acceptance Criteria

- `python -m robot_lsp --version` prints version
- Runner responds to a minimal `initialize`, `shutdown`, `exit` session
- Runner responds with JSON-RPC error for invalid messages
- Logs are sent to stderr
- CI runs pytest and compileall
- Usage documentation exists
- Initial changelog exists

## Tests

- `test_main_version`
- `test_run_lsp_loop_handles_minimal_session`
- `test_run_lsp_loop_returns_protocol_error_response`

## Risks

- Asynchronous diagnostics through the real process still need end-to-end subprocess testing.
- CI tests the resolved Robot Framework version, not a complete RF 7.x matrix.
- Publishing/distribution to PyPI has not been automated yet.

## Dependencies

- Stage 01
- Stage 02
- Stage 05
- Stage 13

## Notes

- The runner injects a publisher that writes diagnostics directly to the transport, avoiding reliance only on an in-memory queue.
- stdout is reserved exclusively for the LSP protocol.
