# VS Code Language Client

## Goal

Start `robot-lsp` as a stdio language server and connect it to VS Code documents with language id `robotframework`.

## Activation

The extension activates for:

- `.robot`
- `.resource`
- Commands under `robot-lsp.*`

## Document Selector

```ts
[
  { scheme: "file", language: "robotframework" },
  { scheme: "untitled", language: "robotframework" }
]
```

## Server Startup

Default server module:

```text
python -m robot_lsp
```

Development startup may use:

```text
uv run python -m robot_lsp
```

When `robot-lsp.languageServer.command` is set, it overrides the normal Python/module startup flow.

## Client Options

The client should enable:

- Synchronization for `.robot` and `.resource` files
- Workspace folder support
- Configuration requests
- Trace/log forwarding to a VS Code output channel

## Restart Behavior

The extension provides `robot-lsp.restartLanguageServer`.

Restart is required when:

- Language server Python changes
- Server command changes
- Server cwd changes
- Critical environment variables change

Regular settings such as diagnostics and snippets should be sent through configuration without restarting when possible.
