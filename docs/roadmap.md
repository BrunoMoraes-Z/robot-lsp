# Roadmap

## Current Stage

**MVP Complete**
Status: `done`

## Verification Summary

As 14 etapas planejadas para o MVP foram implementadas e validadas pela suite atual.

Validação local mais recente:
- `uv run pytest` — 164 testes passando

Os itens abaixo não bloqueiam o MVP, mas seguem pendentes para evolução pós-MVP porque foram explicitamente adiados nos documentos de estágio/specs ou fazem parte de hardening de release além da primeira versão funcional.

## Post-MVP Pending Roadmap

| Order | Item | Source | Status |
|---|---|---|---|
| 01 | Executar matriz real de compatibilidade Robot Framework 7.x, não apenas a versão instalada | Stage 14 / compatibility matrix | done |
| 02 | Automatizar publicação/distribuição de release, incluindo build artifacts e PyPI se aplicável | Stage 14 | done |
| 03 | Implementar logging estruturado aplicado à configuração `robot.lsp.logLevel` em runtime | Stage 13 / Stage 14 | done |
| 04 | Aplicar `robot.lsp.completion.snippets` aos completion items e snippets configuráveis | Stage 13 | pending |
| 05 | Implementar request outbound `workspace/configuration` e configuração por workspace folder | Stage 13 / workspace configuration spec | pending |
| 06 | Adicionar worker pool/cancelamento real para operações longas quando houver métricas justificando | Stage 12 / performance specs | pending |
| 07 | Avaliar subprocess isolation para indexação/análise pesada com testes de integração dedicados | Stage 12 / Stage 14 risks | pending |
| 08 | Adicionar progress reporting (`$/progress`, `window/workDoneProgress/create`) para operações longas | protocol progress spec | pending |
| 09 | Expandir CI para novos targets quando necessário, como macOS e Python 3.13 | compatibility matrix | pending |
| 10 | Implementar diagnostics semânticos/warnings além dos erros de parse do Robot Framework | diagnostics rules spec | pending |

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
| 07 | Hover | done |
| 08 | Navigation | done |
| 09 | Workspace Index | done |
| 10 | Refactoring | done |
| 11 | Formatting & Code Actions | done |
| 12 | Performance & Isolation | done |
| 13 | Configuration | done |
| 14 | Release Hardening | done |

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
- Implementado `HoverService` em `src/robot_lsp/application/hover_service.py`
- Implementados tipos `MarkupContent`, `Hover` e `HoverContext`
- Implementado hover de keywords locais com assinatura, argumentos e documentação
- Implementado hover de variáveis locais com tipo e valor
- Implementado hover de imports com tipo, nome, alias e argumentos
- Integrado handler `textDocument/hover` ao `LspServer`
- Criados testes unitários para service e handler LSP

**Acceptance Criteria**
- ✅ Hover em keyword local retorna assinatura e documentação
- ✅ Hover em variável retorna tipo e valor
- ✅ Hover em import retorna tipo e caminho
- ✅ Retorno respeita `MarkupKind.Markdown`
- ✅ `null`/`None` se não encontrar nada no hover
- ✅ Range no hover cobre o símbolo sob o cursor

---

### Stage 08 — Navigation

**Expected**
- `textDocument/definition`
- `textDocument/references`
- `textDocument/documentSymbol`
- `textDocument/foldingRange`
- `textDocument/selectionRange`

**Done**
- Implementado `NavigationService` em `src/robot_lsp/application/navigation_service.py`
- Implementado `textDocument/definition` para symbols locais
- Implementado `textDocument/references` com suporte a `includeDeclaration`
- Implementado `textDocument/documentSymbol` para imports, variables, test cases e keywords
- Implementado `textDocument/foldingRange` para sections, test cases e keywords
- Implementado `textDocument/selectionRange` com range de símbolo e parent de linha
- Integradas capabilities de navigation no `initialize`
- Criados testes unitários para service e handlers LSP

