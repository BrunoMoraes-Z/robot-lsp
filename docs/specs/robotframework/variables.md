# Variables

## Stage

Stage 04 — Robot Framework Model (parse), Stage 06 — Completion (completion), Stage 07 — Hover (hover)

## Variable Syntax

| Syntax | Type | Exemplo |
|---|---|---|
| `${name}` | Scalar | `${greeting}` |
| `@{name}` | List | `@{items}` |
| `&{name}` | Dict | `&{config}` |
| `%{name}` | Environment | `%{PATH}` |
| `\${name}` (secret, >= 7.4) | Secret | `\${password}` |

## Variable Sources

1. **Variable section**: `*** Variables ***`
2. **Arguments**: keyword/test arguments
3. **Return values**: de keywords chamadas
4. **BuiltIn variables**: `${CURDIR}`, `${TEMPDIR}`, etc.

## Initial Scope (MVP)

- Variables do `*** Variables ***` section (parse, completion, hover)
- Variáveis de argumento de keyword (parse)
- BuiltIn variables (completion)

## Future Scope

- Variáveis de escopo (resolução de qual `@{list}` está sendo referenciada)
- Environment variables
- Secret variables (7.4+)
- Atalho: `$var` sem chaves (sintaxe curta)
