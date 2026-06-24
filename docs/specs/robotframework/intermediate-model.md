# Intermediate Model

## Stage

Stage 04 — Robot Framework Model

## Purpose

Modelos intermediários desacoplam o core do LSP do AST do Robot Framework. Mudanças no AST do RF afetam apenas o adaptador, não as camadas de aplicação e protocolo.

## Models

### RobotDocument

```python
@dataclass
class RobotDocument:
    uri: str
    version: int
    text: str
    suite: RobotSuite | None
    errors: list[RobotDiagnostic]
```

### RobotSuite

```python
@dataclass
class RobotSuite:
    source: str | None
    name: str
    doc: str
    metadata: dict[str, str]
    settings: RobotSettings
    variables: list[RobotVariable]
    imports: list[RobotImport]
    test_cases: list[RobotTestCase]
    keywords: list[RobotKeyword]
```

### RobotSettings

```python
@dataclass
class RobotSettings:
    suite_setup: str | None
    suite_teardown: str | None
    test_setup: str | None
    test_teardown: str | None
    test_template: str | None
    test_timeout: str | None
    force_tags: list[str]
    default_tags: list[str]
```

### RobotVariable

```python
@dataclass
class RobotVariable:
    name: str
    value: str | list | dict | None
    kind: Literal["scalar", "list", "dict", "secret"]
    range: LspRange
```

### RobotImport

```python
@dataclass
class RobotImport:
    type: Literal["library", "resource", "variables"]
    name: str
    args: list[str]
    alias: str | None
    range: LspRange
```

### RobotTestCase

```python
@dataclass
class RobotTestCase:
    name: str
    doc: str
    tags: list[str]
    template: str | None
    timeout: str | None
    setup: str | None
    teardown: str | None
    body: list[RobotStep]
    range: LspRange
```

### RobotKeyword

```python
@dataclass
class RobotKeyword:
    name: str
    doc: str
    tags: list[str]
    args: list[RobotArg]
    body: list[RobotStep]
    range: LspRange
```

### RobotArg

```python
@dataclass
class RobotArg:
    name: str
    default: str | None
    kind: Literal["positional", "optional", "varargs", "kwargs"]
```

### RobotStep

```python
@dataclass
class RobotStep:
    keyword: str
    args: list[str]
    assign: list[str]
    range: LspRange
```

### RobotDiagnostic

```python
@dataclass
class RobotDiagnostic:
    message: str
    severity: Literal["error", "warning", "info"]
    range: LspRange
    code: str | None = None
```

## Design Decisions

- Todos os modelos usam `LspRange` (0-based UTF-16) para ranges
- Modelos são dataclasses simples, sem lógica de negócio
- `None` para campos opcionais indica ausência de informação
- Listas vazias para coleções (nunca None)
