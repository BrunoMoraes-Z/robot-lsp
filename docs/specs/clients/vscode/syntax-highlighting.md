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
- Word pattern that keeps Robot variables recognizable

## TextMate Grammar Scope

Root scope:

```text
source.robotframework
```

Initial grammar coverage:

- Section headers: `*** Settings ***`, `*** Variables ***`, `*** Test Cases ***`, `*** Tasks ***`, `*** Keywords ***`
- Comments
- Settings names
- Variable references: `${x}`, `@{x}`, `&{x}`, `%{x}`
- Typed variables: `${x: int}`
- `VAR` syntax
- `GROUP` and `END`
- Keyword calls and arguments

## LSP Relationship

Syntax highlighting is independent from the LSP and must not require the Python server to start.
