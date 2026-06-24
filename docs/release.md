# Release

## Build Artifacts

Build source distribution and wheel artifacts locally:

```powershell
uv sync --extra dev
uv build
```

The artifacts are written to `dist/`.

## Smoke Install

Validate the generated wheel in a clean virtual environment before publishing:

```powershell
python -m venv .venv-package-smoke
$wheel = (Get-ChildItem -Path dist -Filter *.whl | Select-Object -First 1).FullName
.venv-package-smoke\Scripts\python -m pip install $wheel
.venv-package-smoke\Scripts\robot-lsp --version
```

## CI

The `package` job builds the source distribution and wheel, installs the wheel in a clean environment, runs `robot-lsp --version`, and uploads `dist/*` as a workflow artifact.

## Publishing

PyPI publishing is intentionally manual until credentials and release approval flow are defined.
