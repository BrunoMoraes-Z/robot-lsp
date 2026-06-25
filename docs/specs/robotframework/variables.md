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
| `${name: Secret}` (>= 7.4) | Secret | `${password: Secret}` |

## Variable Sources

1. **Variable section**: `*** Variables ***`
2. **Arguments**: keyword/test arguments
3. **VAR syntax**: `VAR    ${name}    value    scope=TEST`
4. **Return values**: from called keywords
5. **BuiltIn variables**: `${CURDIR}`, `${TEMPDIR}`, etc.

## Initial Scope (MVP)

- Variables from the `*** Variables ***` section (parse, completion, hover)
- Keyword argument variables (parse)
- Variables created with `VAR` syntax in test and keyword bodies (parse, completion, diagnostics)
- Variable type annotations for built-in types (parse, diagnostics, completion)
- Importable dotted Python type annotations such as `pathlib.PurePath`
- Lexical visibility for `VAR` declarations inside test and keyword bodies
- Secret variables through the `Secret` type annotation in RF 7.4+
- BuiltIn variables (completion)

## Future Scope

- Environment variables
- Full custom type/converter resolution beyond importable Python classes
- Runtime-aware variable priority across nested suites and command-line variables
- Shortcut: `$var` without braces (short syntax)
