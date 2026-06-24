# ADR-0004 — Robot Framework AST Adapter

## Status

accepted

## Context

O AST do Robot Framework muda entre versões (ex: `Return` → `ReturnSetting` em 7.0, `Group` adicionado em 7.2). Precisamos isolar o core do LSP dessas mudanças.

## Decision

Criar uma camada de adaptador em `infrastructure/robotframework/` que:

1. Usa exclusivamente APIs públicas de `robot.api.parsing` (nunca `robot.parsing.*`).
2. Define modelos intermediários próprios em `domain/models.py`.
3. O adaptador mapeia nós do AST RF → modelos intermediários.
4. O core do LSP trabalha apenas com modelos intermediários.

### Modelos intermediários
- `RobotSuite`, `RobotSettings`, `RobotVariable`, `RobotImport`
- `RobotTestCase`, `RobotKeyword`, `RobotStep`, `RobotArg`
- `RobotDiagnostic`

### Versionamento
- `FeatureSet` contém flags baseadas na versão do RF.
- Novos nós AST são mapeados condicionalmente conforme disponíveis.

## Consequences

- Mudanças no AST do RF afetam apenas o adaptador.
- Testes do adaptador quebram primeiro quando RF muda, protegendo o resto.
- Core do LSP permanece estável entre versões do RF.

## Alternatives Considered

- Usar AST do RF diretamente: rejeitado por risco de quebra entre versões.
- monkey-patching do AST: rejeitado por ser frágil.