**Acceptance Criteria**
- ✅ `definition` retorna localizações locais
- ✅ `references` retorna ocorrências locais e respeita `includeDeclaration`
- ✅ `documentSymbol` retorna estrutura do documento
- ✅ `foldingRange` retorna ranges dobráveis
- ✅ `selectionRange` retorna ranges por posição
- ✅ Handlers retornam listas vazias quando service/documento não existe

---

### Stage 09 — Workspace Index

**Expected**
- Indexação de arquivos `.robot` e `.resource` no workspace
- Resolução de imports (`Library`, `Resource`, `Variables`)
- Keywords de bibliotecas importadas
- Variáveis de resources importados
- Cache de workspace

**Done**
- Implementado `WorkspaceIndex` em `src/robot_lsp/application/workspace.py`
- Implementados `WorkspaceEntry`, `SymbolLocation` e `ImportResolution`
- Implementado scan de arquivos `.robot` e `.resource`
- Implementadas buscas `find_keyword` e `find_variable`
- Implementada resolução básica de imports `Resource`, `Variables` e `Library`
- Implementado cache simples por mtime + hash de conteúdo
- Integrado opcionalmente `WorkspaceIndex` ao `CompletionService`
- Integrado opcionalmente `WorkspaceIndex` ao `NavigationService`
- Criados testes de indexação, resolução e integração cross-file via resource

**Acceptance Criteria**
- ✅ Indexação de arquivos `.robot` e `.resource`
- ✅ Resolução básica de imports `Library`, `Resource`, `Variables`
- ✅ Keywords de resources importados ficam disponíveis para completion/definition
- ✅ Variáveis de resources importados ficam disponíveis para completion
- ✅ Cache em memória por mtime + hash de conteúdo

---

### Stage 10 — Refactoring

**Expected**
- `textDocument/rename`
- `textDocument/prepareRename`
- `workspace/workspaceEdit`

**Done**
- Implementado `RefactoringService` em `src/robot_lsp/application/refactoring_service.py`
- Implementado `textDocument/prepareRename`
- Implementado `textDocument/rename`
- Implementado `WorkspaceEdit` com `changes`
- Implementado rename local de variables, keywords e test cases
- Implementado rename textual em arquivos indexados quando `WorkspaceIndex` estiver disponível
- Adicionada capability `renameProvider` com `prepareProvider: true`
- Criados testes unitários para service e handlers LSP

**Acceptance Criteria**
- ✅ `prepareRename` retorna range e placeholder
- ✅ `prepareRename` retorna `null` para símbolo desconhecido
- ✅ `rename` retorna `WorkspaceEdit`
- ✅ Rename local altera ocorrências do documento aberto
- ✅ Rename com `WorkspaceIndex` inclui arquivos indexados
- ✅ Handler retorna `null` quando service não está configurado

---

### Stage 11 — Formatting & Code Actions

**Expected**
- `textDocument/formatting`
- `textDocument/rangeFormatting`
- `textDocument/codeAction`
- Quick fixes para diagnostics comuns

**Done**
- Implementado `FormattingService` em `src/robot_lsp/application/formatting_service.py`
- Implementado `textDocument/formatting`
- Implementado `textDocument/rangeFormatting`
- Implementada normalização inicial de espaçamento entre células para 4 espaços
- Implementada remoção de whitespace final por linha
- Implementado `CodeActionService` em `src/robot_lsp/application/code_action_service.py`
- Implementado `textDocument/codeAction`
- Adicionadas capabilities `documentFormattingProvider`, `documentRangeFormattingProvider` e `codeActionProvider`
- Criados testes unitários para services e handlers LSP

**Acceptance Criteria**
- ✅ `textDocument/formatting` retorna `TextEdit` de documento inteiro quando há mudanças
- ✅ `textDocument/formatting` retorna lista vazia quando documento já está formatado
- ✅ `textDocument/rangeFormatting` formata linhas tocadas pelo range
- ✅ `textDocument/codeAction` retorna quick actions para diagnostics conhecidos
- ✅ Capabilities de formatting e code action são anunciadas no `initialize`
- ✅ Handlers retornam lista vazia quando services não estão configurados

