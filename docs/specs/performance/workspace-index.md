# Workspace Index

## Stage

Stage 09 — done

## Goal

Indexar todos os arquivos `.robot` e `.resource` do workspace para resolução de imports, keywords e variáveis.

## Indexed Data

- Keywords definidas em cada arquivo
- Imports (Library, Resource, Variables)
- Variáveis definidas
- Test cases

## Implementation

```python
@dataclass
class WorkspaceEntry:
    uri: str
    suite: RobotSuite
    mtime: float
    hash: str

class WorkspaceIndex:
    _entries: dict[str, WorkspaceEntry]

    def find_keyword(name: str) -> list[KeywordLocation]
    def find_variable(name: str) -> list[VariableLocation]
    def resolve_import(import_: RobotImport) -> str | None
```

## Incremental Update

- Quando arquivo é aberto/fechado/salvo, atualizar entry correspondente
- `didChangeWatchedFiles` para mudanças externas
- Indexação lazy: só quando necessário (completion/hover pedir)

## Notes

- Workspace index é a base para navigation (definition, references)
- Necessário para suportar múltiplos arquivos e imports
- Performance: pode exigir worker separado se workspace grande

## Implemented

- `WorkspaceIndex.scan(root)`
- `WorkspaceIndex.update_file(path)`
- `WorkspaceIndex.remove_file(path)`
- `WorkspaceIndex.find_keyword(name)`
- `WorkspaceIndex.find_variable(name)`
- `WorkspaceIndex.resolve_import(source_path, import_)`
- Cache em memória por mtime + hash

## Future

- Cache em disco
- Watching de arquivos
- Indexação assíncrona
- References globais
