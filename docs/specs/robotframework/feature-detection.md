# Feature Detection

## Stage

Stage 04 — Robot Framework Model

## Strategy

Usar duas abordagens complementares:

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

Usar `try/except ImportError` para classes que podem não existir:

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

FeatureSet é computado uma vez na inicialização do servidor e disponibilizado via injeção de dependência. Todas as partes do sistema que precisam saber de capacidades do RF recebem o FeatureSet.

## Tests

- Testar com mock de `robot.version.VERSION`
- Testar com RF 7.0 e RF 7.2+ se disponível
- FeatureSet congelado (frozen) para evitar mutação
