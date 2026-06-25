# Watched Files

## Stage

**Planned** (post-MVP)

## LSP Methods

- `workspace/didChangeWatchedFiles`

## Notes

- Notify server about changes in `.robot` and `.resource` files outside open documents
- Used to invalidate workspace index cache
- Registered through `workspace/didChangeWatchedFiles` capability during initialization
