# Roadmap

## Current Stage

**Stage 07 — Hover**
Status: `planned`

---

## Stage Status

| Stage | Name | Status |
|---|---|---|
| 00 | Foundation | done |
| 01 | JSON-RPC | done |
| 02 | LSP Lifecycle | done |
| 03 | Document Workspace | done |
| 04 | Robot Framework Model | done |
| 05 | Diagnostics | done |
| 06 | Completion | done |
| 07 | Hover | planned |
| 08 | Navigation | planned |
| 09 | Workspace Index | planned |
| 10 | Refactoring | planned |
| 11 | Formatting & Code Actions | planned |
| 12 | Performance & Isolation | planned |
| 13 | Configuration | planned |
| 14 | Release Hardening | planned |

---

## Stage Details

### Stage 00 — Foundation

**Expected**
- Criar projeto com `uv`
- Definir estrutura de pacotes (Clean Architecture)
- Criar `justfile` com PowerShell
- Criar arquitetura inicial de diretórios
- Criar documentação base (`docs/`, ADRs, stages, specs)
- Configurar `pytest`
- Entrypoint vazio `python -m robot_lsp`

**Done**
- Projeto criado com `uv`
- Estrutura de diretórios Clean Architecture estabelecida
- `pyproject.toml` configurado com dependências e build-system
- `justfile` funcional com PowerShell
- `docs/` completo: roadmap, architecture, ADRs, stages (00-07), specs (protocolo, text-document, RF, testing, performance)
- Entrypoint `python -m robot_lsp` funcional
- Teste de importação de todos os módulos passando
- `pytest` configurado
- `.gitignore` criado

**Acceptance Criteria**
- ✅ `uv run pytest` executa e passa
- ✅ `just test` executa e passa
- ✅ Estrutura `src/robot_lsp/` existe com as camadas `domain/`, `application/`, `infrastructure/`, `protocol/`, `adapters/`
- ✅ Estrutura `tests/` existe com `unit/` e `integration/`
- ✅ `python -m robot_lsp` executa sem erro
- ✅ `docs/` está preenchido com roadmap, architecture, ADRs, stages e specs
- ✅ `just test` executa `uv run pytest`
- ✅ `uv run python -m robot_lsp` imprime info no stderr

---

### Stage 01 — JSON-RPC

**Expected**
- Implementar JSON-RPC 2.0: request, response, notification, error
- Implementar LSP framing (`Content-Length`)
- Implementar reader/writer sobre `stdio`
- Implementar dispatch de métodos
- Suporte a `$/cancelRequest`
- Testes unitários de framing e mensagens

**Done**
- Implementado parser/serializer JSON-RPC 2.0 em `src/robot_lsp/protocol/jsonrpc.py`
- Implementados modelos `JsonRpcMessage`, `JsonRpcError` e erro de protocolo `JsonRpcProtocolError`
- Implementados helpers para request, notification, response e error response
- Implementados error codes padrão JSON-RPC e códigos LSP internos iniciais
- Implementado framing LSP `Content-Length` em `src/robot_lsp/protocol/transport_stdio.py`
- Implementado reader/writer binário com escrita thread-safe
- Implementado `MethodDispatcher` em `src/robot_lsp/protocol/dispatch.py`
- Implementado cancelamento cooperativo via `$/cancelRequest`
- Criados testes unitários para JSON-RPC, transporte e dispatcher

**Acceptance Criteria**
- ✅ Requests, notifications e responses serializam/deserializam corretamente
- ✅ Erros padrão JSON-RPC são emitidos para mensagens inválidas
- ✅ `Content-Length` header é lido/escrito corretamente
- ✅ Mensagens maiores que buffer são lidas corretamente
- ✅ Cancelamento de request funciona

---

### Stage 02 — LSP Lifecycle

**Expected**
- `initialize`
- `initialized`
- `shutdown`
- `exit`
- Estados do servidor (uninitialized, running, shuttingDown, exited)
- Capabilities mínimas (textDocumentSync, completionProvider, hoverProvider)
- Testes de sessão LSP mínima via transporte em memória

