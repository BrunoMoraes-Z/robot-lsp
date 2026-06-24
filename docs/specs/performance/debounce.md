# Debounce

## Stage

Stage 05 — Diagnostics

## Goal

Evitar processamento excessivo durante digitação rápida.

## Implementation

```python
class Debouncer:
    _timers: dict[str, threading.Timer]

    def debounce(key: str, delay: float, callback: Callable) -> None
    def cancel(key: str) -> None
    def cancel_all() -> None
```

## Current Usage

- Diagnostics: 300ms debounce por URI
- Completion: sem debounce (responde a cada request)
- Hover: sem debounce (responde a cada request)

## Future Usage

- Workspace re-index: 500ms debounce
- Code analysis: 300ms debounce

## Design

- Timer é cancelado se nova chamada chegar com mesma key
- Timer executa callback no próximo tick do event loop
- Thread-safe: usar `threading.Lock` ou `threading.Timer` nativo
