# Robot Framework Version Support

## Stage

Stage 04 — Robot Framework Model

## Supported Versions

- **Minimum**: 7.0
- **Current**: todas as versões 7.x
- **Policy**: suportar toda a linha 7.x durante seu ciclo de vida

## Version Detection

```python
from robot.version import VERSION
# "7.0", "7.1.1", "7.2.2", "7.4.2"
```

## Feature Matrix

| Version | Group/END | Secret Variables | Notes |
|---|---|---|---|
| 7.0 | No | No | Base mínima |
| 7.1 | No | No | Sem mudanças no AST |
| 7.2 | Yes | No | `Group`/`GroupHeader` adicionado |
| 7.3 | Yes | No | Apenas mudanças de sintaxe |
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

1. Parsear `robot.version.VERSION`
2. Comparar com versões conhecidas
3. Feature detection via `try/except ImportError` como fallback

## Risks

- RF pode remover APIs públicas em versão futura (ex: deprecation warning em 7.x, remoção em 8.x)
- Feature detection via import é mais seguro que comparação de string de versão

## Tests

- Detecção em RF 7.0
- Detecção em RF 7.2+
- Feature detection com `try/except`
- Fallback para versão desconhecida (assumir mínimo)
