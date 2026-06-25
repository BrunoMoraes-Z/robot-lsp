# Text Document Synchronization

## Stage

Stage 03 — Document & Workspace

## LSP Methods

- `textDocument/didOpen`
- `textDocument/didChange`
- `textDocument/didClose`
- `textDocument/didSave` (optional, deferred)

## Initial Scope

- `TextDocumentSyncKind.Full` (1)
- `openClose: true`
- `change: Full`

## Implementation

### DocumentStore

```python
@dataclass
class Document:
    uri: str
    path: Path | None
    language_id: str
    version: int
    text: str
    lines: list[str]

class DocumentStore:
    _documents: dict[str, Document]

    def open(uri: str, text: str, version: int, language_id: str) -> Document
    def change(uri: str, text: str, version: int) -> Document
    def close(uri: str) -> None
    def get(uri: str) -> Document | None
    def get_all() -> list[Document]
```

### didChange Flow

1. Client sends `didChange` with `textDocument.uri`, `contentChanges[0].text` (full), `textDocument.version`
2. `DocumentStore.change()` updates text and version
3. Triggers `ParseService` to update the model
4. Triggers `DiagnosticService` to generate diagnostics

## Future Scope

- `TextDocumentSyncKind.Incremental` (2): send diffs instead of the full text
- `didSave`: optional notification
- `willSave` / `willSaveWaitUntil`: if needed

## Tests

- Document open
- Full content change
- Incremental versioning
- Close and removal
- Overwrite already-open document
