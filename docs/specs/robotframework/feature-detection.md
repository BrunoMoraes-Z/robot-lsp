# Feature Detection

## Stage

Stage 04 — Robot Framework Model

## Strategy

Use two complementary approaches:

### 1. Version String Parsing

```python
@dataclass
class VersionInfo:
    major: int
    minor: int
    patch: int

    def at_least(self, major: int, minor: int = 0) -> bool:
        return (self.major, self.minor) >= (major, minor)
```

### 2. Feature Import Detection

Use `try/except ImportError` for classes that may not exist:

```python
try:
    from robot.api.parsing import Group
    has_group = True
except ImportError:
    has_group = False
```

## FeatureSet

```python
@dataclass(frozen=True)
class FeatureSet:
    version: VersionInfo
    has_group: bool
    has_secret_variables: bool
```

## Global Feature Set

FeatureSet is computed once during server startup and made available through dependency injection. Every system component that needs to know RF capabilities receives the FeatureSet.

## Tests

- Test with a mock of `robot.version.VERSION`
- Test with RF 7.0 and RF 7.2+ if available
- Frozen FeatureSet to avoid mutation
