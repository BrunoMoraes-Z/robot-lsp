# Import Resolution

## Stage

**Planned** (Stage 09)

## LSP Methods

- N/A (internal service)

## Goal

Resolver imports `Library`, `Resource`, `Variables` para encontrar arquivos reais no sistema de arquivos.

## Resolution Order

1. Relativo ao diretório do arquivo atual
2. Relativo aos diretórios do Python path (para libraries Python)
3. Caminhos configurados pelo usuário (`robot.lsp.importPaths`)

## Implementation Components

- `ImportResolver`: resolve imports para paths absolutos
- `LibraryResolver`: encontra módulos Python para libraries
- `ResourceResolver`: encontra arquivos `.resource` e `.robot`
- Cache de resolução com invalidação

## Notes

- Resolução de libraries Python requer inspecionar `sys.path` e módulos instalados
- Libraries podem ter aliases (`Library  Collections  alias=MyLib`)
- Variables files podem ser `.py`, `.yaml`, `.json`, `.robot`
- Resolução será implementada junto com workspace index
