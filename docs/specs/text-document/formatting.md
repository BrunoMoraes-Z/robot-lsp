# Formatting

## Stage

**Done** (Stage 11)

## LSP Methods

- `textDocument/formatting`
- `textDocument/rangeFormatting`

## Notes

Formatar arquivos `.robot` seguindo boas práticas iniciais de espaçamento.

## Behavior

- `textDocument/formatting` retorna um único `TextEdit` cobrindo o documento inteiro quando o texto muda.
- `textDocument/rangeFormatting` formata linhas completas tocadas pelo range informado.
- Separadores entre células são normalizados para 4 espaços.
- Whitespace final de cada linha é removido.
- Linhas de section como `*** Settings ***` são aparadas.
- Linhas vazias e comentários preservam o conteúdo sem whitespace final.

## Out Of Scope

- Reordenação de settings, test cases ou keywords.
- Formatação semântica baseada em AST.
- Configuração de largura de separador via `FormattingOptions`.
