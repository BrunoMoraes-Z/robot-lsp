# Robot Framework Version Support

## Stage

Stage 04 — Robot Framework Model

## Supported Versions

- **Minimum**: 7.0
- **Current**: all 7.x versions
- **Policy**: support the entire 7.x line during its lifecycle

## Version Detection

```python
from robot.version import VERSION
# "7.0", "7.1.1", "7.2.2", "7.4.2"
```

## Feature Matrix

| Version | VAR Syntax | Group/END | Variable Type Conversion | Secret Variables | Notes |
|---|---|---|---|---|---|
| 7.0 | Yes | No | No | No | Minimum baseline |
| 7.1 | Yes | No | No | No | No AST changes |
| 7.2 | Yes | Yes | No | No | `Group`/`GroupHeader` added |
| 7.3 | Yes | Yes | Yes | No | Variable type annotations supported |
| 7.4 | Yes | Yes | Yes | Yes | `Secret` type supported |

## Implemented 7.x Support

- `VAR` syntax is parsed from test and keyword bodies, including variable kind, scope, value, and type annotation.
- `GROUP` body statements are traversed so contained keyword calls participate in diagnostics and completion sources.
- `GROUP` nodes are exposed as document symbols and folding ranges.
- Variable type annotations such as `${value: int}` are parsed and validated against the built-in type allowlist.
- Dotted Python type annotations are accepted when the module can be imported and the attribute exists.
- Completion suggests built-in variable types while editing a variable type annotation.
- `VAR` variables are resolved lexically: they are visible only after their declaration line.
- `Secret` type annotations are represented as `secret` variables when Robot Framework 7.4+ is available.

## Remaining Future Scope

- Full resolution of user-provided type converters beyond importable Python classes.
- Runtime-aware scope/priority modeling across nested suites and command-line variables.

## Feature Detection

```python
@dataclass
class FeatureSet:
    has_group: bool
    has_secret_variables: bool
    version_str: str
    version: VersionInfo
```

### Detection Strategy

1. Parse `robot.version.VERSION`
2. Compare with known versions
3. Feature detection through `try/except ImportError` as fallback

## Risks

- RF may remove public APIs in a future version (for example, deprecation warning in 7.x, removal in 8.x)
- Feature detection through import is safer than version string comparison

## Tests

- Detection in RF 7.0
- Detection in RF 7.2+
- Feature detection with `try/except`
- Fallback for unknown version (assume minimum)
