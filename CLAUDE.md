<!-- ecip-local-auto -->
## ECIP Local — Code Intelligence (auto-generated)

This workspace is fully indexed by ECIP Local. Every source file has been parsed
into an AST, chunked, and stored with symbol metadata. An MCP server is running
locally and provides 7 tools for code understanding.

**Prefer ECIP MCP tools over native file search/grep/read for all code exploration.**
They are faster and more accurate because they operate on pre-indexed AST data with
symbol-level granularity.

### Recommended workflow
1. `list_namespaces` — get the namespace string for this repo
2. `search_symbols` — find functions, classes, types by name pattern
3. `resolve_symbol` — get full details (docstring, type signature, source snippet)
4. `semantic_search` — natural language queries ("auth middleware", "database setup")
5. `find_references` — trace call sites of a symbol
6. `get_file_context` — see all symbols and chunks in a specific file
7. `get_dependencies` — check package manifest dependencies

### When to fall back to native tools
- Editing files (MCP tools are read-only)
- Git operations (commits, diffs, branches)
- Running tests or build commands
- Files that were just created and not yet indexed (trigger reindex first)
