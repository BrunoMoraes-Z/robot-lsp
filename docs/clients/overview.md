# Clients Overview

## Purpose

Clients integrate `robot-lsp` with editors and IDEs without changing the core language server. Each client is responsible for editor-specific activation, process startup, configuration mapping, user interface integration, and packaging.

## Repository Layout

```text
clients/
  vscode/    VS Code extension client
```

Future clients such as Zed, Neovim, or IntelliJ should live under `clients/<client-name>/` and keep their editor-specific code isolated from `src/robot_lsp/`.

## Design Principles

- The core LSP remains editor-agnostic.
- Clients start the LSP over stdio by default.
- Clients map editor configuration into `robot.lsp` server configuration.
- Client code follows Clean Architecture boundaries where practical.
- Client-specific run, debug, and test explorer behavior belongs under `clients/`.

## Shared Requirements

- Resolve a Python interpreter that can run `robot_lsp` and import `robotframework>=7.0`.
- Support workspace-specific configuration.
- Surface startup failures with actionable messages.
- Keep server logs and client logs separate but correlated.
- Prefer explicit user settings over auto-detection.

## Current Client Roadmap

| Client | Status | Notes |
|---|---|---|
| VS Code | Planned | First supported editor client |
