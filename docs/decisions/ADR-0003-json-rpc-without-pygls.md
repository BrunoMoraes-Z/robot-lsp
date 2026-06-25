# ADR-0003 — JSON-RPC Without pygls

## Status

accepted

## Context

We need to decide how to implement the LSP protocol. The options are to use pygls (a Python LSP library) or implement our own JSON-RPC and transport.

## Decision

Implement JSON-RPC 2.0 and LSP transport (`Content-Length` framing over `stdio`) as custom code, without using `pygls`, `python-lsp-server`, or `robocorp_ls_core`.

## Consequences

### Positive
- Full control of the protocol lifecycle.
- No coupling to third-party versions.
- Possibility for specific optimizations (cancellation, tracing, performance).
- Minimal, lean code for what we actually need.

### Negative
- More code to maintain.
- Responsibility for compatibility with the LSP specification.
- Protocol edge cases must be implemented correctly.

## Alternatives Considered

- pygls: abstracts JSON-RPC and LSP, but hides implementation details and adds a heavy dependency.
- python-lsp-server: focused on Python and does not fit Robot Framework well.
- robocorp_ls_core: reuses existing LSP code, but it is proprietary and complex.
