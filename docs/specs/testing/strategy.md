# Testing Strategy

## Stage

All stages

## Levels

### Unit Tests (`tests/unit/`)

- Testam uma única classe/função isoladamente
- Mocks para dependências externas (infrastructure, RF)
- Execução rápida (segundos)
- Cobertura: todas as funções públicas de domain, application e protocol

### Integration Tests (`tests/integration/`)

- Testam interação entre camadas
- Usam fixtures `.robot` reais
- Testam parser/adapter com RF real instalado
- Testam sessão LSP via transporte em memória
- Execução moderada (minutos)

### Protocol Tests (dentro de `tests/unit/protocol/`)

- Testam JSON-RPC e framing contra especificação
- Testam lifecycle LSP
- Usam transporte em memória (não stdio real)

## Test Framework

- `pytest` como framework principal
- `conftest.py` para fixtures compartilhadas
- `pytest-cov` para cobertura (opcional)
- `unittest.mock` para mocks

## Fixtures

### Robot Files (`tests/integration/fixtures/`)

- `basic_suite.robot`: suite mínima com settings, variables, test case, keyword
- `settings.robot`: todas as variações de settings
- `variables.robot`: scalar, list, dict, environment variables
- `keywords.robot`: keyword com argumentos, docstring, body
- `syntax_error.robot`: arquivo com erros de sintaxe
- `resource.robot`: resource file para testes de import
- `group_rf72.robot`: arquivo usando GROUP/END (RF 7.2+)
- `secret_variable.robot`: uso de secret variable (RF 7.4+)

### In-Memory Transport

```python
@pytest.fixture
def in_memory_transport():
    """Transport que não usa stdio real."""
    reader = io.StringIO()
    writer = io.StringIO()
    transport = TransportStdio(reader=reader, writer=writer)
    return transport, reader, writer
```

## Conftest Structure

- `tests/conftest.py`: fixtures globais
- `tests/unit/conftest.py`: fixtures para unit tests
- `tests/integration/conftest.py`: fixtures com RF real

## Naming Convention

- Arquivos: `test_<module>.py`
- Classes: `Test<Feature>`
- Funções: `test_<feature>_<scenario>`

## Compatibility Matrix

| RF Version | Test Runner |
|---|---|
| 7.0.x | CI (opcional, mínimo) |
| 7.1.x | CI |
| 7.2.x | CI |
| 7.3.x | CI |
| 7.4.x | CI (default) |
