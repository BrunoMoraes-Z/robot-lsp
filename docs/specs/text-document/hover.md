# Hover

## Stage

Stage 07 — Hover

## LSP Methods

- `textDocument/hover`

## Initial Scope

- Hover on local keyword: name, args, docstring
- Hover on local variable: type, value
- Hover on import: type, path
- Markdown formatting

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

### Implemented Providers

1. **KeywordHoverProvider**: finds keyword at position, returns `**Name(args)**` + docstring
2. **VariableHoverProvider**: finds variable at position, returns type and value
3. **ImportHoverProvider**: finds import at position, returns type and path

### HoverContext

```python
@dataclass
class HoverContext:
    uri: str
    position: LspPosition
    document: Document
    suite: RobotSuite | None
    word_at_position: str | None  # word under the cursor
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
- Empty: `None` (null)

## Future Scope

- Hover on library keywords (through libspec)
- Hover on BuiltIn keywords
- Signature help for arguments
- Rich documentation (examples, tags, etc.)

## Tests

- Local keyword -> correct markdown
- Variable -> type and value
- Import -> type
- Missing symbol -> None
- Correct range
