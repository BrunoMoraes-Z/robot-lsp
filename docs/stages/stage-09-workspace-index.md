# Stage 09 — Workspace Index

## Status

done

## Goal

Indexar arquivos `.robot` e `.resource` do workspace para permitir resolução básica de imports, keywords e variables cross-file.

## Scope

- Indexação de arquivos `.robot` e `.resource`
- `WorkspaceEntry` com URI, path, suite, mtime e hash de conteúdo
- Busca de keywords e variables por nome
- Resolução básica de imports `Resource`, `Variables` e `Library`
- Cache simples por mtime + hash de conteúdo
- Integração opcional com completion/navigation para symbols de resources importados

## Out Of Scope

- Watching de arquivos via `workspace/didChangeWatchedFiles`
- Cache em disco
- Indexação assíncrona/worker pool
- Libspec completo de libraries Python
- References globais em todo workspace

## Deliverables

- `src/robot_lsp/application/workspace.py`
- Testes unitários de indexação, resolução e integração com navigation/completion

## Acceptance Criteria

- `scan(root)` indexa `.robot` e `.resource`
- `find_keyword(name)` retorna keywords indexadas
- `find_variable(name)` retorna variables indexadas
- `resolve_import()` resolve `Resource` e `Variables` relativos ao arquivo atual
- `resolve_import()` resolve libraries Python/Robot padrão quando possível
- `CompletionService` pode incluir keywords/variables de resource importado
- `NavigationService.definition()` pode apontar para keyword/variable em resource importado

## Tests

- `test_scan_indexes_robot_and_resource_files`
- `test_find_keyword_and_variable`
- `test_resolve_resource_import`
- `test_resolve_variables_import`
- `test_resolve_library_import`
- `test_imported_keyword_locations`
- `test_imported_variable_locations`
- `test_update_file_reuses_cache_when_unchanged`
- `test_completion_includes_imported_resource_keyword`
- `test_definition_points_to_imported_resource_keyword`

## Risks

- Resolução de libraries ainda não substitui libdoc/libspec completo.
- Indexação síncrona pode ficar pesada em workspaces grandes; Stage 12 tratará performance/isolamento.

## Dependencies

- Stage 04
- Stage 06
- Stage 08

## Notes

- Stage concluída com indexação local síncrona e cache em memória.
- Resolução de `Library` usa `importlib.util.find_spec()` e fallback para `robot.libraries.<name>`.
- Resolução cross-file inicial cobre resources importados, suficiente para foundation de Stage 10+.
- Validação executada com `just test` e `uv run python -m compileall src tests`.
