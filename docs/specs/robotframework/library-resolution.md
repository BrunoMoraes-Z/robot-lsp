# Library Resolution

## Stage

**Planned** (Stage 09)

## Goal

Resolver libraries Python importadas em arquivos `.robot` e extrair keywords, argumentos e documentação.

## Approaches

1. **Static analysis**: ler arquivo Python da library, extrair nomes de função e docstrings via AST
2. **libdoc**: usar `robot.libdoc` para gerar documentação estruturada
3. **Cache**: armazenar libspec (keyword definitions) em cache de disco

## Implementation Strategy

- Iniciar com static analysis básico para libraries Python puras
- libdoc como fallback para libraries complexas
- Cache em disco com invalidação por mtime

## Challenges

- Libraries podem ser dinâmicas (keywords geradas em runtime)
- Libraries podem ter wrapper/decorator que esconde assinatura real
- Libraries podem ser em Java ou .NET via remote library

## Notes

- Resolução total de libraries é complexa e será incremental
- MVP inicial suporta apenas keywords locais e BuiltIn
- Libraries conhecidas (BuiltIn, Collections, etc.) podem ter specs manuais iniciais
