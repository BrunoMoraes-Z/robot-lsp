# Keywords

## Stage

Stage 04 — Robot Framework Model (parse), Stage 06 — Completion, Stage 07 — Hover

## Types

1. **User keywords**: defined in `*** Keywords ***`
2. **Library keywords**: from imported libraries
3. **BuiltIn keywords**: internal Robot Framework keywords (Should Be Equal, Log, etc.)
4. **Resource keywords**: from imported `.resource` files

## Initial Scope (MVP)

- User keywords from the same file
- Basic BuiltIn keywords (known beforehand)

## Future Scope

- Library keywords through libspec
- Resource keywords through workspace index
- Keyword argument completion
- Keyword calltips/signature help
