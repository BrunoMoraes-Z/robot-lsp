# Integration Tests

## Stage

All stages

## Approach

Testar o servidor LSP completo via processo real, usando `subprocess` com transporte stdio.

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
    # Ler Content-Length header
    # Ler body
    pass
```

## Scenarios

- Sessão LSP completa com initialize, document sync, completion, hover, shutdown
- Múltiplos documentos abertos
- Documento com erro de sintaxe → diagnostics publicados
- Documento corrigido → diagnostics limpos
- Servidor é iniciado apenas com `python -m robot_lsp`