---

### Stage 12 — Performance & Isolation

**Expected**
- Cache de parse de AST
- Cache de análise de workspace
- Cancelamento real de requests longos
- Worker pool para operações pesadas
- Subprocesso isolado para indexação (se necessário)

**Done**
- Implementado cache LRU de parse em `ParseService`
- Cache de parse usa URI, versão do documento e SHA-256 do texto
- Cache é reaproveitado por diagnostics, completion, hover, navigation e refactoring via `ParseService`
- Adicionados métodos `clear_uri` e `clear` para invalidação explícita
- Adicionado limite configurável `max_cache_entries`, padrão 50
- Mantido cache de workspace já implementado por mtime + hash de conteúdo
- Worker pool e subprocesso permanecem fora do MVP até métricas justificarem a complexidade

**Acceptance Criteria**
- ✅ Documento inalterado não é parseado novamente
- ✅ Mudança de texto invalida cache
- ✅ Mudança de versão invalida cache
- ✅ Cache respeita limite LRU configurável
- ✅ Cache pode ser invalidado por URI
- ✅ Workspace index mantém cache por mtime + hash
- ✅ Subprocess isolation documentado como futuro, não necessário no MVP atual

---

### Stage 13 — Configuration

**Expected**
- `workspace/configuration`
- Configurações do LSP (feature flags, caminhos de import)
- Configuração por workspace folder
- `didChangeConfiguration`

**Done**
- Implementado `ConfigurationService` em `src/robot_lsp/application/configuration.py`
- Implementado modelo `ServerConfig` com `importPaths`, `logLevel`, `diagnostics.enable` e `completion.snippets`
- Implementado suporte a `initializationOptions`
- Implementado handler `workspace/didChangeConfiguration`
- Adicionada capability `workspace.didChangeConfiguration`
- Integrado `diagnostics.enable` ao agendamento de diagnostics
- Desabilitar diagnostics limpa diagnostics publicados de documentos abertos
- Integrado `robot.lsp.importPaths` à resolução de imports de arquivos no `WorkspaceIndex`
- Criados testes unitários para config service, handler LSP e import paths

**Acceptance Criteria**
- ✅ Defaults funcionam sem configuração
- ✅ `initializationOptions` aplica configurações iniciais
- ✅ `workspace/didChangeConfiguration` atualiza configurações em runtime
- ✅ Diagnostics podem ser desabilitados por configuração
- ✅ Desabilitar diagnostics limpa diagnostics existentes
- ✅ `robot.lsp.importPaths` participa da resolução de `Resource` e `Variables`
- ✅ Valores inválidos são ignorados sem quebrar configuração existente
- ✅ `workspace/configuration` permanece como futuro server-to-client quando existir loop de request outbound

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

**Done**
- Implementado runner stdio real em `src/robot_lsp/main.py`
- Implementada fábrica `create_server()` com todos os services do MVP conectados
- Implementado `--version`
- Implementado `--log-level` com logs em stderr
- Protocol errors no loop stdio retornam JSON-RPC error response
- Notifications pendentes são drenadas pelo runner
- Diagnostics assíncronos podem publicar diretamente no transporte do runner
- Adicionado workflow CI em `.github/workflows/ci.yml`
- Adicionado `README.md`
- Adicionado `docs/usage.md`
- Adicionado `docs/changelog.md`
- Atualizada matriz de compatibilidade com targets e validação local

**Acceptance Criteria**
- ✅ `python -m robot_lsp --version` retorna versão
- ✅ Runner stdio responde sessão mínima LSP
- ✅ Runner stdio retorna erro JSON-RPC para mensagem inválida
- ✅ Logs usam stderr, preservando stdout para LSP
- ✅ CI pipeline documentado em GitHub Actions
- ✅ Documentação de uso e changelog inicial existem
- ✅ Testes e compileall passam
