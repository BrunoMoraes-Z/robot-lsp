# Cancellation

## Stage

Stage 01 — JSON-RPC (basic), Stage 12 (evaluated)

## Current Implementation

- `$/cancelRequest` marca request como cancelado
- Handler verifica periodicamente `is_canceled()` e aborta se True
- Cancelled request response is not sent

## Future Implementation

- `asyncio` tasks with `Task.cancel()` for real cancellation
- Automatic timeout for long requests (for example, 10s)
- Worker pool with `concurrent.futures` and cancellation through Future

## Stage 12 Decision

- The server still runs short synchronous handlers.
- Parse cache reduces reparsing before introducing concurrency.
- Real cancellation with worker pool is deferred until there is a measurable long-running request.

## Design

```python
class CancelToken:
    _canceled: bool = False

    def cancel(self) -> None
    def is_canceled(self) -> bool
    def raise_if_canceled(self) -> None
```
