# Debounce

## Stage

Stage 05 — Diagnostics

## Goal

Avoid excessive processing during fast typing.

## Implementation

```python
class Debouncer:
    _timers: dict[str, threading.Timer]

    def debounce(key: str, delay: float, callback: Callable) -> None
    def cancel(key: str) -> None
    def cancel_all() -> None
```

## Current Usage

- Diagnostics: 300 ms debounce by URI
- Completion: no debounce (responds to each request)
- Hover: no debounce (responds to each request)

## Future Usage

- Workspace re-index: 500ms debounce
- Code analysis: 300ms debounce

## Design

- Timer is cancelled if a new call arrives with the same key
- Timer runs callback on the next event loop tick
- Thread-safe: use `threading.Lock` or native `threading.Timer`
