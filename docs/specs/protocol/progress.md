# Progress

## Stage

**Planned** (pós-MVP)

## Methods

- `$/progress`
- `window/workDoneProgress/create`
- `window/workDoneProgress/cancel`

## Notes

Progress reporting será implementado quando operações longas (workspace index, análise pesada) justificarem feedback ao usuário.

## Implementation (future)

- `WorkDoneProgressBegin`, `WorkDoneProgressReport`, `WorkDoneProgressEnd`
- Token-based progress
- Cancelamento via `window/workDoneProgress/cancel`