**Done**
- Implementado `LspServer` em `src/robot_lsp/protocol/server.py`
- Implementados estados `uninitialized`, `running`, `shuttingDown`, `exited`
- Implementados handlers `initialize`, `initialized`, `shutdown`, `exit`
- Implementada validação de mensagens antes de `initialize` com erro `-32002`
- Implementada validação de requests após `shutdown` com erro `-32003`
- Implementado `serverInfo` com nome e versão do servidor
- Implementadas capabilities iniciais em `src/robot_lsp/protocol/lsp_types.py`
- Criados testes unitários de lifecycle em `tests/unit/protocol/test_server.py`

**Acceptance Criteria**
- ✅ Servidor responde `initialize` com capabilities corretas
- ✅ `initialized` é aceito como notification
- ✅ `shutdown` + `exit` encerra servidor
- ✅ Mensagens antes de `initialize` são rejeitadas
- ✅ Mensagens depois de `shutdown` são rejeitadas

---

### Stage 03 — Document & Workspace

**Expected**
- `textDocument/didOpen`
- `textDocument/didChange` (sync full)
- `textDocument/didClose`
- `DocumentStore`: gerencia documentos abertos
- URI/path helpers
- Conversão de posições LSP (UTF-16 code units)
- Ranges: 0-based line, 0-based UTF-16 column

**Done**
- Corrigido e completado `DocumentStore` em `src/robot_lsp/application/document_store.py`
- Implementado `Document` com `lines` e extração de texto por `LspRange`
- Implementados helpers `uri_to_path` e `path_to_uri`
- Aprimorada conversão UTF-16 em `src/robot_lsp/domain/positions.py`
- Implementado `range_text` para extração por ranges LSP
- Implementados handlers `textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose` no `LspServer`
- Criados testes de `DocumentStore`, URI/path, posições UTF-16 e document sync

**Acceptance Criteria**
- ✅ Documento aberto via `didOpen` fica disponível no `DocumentStore`
- ✅ `didChange` com texto completo substitui conteúdo
- ✅ `didClose` remove documento
- ✅ Conversões UTF-16 funcionam com caracteres multi-byte (acentos, emoji)
- ✅ URI `file://` é convertida para path do sistema
- ✅ `LspRange` calcula texto de um range corretamente

---

### Stage 04 — Robot Framework Model

**Expected**
- Detector de versão do Robot Framework (`robot.version.VERSION`)
- `FeatureSet` com capacidades baseadas na versão
- Parser usando exclusivamente `robot.api.parsing`
- Modelo intermediário próprio (desacoplado do AST do RF)
- Adapter que mapeia AST do RF para modelo intermediário
- Fixtures `.robot` para testes

**Done**
- Implementados modelos intermediários faltantes: `RobotDocument`, `RobotDiagnostic`, `ParseResult`
- Implementado detector de versão em `src/robot_lsp/infrastructure/robotframework/version.py`
- Implementado `FeatureSet` para RF >= 7.0 com flags `has_group` e `has_secret_variables`
- Implementado parser em `src/robot_lsp/infrastructure/robotframework/parser.py` usando apenas `robot.api.parsing`
- Implementado adapter AST em `src/robot_lsp/infrastructure/robotframework/adapter.py`
- Implementado visitor de coleta de erros em `visitors.py`
- Extraídos settings, metadata, imports, variables, test cases, keywords, args e steps
- Criadas fixtures `.robot` e `.resource` reais em `tests/integration/fixtures/`
- Criados testes de versão, parser, adapter e isolamento de imports do RF

**Acceptance Criteria**
- ✅ Versão 7.0+ é detectada e reportada corretamente
- ✅ `FeatureSet` reflete a versão instalada
- ✅ Suite `.robot` é parseada para modelo intermediário
- ✅ Core do LSP nunca importa `robot.api.parsing` nem `robot.parsing` diretamente
- ✅ Erros de parse do RF são capturados sem crash
- ✅ Testes com fixtures reais `.robot`

---

### Stage 05 — Diagnostics

**Expected**
- Diagnostics de parse/sintaxe via Robot Framework
- `textDocument/publishDiagnostics` notificação
- Debounce de diagnostics (ex: 300ms)
- Cancelamento de diagnóstico pendente por URI
- Conversão de ranges RF (1-based) → LSP (0-based)
- Fallback para linha inteira quando range não está disponível

