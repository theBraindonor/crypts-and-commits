---
archived: false
campaign: c006-applicable-lore-mcp-paging
created_by: John Hoff
created_on: '2026-11-21T17:28:24Z'
depends_on: []
kind: scripted
name: e002-demo-api-literal-priming
regions:
- demo-api
status: completed
updated_by: John Hoff
updated_on: '2026-11-23T17:31:08Z'
---

## Requirements

Per ruling c006-e001-demo-api-brace-fix-as-e002:

1. `packages/demo-api/src/demo_api/chat/graph.py::_build_prompt` passes the context priming text to the chat model literally. Braces or other template syntax in sourcebook content (campaign bodies, world body, lore and region summaries) are never parsed as `ChatPromptTemplate` variables.
2. The prompt order stays persona (`SYSTEM_PROMPT`), then priming, then the `messages` placeholder, and the existing `test_prompt_orders_persona_then_priming_then_messages` keeps passing unchanged.
3. A regression test in `packages/demo-api/tests/test_graph.py` builds the prompt from priming text containing braces (e.g. `"Returns {items, next_cursor} and {name}"`) and asserts the formatted system message content equals that text exactly, with no missing-variable error.
4. `render_context_priming` (`packages/demo-api/src/demo_api/chat/priming.py`), the tools, and every other behavior are unchanged. demo-api still only reads the sourcebook through `cac.core`, and nothing writes to it.
5. The 4 currently failing chat tests in `packages/demo-api/tests/test_chat.py` (`test_chat_streams_multiple_chunks`, `test_chat_generates_thread_id_when_omitted`, `test_chat_reused_thread_id_continues_conversation`, `test_chat_new_thread_id_starts_fresh`), which build the graph from this repo's live priming, pass.

## Rationale

`_build_prompt` passes `("system", priming)` to `ChatPromptTemplate.from_messages`, which treats the string as an f-string template. `render_context_priming(REPO_ROOT)` includes the active campaign's body, and c006's body contains `{items, next_cursor}`, so building the prompt fails with `ChatPromptTemplate is missing variables {'items, next_cursor'}`. Any brace in sourcebook content would do the same; this predates c006. Priming is data, not a template, so it should be a literal message. The fix belongs in demo-api, not in the sourcebook text.

## Plan

1. Add the regression test (Requirement 3) to `tests/test_graph.py` and confirm it fails with the missing-variables error before step 2.
2. In `graph.py`, build the priming entry as a literal `langchain_core.messages.SystemMessage(content=priming)` inside `ChatPromptTemplate.from_messages`, which LangChain does not template. Do the same for `SYSTEM_PROMPT` so neither system message is templated. Keep the `MessagesPlaceholder("messages")` last.
3. Run `pdm run pytest -q packages/demo-api` to confirm the regression test, the prompt-order test and the 4 chat tests pass.
4. Run the full suite and ruff.

## Verification

- The regression test fails before step 2 and passes after it.
- `test_prompt_orders_persona_then_priming_then_messages` passes unchanged.
- The 4 listed chat tests pass against this repo's live priming while c006 (whose body contains braces) is the active campaign.
- `git diff` touches only `packages/demo-api/src/demo_api/chat/graph.py` and `packages/demo-api/tests/test_graph.py`.
- Per `clean-tests-and-lint`: `pdm run pytest -q` passes in full, `pdm run ruff check .` reports zero errors, and `pdm run ruff format .` produces no diffs.

## Log

### Review - 2026-11-23T17:00:25Z - John Hoff

Independent review PASS-WITH-NOTES against clean-tests-and-lint and demo-api-uses-cac-core-directly. The plan honors clean-tests-and-lint: a failing regression test is written first, the existing prompt-order test passes unchanged, the full `pdm run pytest -q` must pass, and ruff check/format must be clean, with no skips or suppressions. It honors demo-api-uses-cac-core-directly: the change is limited to how `_build_prompt` builds the prompt, `render_context_priming` and the tools are unchanged, demo-api still reads only through cac.core, and there are no writes, CLI or MCP calls. The diagnosis matches the current code (tuple system entries are f-string templated), and literal `SystemMessage` entries in `ChatPromptTemplate.from_messages` are the right fix. Notes: (1) the cited ruling c006-e001-demo-api-brace-fix-as-e002 was outside the review surface and not checked; (2) whether the 4 `test_chat.py` tests really use live priming depends on the uncited `fake_graph` fixture; (3) the 'git diff touches only graph.py and test_graph.py' check must be scoped to this encounter's own changes, since the branch has unrelated uncommitted work; (4) the live-priming coverage in Requirement 5 is temporary while c006 is active, so the Requirement 3 unit test is the lasting guard.

### Message - 2026-11-23T17:05:20Z - John Hoff

Developer-approved clarification of review note 3: the Verification check "`git diff` touches only graph.py and test_graph.py" is scoped to e002's own changes. Within packages/demo-api, only `src/demo_api/chat/graph.py` and `tests/test_graph.py` change, apart from the uncommitted `packages/demo-api/pyproject.toml` version bump that belongs to e001. e001's uncommitted work elsewhere on the branch is excluded. Per review note 2, the `fake_graph` fixture will be checked during execution to confirm the 4 chat tests exercise live priming; any gap will be logged as a deviation.

### Opened - 2026-11-23T17:05:20Z - John Hoff

Opened with developer approval.

### Message - 2026-11-23T17:13:16Z - John Hoff

Implementation done and verified. Review note 2 resolved: the 4 test_chat.py tests call fake_graph with priming=None and root=None, so build_graph uses render_context_priming(REPO_ROOT), the live priming. Step 1: test_prompt_passes_priming_with_braces_literally was added to tests/test_graph.py and failed before the fix with KeyError 'items, next_cursor' from LangChain's template formatter. Step 2: _build_prompt now passes SystemMessage(content=SYSTEM_PROMPT) and SystemMessage(content=priming) literally, with MessagesPlaceholder("messages") still last. Results: demo-api 33 passed; the full suite `pdm run pytest -q` reports 1743 passed and 0 failed (previously 4 failed); `ruff check .` passes and `ruff format --check .` reports no changes. Scoped diff check (ruling c006-e002-diff-check-scoped-to-encounter): packages/demo-api changes only graph.py and test_graph.py, plus e001's pyproject.toml bump.

### Completed - 2026-11-23T17:31:08Z - John Hoff

Completed with developer confirmation. Every Verification item passed: the regression test failed before the fix and passes after it; the prompt-order test is unchanged and passes; the 4 chat tests pass against live priming; the scoped diff check holds; and the full suite (1743 passed) and ruff are clean.
