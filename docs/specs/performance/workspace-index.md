# Workspace Index

## Stage

Stage 09 — done

## Goal

Index all workspace `.robot` and `.resource` files for import, keyword, and variable resolution.

## Indexed Data

- Keywords defined in each file
- Imports (Library, Resource, Variables)
- Defined variables
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

- When a file is opened/closed/saved, update the corresponding entry
- `didChangeWatchedFiles` for external changes
- Lazy indexing: only when needed (completion/hover requests it)

## Notes

- Workspace index is the foundation for navigation (definition, references)
- Required to support multiple files and imports
- Performance: pode exigir worker separado se workspace grande

## Implemented

- `WorkspaceIndex.scan(root)`
- `WorkspaceIndex.update_file(path)`
- `WorkspaceIndex.remove_file(path)`
- `WorkspaceIndex.find_keyword(name)`
- `WorkspaceIndex.find_variable(name)`
- `WorkspaceIndex.resolve_import(source_path, import_)`
- In-memory cache by mtime + hash

## Future

- Cache em disco
- File watching
- Asynchronous indexing
- References globais
