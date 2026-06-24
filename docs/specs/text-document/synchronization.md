# Text Document Synchronization

## Stage

Stage 03 — Document & Workspace

## LSP Methods

- `textDocument/didOpen`
- `textDocument/didChange`
- `textDocument/didClose`
- `textDocument/didSave` (opcional, postergado)

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

1. Cliente envia `didChange` com `textDocument.uri`, `contentChanges[0].text` (full), `textDocument.version`
2. `DocumentStore.change()` atualiza texto e versão
3. Dispara `ParseService` para atualizar modelo
4. Dispara `DiagnosticService` para gerar diagnostics

## Future Scope

- `TextDocumentSyncKind.Incremental` (2) — enviar diffs em vez do texto completo
- `didSave` — notificação opcional
- `willSave` / `willSaveWaitUntil` — se necessário

## Tests

- Abertura de documento
- Mudança completa de conteúdo
- Versionamento incremental
- Fechamento e remoção
- Sobrescrita de documento já aberto
