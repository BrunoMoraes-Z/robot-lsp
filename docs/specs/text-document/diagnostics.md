# Diagnostics

## Stage

Stage 05 — Diagnostics

## LSP Methods

- `textDocument/publishDiagnostics` (notification servidor → cliente)

## Initial Scope

- Diagnostics de parse/sintaxe vindos do Robot Framework
- Debounce de 300ms
- Cancelamento de diagnóstico pendente por URI
- Range do erro quando disponível; fallback para linha inteira

## Implementation

### LspDiagnostic

```python
@dataclass
class LspDiagnostic:
    range: LspRange
    severity: DiagnosticSeverity
    message: str
    source: str = "robot-lsp"
    code: str | None = None
```

### DiagnosticService

```python
class DiagnosticService:
    _parse_service: ParseService
    _debounce_timers: dict[str, threading.Timer]
    _last_diagnostics: dict[str, list[LspDiagnostic]]
    DEBOUNCE_SECONDS = 0.3

    def schedule_diagnostics(uri: str) -> None
    def _compute_and_publish(uri: str) -> None
    def cancel_pending(uri: str) -> None
```

### Flow

1. `didChange` → `schedule_diagnostics(uri)`
2. Se já existe timer para uri, cancela
3. Agenda novo timer para `DEBOUNCE_SECONDS`
4. Timer executa: parse + collect diagnostics + publica
5. Publicação via `server.publish_diagnostics(uri, diagnostics)`
6. Se diagnostics são idênticos aos últimos publicados, não publica

### RF Range Conversion

- Robot Framework: linha/coluna 1-based
- LSP: linha 0-based, coluna 0-based UTF-16
- Se RF não fornecer coluna, usar coluna 0
- Se RF não fornecer end line/col, usar start line/col (point diagnostic)

## Future Scope

- Análise semântica (imports quebrados, keywords não encontradas)
- Integração com robocop ou linter externo
- Diagnostics com código para code actions
- Diagnostic tags (unnecessary, deprecated)

## Tests

- Parse error → diagnostic publicado
- Correção → diagnostics limpos
- Debounce → não publica se timer ainda não expirou
- Cancelamento → timer antigo não publica
- Range 1-based → 0-based
