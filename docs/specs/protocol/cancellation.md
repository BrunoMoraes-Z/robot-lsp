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

### Flow

1. Request arrives with `id`
2. Handler is registered in `_pending`
3. If `$/cancelRequest` arrives for `id`, mark it in `_canceled` and remove it from `_pending`
4. Handler periodically checks `is_canceled(id)` and aborts if true
5. Response for a cancelled request is not sent to the client

## Notes

- Cancellation is cooperative (handlers must check)
- Initial simplified implementation can be a `_canceled` flag
- Future version: `asyncio` tasks with `Task.cancel()`
