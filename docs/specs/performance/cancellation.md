# Cancellation

## Stage

Stage 01 — JSON-RPC (básico), Stage 12 (avaliado)

## Current Implementation

- `$/cancelRequest` marca request como cancelado
- Handler verifica periodicamente `is_canceled()` e aborta se True
- Resposta de request cancelado não é enviada

## Future Implementation

- `asyncio` tasks com `Task.cancel()` para cancelamento real
- Timeout automático para requests longos (ex: 10s)
- Worker pool com `concurrent.futures` e cancelamento via Future

## Stage 12 Decision

- O servidor ainda executa handlers síncronos e curtos.
- Parse cache reduz reparses antes de introduzir concorrência.
- Cancelamento real com worker pool fica postergado até existir request longo mensurável.

## Design

```python
class CancelToken:
    _canceled: bool = False

    def cancel(self) -> None
    def is_canceled(self) -> bool
    def raise_if_canceled(self) -> None
```
