# Progress

## Stage

**Done** (post-MVP 08)

## Methods

- `$/progress`
- `window/workDoneProgress/create`
- `window/workDoneProgress/cancel`

## Notes

Progress reporting is available for server-initiated work. It is currently used around outbound `workspace/configuration` requests when the client advertises `window.workDoneProgress: true`.

## Implementation

- `WorkDoneProgressBegin`, `WorkDoneProgressReport`, `WorkDoneProgressEnd`
- Token-based progress
- `window/workDoneProgress/create` request is queued before progress notifications
- `$/progress` notifications carry `begin`, `report`, and `end` values

## Future

- Apply the same helper to measured long-running operations such as workspace indexing.
- Cancellation through `window/workDoneProgress/cancel`.
