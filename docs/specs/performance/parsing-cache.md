# Parsing Cache

## Stage

**Done** (Stage 12)

## Goal

Avoid re-parsing the AST when the document has not changed.

## Strategy

- Cache by URI with document version and content hash
- Automatic invalidation when version or text changes
- Maximum size: LRU cache with 50 entries by default
- Explicit invalidation by URI or full cache
- Disk cache for workspace index remains outside the MVP

## Implementation Sketch

```python
class ParseCache:
    _cache: OrderedDict[str, ParseResult]
    _max_size: int = 50

    def get(uri: str, text: str) -> ParseResult | None
    def set(uri: str, text: str, result: ParseResult) -> None
    def invalidate(uri: str) -> None
```

## Notes

- Implemented with `OrderedDict` inside `ParseService`.
- Workspace cache remains separate from the open document cache.
- Versionamento usa `Document.version` e SHA-256 do texto.
- Disk cache will be evaluated when there are real metrics for large workspaces.
