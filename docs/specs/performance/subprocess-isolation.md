# Subprocess Isolation

## Stage

**Planned** (Stage 12)

## Motivation

No MVP, o servidor executa tudo no mesmo processo. Se workspace index ou análise pesada bloquear o event loop, completion/hover ficam lentos.

## Strategy

- **Não implementar subprocessos no MVP**
- Monitorar performance com arquivos reais
- Se necessário, adicionar subprocesso apenas para operações pesadas

## Possible Architecture

```
Main Process (LSP lifecycle, completion, hover)
  └── Subprocess (workspace index, lint, analysis)
```

## Communication

- Subprocesso também usa JSON-RPC sobre stdio (pipe) para comunicação
- Main process serializa requests e responses
- Subprocesso pode ser restartado independentemente

## Lessons from robotframework-lsp

- O LSP existente usa 3 subprocessos (api/lint/others)
- Para um MVP menor, 1 subprocesso suficiente
- Complexidade alta: gerenciar lifecycle, restart, timeout
- Postergar até que métricas justifiquem

## Notes

- Cancelamento entre processos é mais complexo
- Comunicação via pipe com framing JSON-RPC reaproveita código existente
- Subprocesso precisa de seu próprio `DocumentStore` (sincronizado via `didOpen`/`didChange`)
