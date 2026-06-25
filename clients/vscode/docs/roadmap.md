# VS Code Client Roadmap

## Current Stage

Stage 10 - Debug Adapter MVP

Status: `pending`

## Stages

| Stage | Name | Status |
|---|---|---|
| 00 | Documentation And Architecture | done |
| 01 | VS Code Scaffold | done |
| 02 | Language Client Startup | done |
| 03 | Python Resolution | done |
| 04 | Configuration Bridge | done |
| 05 | Syntax Highlighting And Language Configuration | done |
| 06 | LSP Feature Smoke Tests | done |
| 07 | Test Explorer MVP | done |
| 08 | Run Support | done |
| 09 | Debug Adapter Design | done |
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

## Stage 05 Acceptance Criteria

- TextMate grammar contributed for `robotframework` files.
- Grammar highlights section headers, comments, settings, Robot variables, typed variables, `VAR`, `GROUP`, `END`, control keywords, and keyword calls.
- Language configuration includes comments, brackets, auto-closing pairs, surrounding pairs, folding markers, indentation rules, and Robot-aware word pattern.
- Syntax highlighting works independently from the Python language server.
- TypeScript compilation passes with `npm run compile`.

## Stage 06 Acceptance Criteria

- `npm test` exists for VS Code client smoke validation.
- Smoke tests compile the extension before executing runtime checks.
- Smoke tests verify the Robot Framework document selector used by the language client.
- Smoke tests verify default language server startup uses `python -m robot_lsp` style arguments.
- Smoke tests verify `robot-lsp.languageServer.command` overrides the default server command.
- Smoke tests verify VS Code settings map to the server `robot.lsp` configuration shape.
- Smoke tests verify initialization options use the same configuration shape as workspace configuration.

## Stage 07 Acceptance Criteria

- Test controller is registered with id `robot-lsp.testController` and display name `Robot Framework` when `robot-lsp.testExplorer.enabled` is enabled.
- Initial fallback discovery scans workspace `.robot` files without requiring the Python language server to start.
- Test discovery recognizes top-level test cases under `*** Test Cases ***` and top-level tasks under `*** Tasks ***`.
- Test Explorer tree shape is `File.robot -> Test Case Name` for discovered tests.
- Test item ranges point at the discovered test declaration line.
- Smoke tests cover the fallback scanner used by the Test Explorer MVP.
- Run and debug execution are intentionally deferred to later stages.

## Stage 08 Acceptance Criteria

- Run commands are contributed for `robot-lsp.runCurrentFile` and `robot-lsp.runCurrentTest`.
- Run commands build `robot-lsp` launch configurations with `noDebug: true`.
- Current-file runs target the active Robot Framework document.
- Current-test runs select the nearest discovered test or task at the active cursor line.
- Generated run configurations include runtime Python, environment, Python path, and Robot variables from settings.
- Test Explorer exposes a Run profile and starts selected test items through the same run controller.
- Smoke tests cover generated file and test run configurations.
- Debug adapter execution and final result reporting are intentionally deferred to later stages.

## Stage 09 Acceptance Criteria

- VS Code manifest contributes debug type `robot-lsp` with label `Robot LSP`.
- Debug contribution is scoped to the `robotframework` language.
- Launch configuration attributes document target, cwd, args, env, variables, python, pythonPath, terminal, and makeSuite.
- Initial launch configuration and snippet are provided for the current Robot Framework file.
- Extension activates for debug sessions and registers a debug configuration provider.
- Debug configuration provider normalizes missing launch values using the active Robot document or workspace defaults.
- Application layer can build debug launch configurations with `noDebug: false`.
- Smoke tests cover the debug launch configuration contract and package contribution.
