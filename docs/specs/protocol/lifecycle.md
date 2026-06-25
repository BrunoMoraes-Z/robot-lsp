# LSP Lifecycle

## Stage

Stage 02 — LSP Lifecycle

## Methods

### initialize

```json
// Request
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
  "processId": 1234,
  "rootUri": "file:///c:/projects/robot",
  "capabilities": {...}
}}

// Response
{"jsonrpc":"2.0","id":1,"result":{
  "capabilities": {
    "textDocumentSync": 1,
    "completionProvider": {"triggerCharacters":[" "]},
    "hoverProvider": true
  },
  "serverInfo": {
    "name": "robot-lsp",
    "version": "0.1.0"
  }
}}
```

### initialized

```json
{"jsonrpc":"2.0","method":"initialized","params":{}}
```

### shutdown

```json
// Request
{"jsonrpc":"2.0","id":2,"method":"shutdown","params":null}
// Response
{"jsonrpc":"2.0","id":2,"result":null}
```

### exit

```json
{"jsonrpc":"2.0","method":"exit","params":null}
```

## Implementation

### Server States

```python
class ServerState(Enum):
    UNINITIALIZED = "uninitialized"
    RUNNING = "running"
    SHUTTING_DOWN = "shuttingDown"
    EXITED = "exited"
```

### LspServer

```python
class LspServer:
    state: ServerState
    document_store: DocumentStore
    parse_service: ParseService
    diagnostic_service: DiagnosticService
    completion_service: CompletionService
    hover_service: HoverService

    def handle_message(self, msg: JsonRpcMessage) -> JsonRpcMessage | None
```

- Returns `JsonRpcMessage` for responses, `None` for notifications
- Private methods `_handle_initialize`, `_handle_shutdown`, etc.
- Validates current state before processing each method
