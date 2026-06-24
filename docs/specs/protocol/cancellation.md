# Cancellation

## Stage

Stage 01 — JSON-RPC

## Methods

### $/cancelRequest

```json
{"jsonrpc":"2.0","method":"$/cancelRequest","params":{"id": 1}}
```

## Implementation

### Endpoint

```python
class Endpoint:
    _pending: dict[int, asyncio.Future | threading.Event]
    _canceled: set[int]

    def register_request(id: int, handler: Callable)
    def cancel_request(id: int)
    def is_canceled(id: int) -> bool
```

### Fluxo

1. Request chega com `id`
2. Handler é registrado em `_pending`
3. Se `$/cancelRequest` chega para `id`, marca em `_canceled` e remove de `_pending`
4. Handler periodicamente checa `is_canceled(id)` e aborta se True
5. Resposta de request cancelado não é enviada ao cliente

## Notes

- Cancelamento é cooperativo (handlers precisam checar)
- Implementação inicial simplificada pode ser uma flag `_canceled`
- Versão futura: `asyncio` tasks com `Task.cancel()`
