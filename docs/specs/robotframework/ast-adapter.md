# Robot Framework AST Adapter

## Stage

Stage 04 — Robot Framework Model

## Goal

Map the Robot Framework AST (a mutable structure across versions) to stable intermediate models in `domain/models.py`.

## Architecture

```
robot.api.parsing (AST) → RobotFrameworkParser → RobotFrameworkASTAdapter → domain.models
```

## Adapter Pattern

```python
class RobotFrameworkASTAdapter:
    def __init__(self, features: FeatureSet):
        self._features = features

    def to_suite(self, model: File) -> RobotSuite:
        ...

    def to_settings(self, section: SettingSection) -> RobotSettings:
        ...

    def to_variables(self, section: VariableSection) -> list[RobotVariable]:
        ...

    def to_imports(self, section: SettingSection) -> list[RobotImport]:
        ...

    def to_test_cases(self, section: TestCaseSection) -> list[RobotTestCase]:
        ...

    def to_keywords(self, section: KeywordSection) -> list[RobotKeyword]:
        ...
```

## Version-Specific Handling

```python
# RF 7.0+: ReturnSetting (setting) differs from Return (statement)
if self._features.version.at_least(7, 0):
    # Treat ReturnSetting as a setting
    # Treat Return as a keyword call
```

## Visitor Implementation

```python
# visitors.py
class ModelBuildingVisitor(ModelVisitor):
    def __init__(self, adapter: RobotFrameworkASTAdapter):
        self.adapter = adapter
        self.suite: RobotSuite | None = None

    def visit_File(self, node: File):
        ...
    def visit_SettingSection(self, node: SettingSection):
        ...
    def visit_VariableSection(self, node: VariableSection):
        ...
    def visit_TestCaseSection(self, node: TestCaseSection):
        ...
    def visit_KeywordSection(self, node: KeywordSection):
        ...
```

## Error Handling

- Syntax errors are returned separately from the model
- Adapter never raises exceptions; it collects errors in a list
- ParseService returns `ParseResult(suite=..., errors=[...])`

## Tests

- Each statement/block type has a mapping test
- Parse errors are captured without crashing
- Conditional FeatureSet affects mapping
