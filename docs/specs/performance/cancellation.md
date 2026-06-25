# Cancellation

## Stage

Stage 01 — JSON-RPC (basic), Stage 12 (evaluated)

## Current Implementation

- `$/cancelRequest` marks request as cancelled
- Handler checks `is_canceled()` periodically or calls `raise_if_canceled()` and aborts if true
- Cancelled request response is not sent
- `CancelToken` is thread-safe and backed by `threading.Event`
- `MethodDispatcher` supports optional worker execution per method with `ThreadPoolExecutor`
- Worker-backed requests are cancelled through both `CancelToken` and `Future.cancel()`

## Future Implementation

- Automatic timeout for long requests (for example, 10s)
- Metrics-based migration of specific heavy LSP handlers to worker execution
- `asyncio` tasks with `Task.cancel()` if the server loop is migrated to asyncio

## Post-MVP 06 Decision

- Worker pool infrastructure is implemented in `MethodDispatcher`.
- Existing LSP handlers remain synchronous because there is still no measured long-running handler that justifies thread-safety costs.
- Future heavy handlers can opt in with `register(..., run_in_worker=True)`.

## Design

```python
class CancelToken:
    _cancel_event: threading.Event

    def cancel(self) -> None
    def is_canceled(self) -> bool
    def raise_if_canceled(self) -> None
```

```python
dispatcher = MethodDispatcher(max_workers=2)
dispatcher.register("workspace/heavyOperation", handler, run_in_worker=True)
```
