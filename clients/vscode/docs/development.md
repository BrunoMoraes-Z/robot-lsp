# VS Code Client Development

## Prerequisites

- Node.js LTS
- npm
- VS Code
- Python 3.10+
- `robot-lsp` development checkout

## Planned Development Setup

```powershell
cd clients/vscode
npm install
npm run compile
```

## Development Server Command

During local development, the extension may start the server with:

```powershell
uv run python -m robot_lsp
```

from the repository root.

## Clean Architecture Rule

Do not import `vscode` from domain or application modules. Keep VS Code APIs in infrastructure and presentation adapters.
