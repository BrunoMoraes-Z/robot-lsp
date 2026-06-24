# ADR-0001 — Project Scope

## Status

accepted

## Context

Precisamos definir o escopo inicial e visão de longo prazo do projeto.

## Decision

Robot Framework Language Server é um projeto de longo prazo que implementará o protocolo LSP completo para arquivos `.robot` e `.resource`. O projeto é real (não POC) e será desenvolvido em estágios incrementalmente.

### In Scope (visão geral)
- Servidor LSP para Robot Framework suportando RF >= 7.0.
- JSON-RPC 2.0 próprio (sem pygls).
- Transporte via `stdio`.
- Todos os métodos LSP propostos pelo protocolo, implementados em estágios.
- Clean Architecture com modelos intermediários.
- Suporte a múltiplas versões do Robot Framework via feature detection.
- Testes unitários e de integração.

### Out of Scope (neste projeto)
- Extensões IDE (VS Code, Neovim, etc.) — serão projetos separados no futuro.
- Debug adapter — não faz parte do protocolo LSP.
- Robot Framework Console (REPL) — não faz parte do protocolo LSP.

## Consequences

- Foco exclusivo no servidor simplifica a arquitetura inicial.
- Projetos separados para extensões IDE mantêm responsabilidade única.
- Documentamos a API de integração para facilitar extensões futuras.

## Alternatives Considered

- Unificar servidor + extensão em um repositório: rejeitado para manter independência de versão.
