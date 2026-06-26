# VS Code Syntax Highlighting

## Goal

Provide immediate editor feedback even before the LSP starts.

## Language Contribution

Language id: `robotframework`

Extensions:

- `.robot`
- `.resource`

Aliases:

- Robot Framework
- Robot

## Language Configuration

- Line comment: `#`
- Brackets: `[]`, `{}`, `()`
- Auto-closing pairs for quotes and brackets
- Folding markers for block keywords such as `GROUP`, `IF`, `FOR`, `WHILE`, and `TRY`
- Indentation rules for Robot Framework block syntax
- Word pattern that keeps Robot variables recognizable

## TextMate Grammar Scope

Root scope:

```text
source.robotframework
```

Grammar file:

```text
clients/vscode/syntaxes/robot.tmLanguage.json
```

Initial grammar coverage:

- Section headers: `*** Settings ***`, `*** Variables ***`, `*** Test Cases ***`, `*** Tasks ***`, `*** Keywords ***`
- Comments
- Settings names
- Variable references: `${x}`, `@{x}`, `&{x}`, `%{x}`
- Typed variables: `${x: int}`
- `VAR` syntax
- `GROUP` and `END`
- Control keywords: `IF`, `ELSE IF`, `ELSE`, `FOR`, `WHILE`, `TRY`, `EXCEPT`, `FINALLY`, `RETURN`, `CONTINUE`, `BREAK`
- Keyword calls and arguments

## LSP Relationship

Syntax highlighting must not require the Python server to start. The TextMate grammar provides immediate fallback colorization while the LSP starts.

When the LSP is available, semantic tokens provide the richer second colorization pass. The client relies on the server capability documented in:

```text
docs/specs/text-document/semantic-tokens.md
```

## Semantic Token Scope Mapping

The VS Code extension should map server semantic token types to TextMate scopes with `semanticTokenScopes` in `package.json`.

Roadmap:

- Keep the current TextMate grammar for startup and fallback highlighting.
- Add semantic token scope mappings after the server emits stable token types.
- Prefer broadly supported scopes so common VS Code themes color tokens without custom theme rules.
- Evaluate compatibility with Robot Framework scopes used by existing extensions, especially `.robot` scopes.
