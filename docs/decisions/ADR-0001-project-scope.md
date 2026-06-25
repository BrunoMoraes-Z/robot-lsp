# ADR-0001 — Project Scope

## Status

accepted

## Context

We need to define the project's initial scope and long-term vision.

## Decision

Robot Framework Language Server is a long-term project that will implement the full LSP protocol for `.robot` and `.resource` files. The project is real (not a POC) and will be developed incrementally in stages.

### In Scope (overview)
- LSP server for Robot Framework supporting RF >= 7.0.
- Custom JSON-RPC 2.0 implementation (without pygls).
- Transport through `stdio`.
- All LSP methods proposed by the protocol, implemented in stages.
- Clean Architecture with intermediate models.
- Support for multiple Robot Framework versions through feature detection.
- Unit and integration tests.

### Out of Scope (for this project)
- IDE extensions (VS Code, Neovim, etc.) will be separate future projects.
- Debug adapter: not part of the LSP protocol.
- Robot Framework Console (REPL): not part of the LSP protocol.

## Consequences

- Focusing only on the server simplifies the initial architecture.
- Separate IDE extension projects keep responsibilities isolated.
- We document the integration API to make future extensions easier.

## Alternatives Considered

- Unify server and extension in one repository: rejected to keep versioning independent.
