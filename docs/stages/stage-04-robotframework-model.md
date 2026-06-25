# Stage 04 — Robot Framework Model

## Status

done

## Goal

Implement the Robot Framework version detector, parser through `robot.api.parsing`, intermediate model, and AST adapter.

## Scope

- `RobotFrameworkVersionDetector`: reads `robot.version.VERSION` and returns `VersionInfo`
- `FeatureSet`: version-based flags:
- `has_group` (>= 7.2)
- `has_secret_variables` (>= 7.4)
- Intermediate model in `domain/models.py`:
- `RobotSuite`, `RobotSettings`, `RobotVariable`, `RobotImport`
- `RobotTestCase`, `RobotKeyword`, `RobotStep`, `RobotArg`
- `RobotDocument`
- `RobotFrameworkParser`: public interface for parsing text/files
- `RobotFrameworkASTAdapter`: maps RF AST to intermediate models
- Visits `File` -> `RobotSuite`
- `SettingSection` -> `RobotSettings`, `RobotImport`, `RobotVariable`
- `TestCaseSection` -> `RobotTestCase`
- `KeywordSection` -> `RobotKeyword`
- Test fixtures: real `.robot` and `.resource` files

## Out Of Scope

- Diagnostics (Stage 05)
- Model-based completion/hover (Stage 06+)
- Import/library resolution

## Deliverables

- `src/robot_lsp/domain/models.py`
- `src/robot_lsp/domain/features.py`
- `src/robot_lsp/infrastructure/robotframework/version.py`
- `src/robot_lsp/infrastructure/robotframework/parser.py`
- `src/robot_lsp/infrastructure/robotframework/adapter.py`
- `src/robot_lsp/infrastructure/robotframework/visitors.py`
- `.robot` fixtures in `tests/integration/fixtures/`
- Adapter unit tests

## Acceptance Criteria

- Version 7.0+ is detected without error
- `FeatureSet` reflects the installed version
- `RobotSuite` is populated correctly from `.robot` text
- Settings, variables, imports, test cases, and keywords are extracted
- Parse errors (invalid syntax) are captured without crashing
- Core does not import `robot.api.parsing` or `robot.parsing.*`
- Tests with real fixtures pass

## Tests

- `test_version_detection`
- `test_feature_set_rf7`
- `test_parse_basic_suite`
- `test_parse_settings`
- `test_parse_variables_scalar`
- `test_parse_variables_list_dict`
- `test_parse_imports`
- `test_parse_test_case`
- `test_parse_keyword`
- `test_parse_steps`
- `test_parse_with_syntax_error`
- `test_adapter_no_direct_rf_import_in_core`

## Risks

- RF AST may change between minor versions; test the adapter with each 7.x version
- Parse errors may come without positions; fallback is required

## Dependencies

- Stage 03 (needs `Document` and positions)

## Notes

- Stage completed with the base parser and adapter for Robot Framework >= 7.0.
- The core (`domain`, `application`, `protocol`) does not import `robot.api.parsing` or `robot.parsing`.
- The adapter works through intermediate models and public `robot.api.parsing` tokens.
- Parse errors exposed as `Error` nodes are converted to `RobotDiagnostic`.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
