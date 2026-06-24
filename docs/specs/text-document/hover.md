# Hover

## Stage

Stage 07 — Hover

## LSP Methods

- `textDocument/hover`

## Initial Scope

- Hover em keyword local: nome, args, docstring
- Hover em variável local: tipo, valor
- Hover em import: tipo, caminho
- Formatação Markdown

## Implementation

### HoverService

```python
class HoverService:
    _parse_service: ParseService

    def compute_hover(uri: str, position: LspPosition) -> Hover | None
```

### Providers

```python
class HoverProvider(ABC):
    def should_handle(context: HoverContext) -> bool
    def compute(context: HoverContext) -> Hover | None
```

### Providers Implementados

1. **KeywordHoverProvider**: encontra keyword na posição, retorna `**Nome(args)**` + docstring
2. **VariableHoverProvider**: encontra variável na posição, retorna tipo e valor
3. **ImportHoverProvider**: encontra import na posição, retorna tipo e caminho

### HoverContext

```python
@dataclass
class HoverContext:
    uri: str
    position: LspPosition
    document: Document
    suite: RobotSuite | None
    word_at_position: str | None  # palavra sob o cursor
```

### Hover Response

```python
@dataclass
class Hover:
    contents: MarkupContent
    range: LspRange | None
```

### Markdown Format

- Keyword: `**keyword_name(args)**\n\nDocstring text`
- Variable: `**${var}**\`\`\`\nType: scalar\nValue: "hello"\`\`\``
- Import: `**Library**: Collections`
- Vazio: `None` (null)

## Future Scope

- Hover em keywords de libraries (via libspec)
- Hover em BuiltIn keywords
- Signature help para argumentos
- Documentation rica (exemplo, tags, etc.)

## Tests

- Keyword local → markdown correto
- Variável → tipo e valor
- Import → tipo
- Símbolo inexistente → None
- Range correto