**Done**
- Implementado `ParseService` em `src/robot_lsp/application/parse_service.py`
- Implementado `DiagnosticService` em `src/robot_lsp/application/diagnostic_service.py`
- Implementada serialização LSP de `LspDiagnostic` em `domain/diagnostics.py`
- Integrado `DiagnosticService` ao `LspServer` via injeção opcional
- Implementado `textDocument/publishDiagnostics` como notification de saída
- `didOpen` e `didChange` agendam diagnostics com debounce
- `didClose` limpa diagnostics e cancela timers pendentes
- Implementado cancelamento de diagnostic pendente por URI
- Implementada deduplicação para não publicar diagnostics idênticos
- Criados testes unitários para parse diagnostics, clear, debounce, cancel, publication e ranges

**Acceptance Criteria**
- ✅ Documento inválido dispara `publishDiagnostics`
- ✅ Documento corrigido limpa diagnostics
- ✅ Debounce evita flood em digitação rápida
- ✅ Diagnostics cancelados não são publicados
- ✅ Parsing não quebra servidor em caso de erro grave
- ✅ Severidade correta: error para parse error

---

### Stage 06 — Completion

**Expected**
- Completar sections (`*** Settings ***`, etc.)
- Completar settings (`Library`, `Resource`, `Suite Setup`, etc.)
- Completar keywords locais (mesmo arquivo)
- Completar variables locais
- `InsertTextFormat.PlainText` e `Snippet` simples

**Done**
- Implementado `CompletionService` em `src/robot_lsp/application/completion_service.py`
- Implementados tipos `CompletionItem`, `CompletionList`, `CompletionContext` e `CompletionItemKind`
- Implementada completion de sections
- Implementada completion de settings em `*** Settings ***`
- Implementada completion de keywords locais em bodies de test cases/keywords
- Implementada completion de variables locais com triggers `$`, `@`, `&`, `%`
- Integrado handler `textDocument/completion` ao `LspServer`
- Criados testes unitários para service e handler LSP

**Acceptance Criteria**
- ✅ Cursor após linha vazia completa sections
- ✅ Cursor em `*** Settings ***` completa settings conhecidos
- ✅ Cursor em `*** Keywords ***` completa keywords do arquivo
- ✅ Cursor onde variável é esperada completa variáveis do arquivo
- ✅ Completion items têm label, kind, detail e documentation quando aplicável

---

### Stage 07 — Hover

**Expected**
- Hover em keyword local (mostra docstring/args)
- Hover em variable local (mostra tipo e valor)
- Hover em import (mostra tipo do import)
- Formatação Markdown
- Range do símbolo sob o cursor

**Done**
- _Nothing yet_

**Acceptance Criteria**
- Hover em keyword local retorna assinatura e documentação
- Hover em variável retorna tipo e valor
- Hover em import retorna tipo e caminho
- Retorno respeita `MarkupKind.Markdown`
- `null`/`None` se não encontrar nada no hover

---

### Stage 08 — Navigation

**Expected**
- `textDocument/definition`
- `textDocument/references`
- `textDocument/documentSymbol`
- `textDocument/foldingRange`
- `textDocument/selectionRange`

**Status:** planned

---

### Stage 09 — Workspace Index

**Expected**
- Indexação de arquivos `.robot` e `.resource` no workspace
- Resolução de imports (`Library`, `Resource`, `Variables`)
- Keywords de bibliotecas importadas
- Variáveis de resources importados
- Cache de workspace

**Status:** planned

---

### Stage 10 — Refactoring

**Expected**
- `textDocument/rename`
- `textDocument/prepareRename`
- `workspace/workspaceEdit`

**Status:** planned

---

### Stage 11 — Formatting & Code Actions

**Expected**
- `textDocument/formatting`
- `textDocument/rangeFormatting`
- `textDocument/codeAction`
- Quick fixes para diagnostics comuns

**Status:** planned

---

### Stage 12 — Performance & Isolation

**Expected**
- Cache de parse de AST
- Cache de análise de workspace
- Cancelamento real de requests longos
- Worker pool para operações pesadas
- Subprocesso isolado para indexação (se necessário)

**Status:** planned

---

### Stage 13 — Configuration

**Expected**
- `workspace/configuration`
- Configurações do LSP (feature flags, caminhos de import)
- Configuração por workspace folder
- `didChangeConfiguration`

**Status:** planned

---

### Stage 14 — Release Hardening

**Expected**
- Matriz de compatibilidade RF 7.x
- CI pipeline
- Packaging e distribuição
- Logging estruturado
- Tracing para diagnóstico
- Documentação de uso
- Changelog

**Status:** planned
