# Parsing Cache

## Stage

**Planned** (Stage 12)

## Goal

Evitar re-parsing do AST quando o documento não mudou.

## Strategy

- Cache por URI com hash do conteúdo
- Invalidação: quando `didChange` chega com texto diferente
- Tamanho máximo: LRU cache com N entradas (ex: 50)
- Cache em disco para workspace index (ex: usando `pickle` + mtime)

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

- Cache simples implementável com `@lru_cache` ou `OrderedDict`
- Cache de workspace (disco) será diferente do cache de documentos abertos
- Versionamento: usar timestamp ou hash do conteúdo como chave
