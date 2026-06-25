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

| Version | Group/END | Secret Variables | Notes |
|---|---|---|---|
| 7.0 | No | No | Minimum baseline |
| 7.1 | No | No | No AST changes |
| 7.2 | Yes | No | `Group`/`GroupHeader` added |
| 7.3 | Yes | No | Syntax changes only |
| 7.4 | Yes | Yes | `Secret` type |

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
