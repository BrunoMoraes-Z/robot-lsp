# Progress

## Stage

**Planned** (post-MVP)

## Methods

- `$/progress`
- `window/workDoneProgress/create`
- `window/workDoneProgress/cancel`

## Notes

Progress reporting will be implemented when long-running operations (workspace index, heavy analysis) justify user feedback.

## Implementation (future)

- `WorkDoneProgressBegin`, `WorkDoneProgressReport`, `WorkDoneProgressEnd`
- Token-based progress
- Cancelamento via `window/workDoneProgress/cancel`
