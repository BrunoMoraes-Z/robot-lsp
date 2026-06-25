# LSP Framing

## Stage

Stage 01 — JSON-RPC

## Specification

### Content-Length Header

```
Content-Length: <bytes>\r\n
\r\n
<json>
```

### Exemplo

```
Content-Length: 45\r\n
\r\n
{"jsonrpc":"2.0","id":1,"method":"exit","params":null}
```

### Notes

- Header ends with `\r\n\r\n`
- Content-Length is the number of bytes in the JSON (UTF-8)
- Optional Content-Type, parsed but not validated if present
- Only one required header: `Content-Length`

## Implementation

### TransportStdio

```python
class TransportStdio:
    def read_message() -> str | None
    def write_message(message: str) -> None
```

- Read: `sys.stdin.buffer.read(n)` with a loop until Content-Length bytes are filled
- Write: `sys.stdout.buffer.write(header + message)` thread-safe (lock)
- Write error: log to stderr

## Tests

- Simple message
- Message with multibyte body
- Message received in partial chunks
- Multiple messages in sequence
- Content-Type ignored
