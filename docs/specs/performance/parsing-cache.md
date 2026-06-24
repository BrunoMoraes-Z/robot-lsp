# Parsing Cache

## Stage

**Done** (Stage 12)

## Goal

Evitar re-parsing do AST quando o documento não mudou.

## Strategy

- Cache por URI com versão do documento e hash do conteúdo
- Invalidação automática quando versão ou texto mudam
- Tamanho máximo: LRU cache com 50 entradas por padrão
- Invalidação explícita por URI ou cache completo
- Cache em disco para workspace index fica fora do MVP

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

- Implementado com `OrderedDict` dentro de `ParseService`.
- Cache de workspace permanece separado do cache de documentos abertos.
- Versionamento usa `Document.version` e SHA-256 do texto.
- Cache em disco será avaliado quando houver métricas reais de workspace grande.
