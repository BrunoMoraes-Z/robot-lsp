# Variables

## Stage

Stage 04 — Robot Framework Model (parse), Stage 06 — Completion (completion), Stage 07 — Hover (hover)

## Variable Syntax

| Syntax | Type | Example |
|---|---|---|
| `${name}` | Scalar | `${greeting}` |
| `@{name}` | List | `@{items}` |
| `&{name}` | Dict | `&{config}` |
| `%{name}` | Environment | `%{PATH}` |
| `\${name}` (secret, >= 7.4) | Secret | `\${password}` |

## Variable Sources

1. **Variable section**: `*** Variables ***`
2. **Arguments**: keyword/test arguments
3. **Return values**: from called keywords
4. **BuiltIn variables**: `${CURDIR}`, `${TEMPDIR}`, etc.

## Initial Scope (MVP)

- Variables from the `*** Variables ***` section (parse, completion, hover)
- Keyword argument variables (parse)
- BuiltIn variables (completion)

## Future Scope

- Scoped variables (resolution of which `@{list}` is being referenced)
- Environment variables
- Secret variables (7.4+)
- Shortcut: `$var` without braces (short syntax)
