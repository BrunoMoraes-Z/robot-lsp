# ADR-0002 — Clean Architecture

## Status

accepted

## Context

O projeto precisa ser sustentável a longo prazo, com separação clara de responsabilidades para permitir manutenção, testes e evolução independentes.

## Decision

Adotar Clean Architecture (também conhecida como Arquitetura Limpa / Onion Architecture / Hexagonal) com as seguintes camadas:

- **Domain**: modelos de negócio puros, sem dependências externas.
- **Application**: casos de uso que orquestram o domínio.
- **Protocol**: comunicação com o mundo exterior (JSON-RPC, LSP framing).
- **Infrastructure**: implementações concretas (parser RF, adaptadores).

### Regra de dependência
- Código fonte pode depender apenas de camadas mais internas.
- `domain` → nenhuma dependência.
- `application` → domain.
- `protocol` → application, domain.
- `infrastructure` → domain.
- Nenhuma camada importa da camada externa de outra.

## Consequences

- Testabilidade: cada camada pode ser testada isoladamente.
- Troca de implementação: parser RF pode ser substituído sem afetar core.
- Framework agnóstico: o LSP não depende de bibliotecas externas de LSP.

## Alternatives Considered

- Flat structure: rejeitada por não escalar com a complexidade do LSP.
- MVC: não se adequa a um servidor orientado a protocolo.
