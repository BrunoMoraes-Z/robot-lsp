# Completion

## Stage

Stage 06 — Completion

## LSP Methods

- `textDocument/completion`
- `completionItem/resolve` (deferred)

## Initial Scope

- Complete sections: `*** Settings ***`, `*** Variables ***`, `*** Test Cases ***`, `*** Keywords ***`
- Complete settings in `*** Settings ***`: `Library`, `Resource`, `Variables`, `Documentation`, `Metadata`, `Suite Setup`, `Suite Teardown`, `Test Setup`, `Test Teardown`, `Test Tags`, `Test Template`, `Test Timeout`, `Force Tags`, `Default Tags`
- Complete local keywords (defined in the same file)
- Complete local variables (defined in the same file)
- Trigger characters: ` ` (space), `$`, `@`, `&`, `%`

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

### Implemented Providers

1. **SectionProvider**: at the start of the file, after an empty line
2. **SettingProvider**: in Settings section, after the setting name
3. **LocalKeywordProvider**: in keyword calls (body context)
4. **LocalVariableProvider**: when cursor is after `$`, `@`, `&`, `%`

### CompletionContext

```python
@dataclass
class CompletionContext:
    uri: str
    position: LspPosition
    document: Document
    suite: RobotSuite | None
    line_text: str
    line_prefix: str  # text before the cursor on the line
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
    data: Any = None  # for future resolve
```

## Future Scope

- Keywords from imported libraries
- Variables from imported resources
- Snippets for keyword/test case templates
- Auto-import (complete Library/Resource with path)
- `completionItem/resolve` for detailed documentation
- Smart filtering and sorting

## Tests

- Sections completed correctly
- Settings completed only in Settings section
- Local keywords appear
- Local variables appear
- Trigger characters
- Empty context returns an empty list
