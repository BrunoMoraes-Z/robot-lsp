# Import Resolution

## Stage

Stage 09 — partially implemented, Stage 13 — configured paths

## LSP Methods

- N/A (internal service)

## Goal

Resolver imports `Library`, `Resource`, `Variables` para encontrar arquivos reais no sistema de arquivos.

## Resolution Order

1. Relativo ao diretório do arquivo atual
2. Caminhos configurados pelo usuário (`robot.lsp.importPaths`) para imports de arquivo
3. Relativo aos diretórios do Python path (para libraries Python)

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

## Implemented

- `Resource` relativo ao arquivo atual
- `Variables` relativo ao arquivo atual
- `Resource` e `Variables` via caminhos configurados em `robot.lsp.importPaths`
- `Library` via `importlib.util.find_spec()`
- Robot standard libraries via `robot.libraries.<name>`

## Future

- Libspec/libdoc completo para libraries
- Resolução de variables files `.py`, `.yaml`, `.json` com extração semântica
