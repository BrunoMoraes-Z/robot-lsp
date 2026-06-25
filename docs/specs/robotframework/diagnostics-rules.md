# Diagnostics Rules

## Stage

Stage 05 — Diagnostics

## Initial Rules

### Parse Errors

- Robot Framework syntax errors are reported as `error`
- Includes: invalid section, missing argument, incorrect IF/WHILE/FOR syntax, etc.
- Range obtained from the error reported by RF

### Warnings (future)

- Template in test case without arguments
- Force tags overriding tags
- Empty documentation in public keyword

### Semantic Errors (future)

- Library/resource/variables import not found
- Keyword called but not defined or imported
- Variable referenced but not defined
- Positional argument after named argument
- Missing template in test case that uses a template

## Severity Mapping

| Type | LSP Severity | Code |
|---|---|---|
| Parse error | 1 (Error) | parse_error |
| Import not found | 1 (Error) | import_not_found |
| Keyword not found | 2 (Warning) | keyword_not_found |
| Variable not found | 2 (Warning) | variable_not_found |
| Style issue | 3 (Information) | style_issue |
| Unused keyword | 3 (Information) | unused_keyword |
