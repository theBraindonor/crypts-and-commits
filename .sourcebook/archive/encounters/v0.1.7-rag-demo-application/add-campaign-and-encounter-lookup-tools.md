---
archived: true
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-06T17:09:10Z'
depends_on:
- add-chat-persona-and-context-priming
name: add-campaign-and-encounter-lookup-tools
regions:
- demo-api
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T14:09:04Z'
---

## Requirements

- The demo-api chat agent must be able to call tools that get and list encounters, and get and list campaigns, backed directly by `cac.core.encounter` / `cac.core.campaign` — never a `cac` CLI subprocess or the MCP server (per the `demo-api-uses-cac-core-directly` region lore).
- Tools stay strictly read-only against `.sourcebook`: only the existing non-mutating `core` functions (`list_encounters`, `read_encounter`, `list_campaigns_with_status`, `read_campaign`) are exposed; no mutating call is wrapped.
- The tool structure must make adding a future domain's tools (e.g. lore, region, world) a small, isolated addition - a new module plus one line registering it - not a change to existing tool modules or to the LangGraph wiring in `graph.py`.
- The LangGraph agent must actually execute tool calls in a loop (bind tools to the model, route a model's tool call to execution, feed the result back to the model for a final answer), not just expose schemas nothing invokes.
- Existing chat behavior (streaming, multi-turn persistence via the SQLite checkpointer, context priming) keeps working unchanged.

## Rationale

`add-chat-persona-and-context-priming` already established that `demo-api` depends on `crypts-and-commits` and reads `.sourcebook` content by calling straight into `cac.core.prime` in-process (`demo_api/chat/priming.py`), per the `demo-api-uses-cac-core-directly` lore. That lore explicitly extends to "any `demo-api` functionality that reads `.sourcebook` content" and calls out read-only access as a hard constraint - this encounter is the first case beyond the initial priming read, so it's the first real test of that lore holding up for a second, differently-shaped feature (on-demand tool calls instead of one priming string built at graph-build time).

Encounters and campaigns are the natural starting domain: they're the active work-tracking loop the user most wants the agent to be able to answer live questions about (e.g. "what's the status of X"), and `cac.core.campaign`/`cac.core.encounter` already expose plain, dataclass-returning read functions with no I/O beyond the filesystem, so wrapping them needs no new abstraction in `core` itself.

Structuring tools as one module per domain, each exporting a `build_tools(root) -> list[BaseTool]` factory aggregated by a top-level `demo_api/chat/tools/__init__.py`, mirrors the project's own architecture rule (thin wrappers composed over focused modules) and satisfies the user's explicit ask that the design make adding more tool calls easy later. A factory taking `root` (rather than each tool closing over the module-level `REPO_ROOT` constant directly) mirrors the existing `render_context_priming(root)` pattern and keeps the tools testable against a `tmp_path` sourcebook instead of this repository's real one.

LangGraph's prebuilt `ToolNode` + `tools_condition` (already available in the pinned `langgraph>=1.2.10`) is the standard, minimal way to wire a tool-execution loop onto a `StateGraph`, and `ToolNode` catches tool-function exceptions by default (returning them to the model as an error `ToolMessage` instead of crashing the graph) - so tool functions can let `cac.core`'s existing exceptions (`EncounterNotFoundError`, `NoActiveCampaignError`, etc.) propagate unchanged rather than adding a bespoke translation layer.

## Plan

1. Add `packages/demo-api/src/demo_api/chat/tools/` as a new package:
   - `encounters.py`: `build_tools(root: Path) -> list[BaseTool]` returning two `@tool`-wrapped closures over `root`:
     - `list_encounters(campaign: str | None = None)` - resolves the campaign via `cac.core.campaign.resolve_campaign(root, campaign, require_mutable=False)` (defaults to the active/open campaign when omitted) and returns `cac.core.encounter.list_encounters(root, resolved)`.
     - `get_encounter(name: str, campaign: str | None = None)` - same campaign resolution, then `cac.core.encounter.read_encounter(root, resolved, name)`, returned as a plain JSON-serializable dict (`name`, `campaign`, `status`, `regions`, `depends_on`, `body`) since tool results must serialize, unlike the `Encounter` dataclass.
     Each closure's docstring is its tool description; the campaign parameter's default-to-active behavior is described there for the model.
   - `campaigns.py`: same shape - `build_tools(root: Path) -> list[BaseTool]` with `list_campaigns()` (wraps `cac.core.campaign.list_campaigns_with_status`, returns `[{"name", "status"}, ...]`) and `get_campaign(name: str)` (wraps `read_campaign`, returns a dict of `name`/`status`/`body`).
   - `__init__.py`: `build_tools(root: Path) -> list[BaseTool]` concatenating every registered domain module's `build_tools(root)` from one private list - the single place a future domain module gets wired in.
2. Update `packages/demo-api/src/demo_api/chat/graph.py`:
   - `_chat_node` gains a `tools: Sequence[BaseTool]` parameter and calls `model.bind_tools(tools)` before building the chain.
   - `build_graph` gains a `root: Path | None = None` parameter (mirrors the existing `priming` override), defaulting to `REPO_ROOT`; builds `tools = tools_pkg.build_tools(resolved_root)`, adds a `ToolNode(tools)` node named `"tools"`, and wires `add_conditional_edges("chat", tools_condition)` plus `add_edge("tools", "chat")` so a tool-calling response routes to execution and back into another model turn, while a plain text response still routes straight to `END`.
   - Extend `SYSTEM_PROMPT` with one sentence noting that live campaign/encounter lookup tools are available and should be preferred over guessing when asked about current status.
3. Tests:
   - `packages/demo-api/tests/test_tools.py`: build a temp sourcebook under `tmp_path` using `cac.core.campaign.create_campaign`/`open_campaign` and `cac.core.encounter.create_encounter` (plus region assignment/review where a transition requires it), call each domain's `build_tools(tmp_path)`, and invoke the resulting tools directly (`.invoke(...)`) to assert: list/get results match what was written, omitting `campaign` resolves to the active campaign, and a nonexistent name/campaign raises the underlying `cac.core` exception unchanged (not swallowed or wrapped).
   - `packages/demo-api/tests/conftest.py` (new): a `_FakeToolCallingModel(GenericFakeChatModel)` overriding `bind_tools` to return `self` (the stock `GenericFakeChatModel.bind_tools` raises `NotImplementedError`, since `BaseChatModel`'s default is abstract), plus a shared `fake_graph(*replies, root=None)` helper; update `test_chat.py` and `test_graph.py`'s existing local `_fake_graph` helpers to use it instead of duplicating the fake model.
   - `packages/demo-api/tests/test_graph.py`: add a test driving a full tool-calling round trip - the fake model's first reply is an `AIMessage` with a `tool_calls` entry naming one of the new tools, the graph executes it via `ToolNode` against a `tmp_path` sourcebook (passed as `root`), and the fake model's second reply is the final text - asserting the final state's last message content and that a `ToolMessage` for the tool call appears in `state.values["messages"]`.

## Verification

- `pdm run pytest packages/demo-api -q` and the full `pdm run pytest -q` both pass.
- `pdm run ruff check .` reports zero errors and `pdm run ruff format .` reports no diffs.
- Manually start the demo-api server and send a `/chat` message that requires a live lookup (e.g. asking about the status of an open encounter) to confirm a real tool-call round trip end-to-end; treat this as best-effort given this region's noted OpenRouter free-tier rate-limit flakiness, not a hard blocker if the model backend itself is unavailable.

## Log

### Review - 2026-08-06T17:42:30Z - John Hoff

Reviewed against the two applicable lore items (clean-tests-and-lint, demo-api-uses-cac-core-directly) and both are honored: the Plan wraps only the four named non-mutating cac.core.campaign/cac.core.encounter functions directly (no CLI subprocess, no MCP), all five referenced functions/signatures (list_encounters, read_encounter, list_campaigns_with_status, read_campaign, resolve_campaign) were confirmed to exist as described in core/campaign.py and core/encounter.py, and the Verification section correctly gates on pdm run pytest -q plus ruff check/format. The proposed graph.py changes (adding tools/root params) are consistent with the file's current shape and mirror its existing priming-override pattern. Two non-blocking risk notes for implementation time, not lore violations: the claimed default exception-catching behavior of LangGraph's ToolNode and the claimed need to override GenericFakeChatModel.bind_tools are third-party-library assumptions that weren't independently verified in this review and are worth a quick sanity check once coding starts.

### Completed - 2026-08-06T17:54:42Z - John Hoff

Implemented and verified: demo_api/chat/tools/ (campaigns.py, encounters.py, __init__.py) wraps cac.core.campaign/cac.core.encounter read-only functions as LangChain tools; graph.py wires a real tool-calling loop via ToolNode + tools_condition and gained a root override param; new tests/conftest.py FakeToolCallingModel + fake_graph fixture, tests/test_tools.py, and a tool-call round-trip test in test_graph.py. Full suite (783 tests) passes, ruff clean, and a live /chat smoke test against a running server confirmed the agent correctly reported this encounter's real-time status via the new tools.
