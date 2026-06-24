# Watched Files

## Stage

**Planned** (pós-MVP)

## LSP Methods

- `workspace/didChangeWatchedFiles`

## Notes

- Notificar servidor sobre mudanças em arquivos `.robot` e `.resource` fora dos documentos abertos
- Usado para invalidar cache de workspace index
- Registrado via `workspace/didChangeWatchedFiles` capability na inicialização
