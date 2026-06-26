# Semantic Tokens

## Goal

Provide contextual Robot Framework colorization through LSP semantic tokens, using the Robot Framework parser as the source of truth.

TextMate grammar remains the fast fallback for immediate editor feedback. Semantic tokens add the second pass that regex grammars cannot provide reliably.

## LSP Methods

- `textDocument/semanticTokens/full`
- `textDocument/semanticTokens/range` (deferred)

## Server Capability

The server advertises a fixed semantic token legend:

```json
{
  "semanticTokensProvider": {
    "legend": {
      "tokenTypes": [
        "variable",
        "comment",
        "header",
        "setting",
        "name",
        "keywordNameDefinition",
        "variableOperator",
        "keywordNameCall",
        "settingOperator",
        "control",
        "testCaseName",
        "parameterName",
        "argumentValue",
        "error",
        "documentation"
      ],
      "tokenModifiers": []
    },
    "full": true,
    "range": false
  }
}
```

The legend order is stable. New token types may only be appended unless a breaking protocol version is introduced.

## Initial Scope

The first implementation is intentionally direct: convert Robot Framework parser tokens to LSP semantic tokens without advanced sub-tokenization.

Initial token mapping:

- `COMMENT` -> `comment`
- section/header tokens -> `header`
- setting tokens -> `setting`
- import/resource/library names -> `name`
- keyword definition names -> `keywordNameDefinition`
- test case names -> `testCaseName`
- keyword calls -> `keywordNameCall`
- arguments -> `argumentValue`
- variables and assignments -> `variable`
- control-flow tokens -> `control`
- parser errors/fatal errors -> `error`

## Roadmap

### Step 1: Protocol and Direct Parser Tokens

- Add semantic token legend and server capability.
- Add `textDocument/semanticTokens/full` handler.
- Add `SemanticTokensService` with LSP delta encoding.
- Add Robot Framework parser-backed token extraction.
- Add unit tests for capability, handler shape, and token presence.

### Step 2: VS Code Scope Mapping

- Add `semanticTokenScopes` to the VS Code extension manifest.
- Map token types to broadly supported TextMate scopes.
- Prefer compatibility with existing Robot Framework scopes where practical.
- Keep TextMate grammar as fallback.

### Step 3: Variable and Setting Operators

Status: implemented.

- Split `${name}` into variable operators and variable body where useful.
- Split `[Arguments]` into setting operators and setting name.
- Keep UTF-16 offsets correct for non-ASCII text.

### Step 4: Named Arguments

Status: implemented.

- Split `name=value` arguments into `parameterName`, `variableOperator`, and `argumentValue`.
- Handle escaped equals and Robot Framework syntax differences conservatively.

### Step 5: Keyword Call Refinement

- Split `Library.Keyword` into library/resource prefix as `name` and callable part as `keywordNameCall`.
- Color BDD prefixes such as `Given`, `When`, `Then`, `And`, `But` as `control`.
- Add localized BDD prefix support when localization data is available.

### Step 6: Documentation and Errors

- Color documentation bodies as `documentation`.
- Ensure parser errors and invalid headers are surfaced as `error` tokens where positions are available.

### Step 7: Performance and Caching

- Avoid duplicate parsing if metrics show semantic tokens become expensive.
- Either cache raw parser token data or extend parse results with a stable syntax-token model.
- Keep semantic token generation cancellation-aware for large files.

## Tests

- `initialize` advertises the semantic token provider with the expected legend.
- Missing documents return no semantic token result.
- Open documents return valid `data` arrays using LSP semantic token delta encoding.
- Headers, comments, variables, test names, keyword definitions, keyword calls, settings, and control tokens are represented.
- UTF-16 token lengths are correct for non-ASCII content.
