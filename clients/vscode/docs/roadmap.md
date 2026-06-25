# VS Code Client Roadmap

## Current Stage

Stage 05 - Syntax Highlighting And Language Configuration

Status: `pending`

## Stages

| Stage | Name | Status |
|---|---|---|
| 00 | Documentation And Architecture | done |
| 01 | VS Code Scaffold | done |
| 02 | Language Client Startup | done |
| 03 | Python Resolution | done |
| 04 | Configuration Bridge | done |
| 05 | Syntax Highlighting And Language Configuration | pending |
| 06 | LSP Feature Smoke Tests | pending |
| 07 | Test Explorer MVP | pending |
| 08 | Run Support | pending |
| 09 | Debug Adapter Design | pending |
| 10 | Debug Adapter MVP | pending |
| 11 | Packaging And Release | pending |

## Stage 00 Acceptance Criteria

- Client architecture documented.
- Settings documented with `robot-lsp.*` prefix.
- Python resolution strategy documented.
- Run/debug/test explorer strategy documented.
- Debug adapter strategy documented.

## Stage 01 Acceptance Criteria

- `package.json` created with VS Code metadata and `robot-lsp.*` settings.
- `tsconfig.json` created with strict TypeScript settings.
- `src/` Clean Architecture folders created.
- `extension.ts` created as composition root.
- Placeholder commands registered.
- `robotframework` language contribution added for `.robot` and `.resource`.
- TypeScript compilation passes with `npm run compile`.

## Stage 02 Acceptance Criteria

- `vscode-languageclient` dependency added.
- Extension starts `robot-lsp` over stdio on activation.
- Server command uses `robot-lsp.languageServer.*` overrides when configured.
- Default startup uses `python -m robot_lsp` on Windows and `python3 -m robot_lsp` on Linux/macOS.
- Restart command stops and starts the language client.
- Deactivation stops the language client.
- TypeScript compilation passes with `npm run compile`.

## Stage 03 Acceptance Criteria

- Python resolution implemented in the application layer behind ports.
- Resolution order supports explicit setting, VS Code Python extension, workspace virtual environments, and PATH fallback.
- Language server Python is validated by importing `robot_lsp` and `robotframework>=7.0`.
- Startup shows an actionable VS Code error when no valid Python is found.
- Language client startup uses the resolved Python unless `robot-lsp.languageServer.command` is configured.
- Domain and application layers remain free of VS Code API imports.

## Stage 04 Acceptance Criteria

- VS Code settings with `robot-lsp.*` prefix are mapped to the server's `robot.lsp` configuration shape.
- `workspace/configuration` requests for `robot.lsp` are answered by the client.
- Initialization options use the same configuration bridge as workspace configuration requests.
- `${workspaceFolder}` is expanded in language server, runtime, env, python path, and Robot variable settings.
- `robot-lsp.variables` reaches the core LSP and suppresses false undefined-variable diagnostics.
- TypeScript compilation passes with `npm run compile`.
