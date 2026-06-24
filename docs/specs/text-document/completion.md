# Completion

## Stage

Stage 06 — Completion

## LSP Methods

- `textDocument/completion`
- `completionItem/resolve` (postergado)

## Initial Scope

- Completar sections: `*** Settings ***`, `*** Variables ***`, `*** Test Cases ***`, `*** Keywords ***`
- Completar settings em `*** Settings ***`: `Library`, `Resource`, `Variables`, `Documentation`, `Metadata`, `Suite Setup`, `Suite Teardown`, `Test Setup`, `Test Teardown`, `Test Tags`, `Test Template`, `Test Timeout`, `Force Tags`, `Default Tags`
- Completar keywords locais (definidas no mesmo arquivo)
- Completar variáveis locais (definidas no mesmo arquivo)
- Trigger characters: ` ` (espaço), `$`, `@`, `&`, `%`

## Implementation

### CompletionService

```python
class CompletionService:
    _parse_service: ParseService

    def compute_completion(uri: str, position: LspPosition) -> CompletionList | None
```

### Providers

```python
class CompletionProvider(ABC):
    def should_trigger(context: CompletionContext) -> bool
    def compute(context: CompletionContext) -> list[CompletionItem]
```

### Providers Implementados

1. **SectionProvider**: no início do arquivo, após linha vazia
2. **SettingProvider**: em seção Settings, após nome do setting
3. **LocalKeywordProvider**: em chamada de keyword (contexto body)
4. **LocalVariableProvider**: quando cursor após `$`, `@`, `&`, `%`

### CompletionContext

```python
@dataclass
class CompletionContext:
    uri: str
    position: LspPosition
    document: Document
    suite: RobotSuite | None
    line_text: str
    line_prefix: str  # texto antes do cursor na linha
    trigger_kind: CompletionTriggerKind
    trigger_character: str | None
```

### CompletionItem Format

```python
@dataclass
class CompletionItem:
    label: str
    kind: CompletionItemKind
    detail: str | None = None
    documentation: str | None = None
    text_edit: TextEdit | None = None
    data: Any = None  # para resolve futuro
```

## Future Scope

- Keywords de libraries importadas
- Variables de resources importados
- Snippets para templates de keyword/test case
- Auto-import (completar Library/Resource com path)
- `completionItem/resolve` para documentação detalhada
- Filtering e sorting inteligente

## Tests

- Sections completadas corretamente
- Settings completados apenas em Settings section
- Keywords locais aparecem
- Variáveis locais aparecem
- Trigger characters
- Contexto vazio retorna lista vazia
