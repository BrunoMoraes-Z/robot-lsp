# Integration Tests

## Stage

All stages

## Approach

Test the full LSP server through a real process, using `subprocess` with stdio transport.

```python
@pytest.fixture
def lsp_process():
    proc = subprocess.Popen(
        [sys.executable, "-m", "robot_lsp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    yield proc
    proc.kill()
```

## Test Format

```python
def send(proc, message: dict):
    data = json.dumps(message).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    proc.stdin.write(header + data)
    proc.stdin.flush()

def receive(proc) -> dict:
    # Read Content-Length header
    # Read body
    pass
```

## Scenarios

- Full LSP session with initialize, document sync, completion, hover, shutdown
- Multiple open documents
- Document with syntax error -> diagnostics published
- Fixed document -> diagnostics cleared
- Server is started only with `python -m robot_lsp`

## Implemented In Stage 14

- Stdio runner tested in memory with real framing.
- Minimal `initialize` -> `shutdown` -> `exit` session validated in `tests/unit/test_main.py`.
- Error response for invalid JSON-RPC message validated in the runner.

## Implemented Post-MVP

- Real subprocess test with `python -m robot_lsp` in `tests/integration/test_stdio_server.py`.
- Real session through stdio: `initialize`, `initialized`, `didOpen`, `completion`, `shutdown`, `exit`.
- Completion validation in a document opened through real stdio transport.
- Asynchronous diagnostics through stdio: parse error publication and cleanup after `didChange`.

## Future

- Subprocess test with multiple open documents.
- Subprocess test for hover, definition, and formatting.
