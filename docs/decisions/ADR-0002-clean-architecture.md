# ADR-0002 — Clean Architecture

## Status

accepted

## Context

The project must be sustainable long term, with clear separation of responsibilities to allow independent maintenance, testing, and evolution.

## Decision

Adopt Clean Architecture (also known as Onion Architecture or Hexagonal Architecture) with the following layers:

- **Domain**: pure business models with no external dependencies.
- **Application**: use cases that orchestrate the domain.
- **Protocol**: communication with the outside world (JSON-RPC, LSP framing).
- **Infrastructure**: concrete implementations (RF parser, adapters).

### Dependency Rule
- Source code may depend only on more internal layers.
- `domain` -> no dependencies.
- `application` → domain.
- `protocol` → application, domain.
- `infrastructure` → domain.
- No layer imports from another layer's outer layer.

## Consequences

- Testability: each layer can be tested in isolation.
- Implementation swapping: the RF parser can be replaced without affecting the core.
- Framework agnostic: the LSP server does not depend on external LSP libraries.

## Alternatives Considered

- Flat structure: rejected because it does not scale with LSP complexity.
- MVC: does not fit a protocol-oriented server.
