# VS Code Client Roadmap

## Current Stage

Stage 02 - Language Client Startup

Status: `pending`

## Stages

| Stage | Name | Status |
|---|---|---|
| 00 | Documentation And Architecture | done |
| 01 | VS Code Scaffold | done |
| 02 | Language Client Startup | pending |
| 03 | Python Resolution | pending |
| 04 | Configuration Bridge | pending |
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
