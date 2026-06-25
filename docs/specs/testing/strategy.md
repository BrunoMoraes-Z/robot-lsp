# Testing Strategy

## Stage

All stages

## Levels

### Unit Tests (`tests/unit/`)

- Test a single class/function in isolation
- Mocks for external dependencies (infrastructure, RF)
- Fast execution (seconds)
- Coverage: all public functions in domain, application, and protocol

### Integration Tests (`tests/integration/`)

- Test interaction between layers
- Usam fixtures `.robot` reais
- Test parser/adapter with real installed RF
- Test LSP session through in-memory transport
- Moderate execution time (minutes)

### Protocol Tests (dentro de `tests/unit/protocol/`)

- Test JSON-RPC and framing against the specification
- Testam lifecycle LSP
- Use in-memory transport (not real stdio)

## Test Framework

- `pytest` como framework principal
- `conftest.py` for shared fixtures
- `pytest-cov` for coverage (optional)
- `unittest.mock` for mocks

## Fixtures

### Robot Files (`tests/integration/fixtures/`)

- `basic_suite.robot`: minimal suite with settings, variables, test case, keyword
- `settings.robot`: all settings variations
- `variables.robot`: scalar, list, dict, environment variables
- `keywords.robot`: keyword with arguments, docstring, body
- `syntax_error.robot`: file with syntax errors
- `resource.robot`: resource file for import tests
- `group_rf72.robot`: file using GROUP/END (RF 7.2+)
- `secret_variable.robot`: uso de secret variable (RF 7.4+)

### In-Memory Transport

```python
@pytest.fixture
def in_memory_transport():
    """Transport that does not use real stdio."""
    reader = io.StringIO()
    writer = io.StringIO()
    transport = TransportStdio(reader=reader, writer=writer)
    return transport, reader, writer
```

## Conftest Structure

- `tests/conftest.py`: fixtures globais
- `tests/unit/conftest.py`: fixtures for unit tests
- `tests/integration/conftest.py`: fixtures with real RF

## Naming Convention

- Arquivos: `test_<module>.py`
- Classes: `Test<Feature>`
- Functions: `test_<feature>_<scenario>`

## Compatibility Matrix

| RF Version | Test Runner |
|---|---|
| 7.0.x | CI (optional, minimum) |
| 7.1.x | CI |
| 7.2.x | CI |
| 7.3.x | CI |
| 7.4.x | CI (default) |
