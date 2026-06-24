# Cancellation

## Stage

Stage 01 — JSON-RPC (básico), Stage 12 (completo)

## Current Implementation

- `$/cancelRequest` marca request como cancelado
- Handler verifica periodicamente `is_canceled()` e aborta se True
- Resposta de request cancelado não é enviada

## Future Implementation

- `asyncio` tasks com `Task.cancel()` para cancelamento real
- Timeout automático para requests longos (ex: 10s)
- Worker pool com `concurrent.futures` e cancelamento via Future

## Design

```python
class CancelToken:
    _canceled: bool = False

    def cancel(self) -> None
    def is_canceled(self) -> bool
    def raise_if_canceled(self) -> None
```
