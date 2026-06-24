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

### Observações

- Header termina com `\r\n\r\n`
- Content-Length é o número de bytes do JSON (UTF-8)
- Content-Type opcional, se presente deve ser parseado mas não validado
- Apenas um header obrigatório: `Content-Length`

## Implementation

### TransportStdio

```python
class TransportStdio:
    def read_message() -> str | None
    def write_message(message: str) -> None
```

- Leitura: `sys.stdin.buffer.read(n)` com loop até preencher Content-Length bytes
- Escrita: `sys.stdout.buffer.write(header + message)` thread-safe (lock)
- Erro de escrita: log em stderr

## Tests

- Mensagem simples
- Mensagem com body multi-byte
- Mensagem recebida em chunks parciais
- Múltiplas mensagens em sequência
- Content-Type ignorado
