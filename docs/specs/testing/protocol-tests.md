# Protocol Tests

## Stage

Stage 01 — JSON-RPC / Stage 02 — LSP Lifecycle

## Approach

Test the LSP protocol through in-memory transport, without real stdio.

```python
@pytest.fixture
def protocol_server():
    reader = io.BytesIO()
    writer = io.BytesIO()
    transport = TransportStdio(reader=reader, writer=writer)
    server = LspServer(transport=transport)
    return server, reader, writer
```

## Test Format

```python
def send_request(reader, writer, method: str, params: dict | None) -> dict:
    """Send request through writer and read response from reader."""
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    writer.write(encode_lsp(json.dumps(request)))
    writer.seek(0)
    response = read_lsp(reader)
    return json.loads(response)

def test_initialize():
    server, reader, writer = protocol_server()
    result = send_request(reader, writer, "initialize", {
        "processId": 1234,
        "capabilities": {},
        "rootUri": None
    })
    assert "capabilities" in result
    assert result["capabilities"]["textDocumentSync"] == 1
```

## What to Test

- Full initialize -> didOpen -> completion -> shutdown -> exit cycle
- Out-of-order messages
- Cancellation through $/cancelRequest
- Multiple concurrent requests
- Notifications with no expected response
