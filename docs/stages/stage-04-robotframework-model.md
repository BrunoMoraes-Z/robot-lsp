# Stage 04 — Robot Framework Model

## Status

done

## Goal

Implementar o detector de versão do Robot Framework, o parser via `robot.api.parsing`, o modelo intermediário e o adaptador AST.

## Scope

- `RobotFrameworkVersionDetector`: lê `robot.version.VERSION` e retorna `VersionInfo`
- `FeatureSet`: flags baseadas na versão:
  - `has_group` (>= 7.2)
  - `has_secret_variables` (>= 7.4)
- Modelo intermediário em `domain/models.py`:
  - `RobotSuite`, `RobotSettings`, `RobotVariable`, `RobotImport`
  - `RobotTestCase`, `RobotKeyword`, `RobotStep`, `RobotArg`
  - `RobotDocument`
- `RobotFrameworkParser`: interface pública para parse de texto/arquivo
- `RobotFrameworkASTAdapter`: mapeia AST do RF para modelos intermediários
  - Visita `File` → `RobotSuite`
  - `SettingSection` → `RobotSettings`, `RobotImport`, `RobotVariable`
  - `TestCaseSection` → `RobotTestCase`
  - `KeywordSection` → `RobotKeyword`
- Fixtures de teste: arquivos `.robot` e `.resource` reais

## Out Of Scope

- Diagnostics (Stage 05)
- Completion/hover baseados no modelo (Stage 06+)
- Resolução de imports/bibliotecas

## Deliverables

- `src/robot_lsp/domain/models.py`
- `src/robot_lsp/domain/features.py`
- `src/robot_lsp/infrastructure/robotframework/version.py`
- `src/robot_lsp/infrastructure/robotframework/parser.py`
- `src/robot_lsp/infrastructure/robotframework/adapter.py`
- `src/robot_lsp/infrastructure/robotframework/visitors.py`
- Fixtures `.robot` em `tests/integration/fixtures/`
- Testes unitários do adapter

## Acceptance Criteria

- Versão 7.0+ detectada sem erro
- `FeatureSet` reflete versão instalada
- `RobotSuite` é populado corretamente a partir de texto `.robot`
- Settings, variables, imports, test cases e keywords são extraídos
- Erros de parse (sintaxe inválida) são capturados sem crash
- Core não importa `robot.api.parsing` nem `robot.parsing.*`
- Testes com fixtures reais passam

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

- AST do RF pode mudar entre minor versions — testar adapter com cada versão 7.x
- Erros de parse podem vir sem posição — fallback necessário

## Dependencies

- Stage 03 (precisa de `Document` e posições)

## Notes

- Stage concluída com parser e adapter base para Robot Framework >= 7.0.
- O core (`domain`, `application`, `protocol`) não importa `robot.api.parsing` nem `robot.parsing`.
- O adapter trabalha por modelos intermediários e tokens públicos do `robot.api.parsing`.
- Erros de parse expostos como nós `Error` são convertidos para `RobotDiagnostic`.
- Validação executada com `just test` e `uv run python -m compileall src tests`.
