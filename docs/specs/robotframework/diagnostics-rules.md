# Diagnostics Rules

## Stage

Stage 05 — Diagnostics

## Initial Rules

### Parse Errors

- Erros de sintaxe do Robot Framework são reportados como `error`
- Inclui: seção inválida, argumento faltando, sintaxe de IF/WHILE/FOR incorreta, etc.
- Range obtido do erro reportado pelo RF

### Warnings (future)

- Template em test case sem argumentos
- Força bruta (force tags) sobrescrevendo tags
- Documentação vazia em keyword pública

### Semantic Errors (future)

- Import de library/resource/variables não encontrado
- Keyword chamada mas não definida nem importada
- Variável referenciada mas não definida
- Argumento posicional após argumento nomeado
- Template ausente em test case que usa template

## Severity Mapping

| Tipo | Severidade LSP | Código |
|---|---|---|
| Parse error | 1 (Error) | parse_error |
| Import not found | 1 (Error) | import_not_found |
| Keyword not found | 2 (Warning) | keyword_not_found |
| Variable not found | 2 (Warning) | variable_not_found |
| Style issue | 3 (Information) | style_issue |
| Unused keyword | 3 (Information) | unused_keyword |
