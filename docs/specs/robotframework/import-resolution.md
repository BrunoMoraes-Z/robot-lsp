# Import Resolution

## Stage

Stage 09 — partially implemented, Stage 13 — configured paths

## LSP Methods

- N/A (internal service)

## Goal

Resolve `Library`, `Resource`, and `Variables` imports to find real files on the filesystem.

## Resolution Order

1. Relative to the current file directory
2. User-configured paths (`robot.lsp.importPaths`) for file imports
3. Relative to Python path directories (for Python libraries)

## Implementation Components

- `ImportResolver`: resolves imports to absolute paths
- `LibraryResolver`: finds Python modules for libraries
- `ResourceResolver`: finds `.resource` and `.robot` files
- Resolution cache with invalidation

## Notes

- Python library resolution requires inspecting `sys.path` and installed modules
- Libraries may have aliases (`Library  Collections  alias=MyLib`)
- Variables files may be `.py`, `.yaml`, `.json`, `.robot`
- Resolution will be implemented together with workspace index

## Implemented

- `Resource` relative to the current file
- `Variables` relative to the current file
- `Resource` and `Variables` through paths configured in `robot.lsp.importPaths`
- `Library` via `importlib.util.find_spec()`
- Robot standard libraries via `robot.libraries.<name>`

## Future

- Full libspec/libdoc for libraries
- Variables file resolution for `.py`, `.yaml`, `.json` with semantic extraction
