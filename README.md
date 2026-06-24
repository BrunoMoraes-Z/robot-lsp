# Robot Framework Language Server

Language Server Protocol implementation for Robot Framework, written in Python without `pygls`.

## Requirements

- Python 3.10+
- Robot Framework 7.0+
- `uv` for local development

## Run

```powershell
uv run python -m robot_lsp
```

The server speaks LSP over stdio using `Content-Length` framing.

## CLI

```powershell
uv run python -m robot_lsp --version
uv run python -m robot_lsp --log-level debug
```

## Development

```powershell
just test
uv run python -m compileall src tests
```

## Package Build

```powershell
uv sync --extra dev
uv build
```

See `docs/release.md` for release artifact validation.

## Implemented MVP Features

- JSON-RPC 2.0 and LSP stdio framing
- LSP lifecycle and full text document sync
- Robot Framework parsing through an infrastructure adapter
- Diagnostics, completion, hover, navigation, rename, formatting and code actions
- Workspace index for `.robot` and `.resource` files
- Parse cache and configuration handling

See `docs/roadmap.md` for stage details.
