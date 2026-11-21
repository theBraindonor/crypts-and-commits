---
archived: false
campaign: c002-rulings
created_by: John Hoff
created_on: '2026-11-21T00:36:37Z'
depends_on: []
kind: scripted
name: e001-ruling-records-core
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-11-21T02:16:00Z'
---

## Requirements

Implement the core ruling record type from `b005-ruling-records`, with its CLI and MCP surfaces and the owning docs.

- **Storage.** Live rulings are stored in `.sourcebook/rulings/<name>.md` and archived ones in `.sourcebook/archive/rulings/<name>.md`. Each file holds YAML frontmatter plus a markdown body, like rumors.
- **Naming.** Ruling names are literal canonical names of the form `cNNN-eNNN-slug`:
  - `cNNN` must resolve, through `references.Inventory`, to an existing numbered campaign, and that campaign must have status `open`. A reactivated campaign is `open` and qualifies. `draft`, `paused`, `completed` and `abandoned` campaigns are refused.
  - `eNNN` is either `e000`, meaning a campaign-level decision with no encounter, or it must resolve to an existing encounter in that campaign. The encounter may be in any status.
  - `slug` is a non-empty run of `NAME_PATTERN` characters.
  - The full name must be unused among all live and archived rulings.
  - Rulings get no numeric short references and no renumber operation.
- **Frontmatter.**
  - `name` and `status`
  - `archived`, a strict bool that must match the record's location
  - `campaign`, the canonical campaign name
  - `encounter`, the canonical encounter name, or null for `e000`
  - `summary`, required, at most 500 characters
  - `origin`, required free text
  - `resolution`, the latest disposition narrative, or null while `recorded`
  - `history`, a list of `{action, message, by, on}` entries
  - the standard `created_*` and `updated_*` stamps
- **Body.** It comes from a packaged `templates/sourcebook/ruling.md` with `## Decision`, `## Context` and `## Consequences` headings.
- **Lifecycle** (`RULING_STATUSES = ("recorded", "canonized", "noted")`):
  - `create`: the campaign and encounter checks above apply only here. The new ruling is `recorded`.
  - `update`: replaces body, summary and origin together. Allowed only for unarchived `recorded` rulings, and does not re-check the campaign status.
  - `canonize(message)`: `recorded` → `canonized`. Requires a non-blank narrative of how the world (lore, regions, world summary) was updated. The narrative is stored as `resolution` and appended to `history`.
  - `note(message)`: `recorded` → `noted`. Requires a non-blank narrative of why the ruling needs no lore, stored the same way.
  - `reopen(message)`: unarchived `canonized` or `noted` → `recorded`. Requires a reason, clears `resolution`, and appends to `history`.
  - `archive`: unarchived `canonized` or `noted` only. Moves the record to `archive/rulings/` under `Recovery`. It does not depend on campaign archival, and campaign archival does not touch rulings.
  - There is no delete.
  - `list` supports `include_archived` and a `status` filter. It refuses live/archive name overlap.
  - `get` returns metadata, summary and a budgeted body.
- **Interfaces.**
  - CLI: `cac ruling list|get|create|update|canonize|note|reopen|archive`, wired into `cli/app.py`.
  - MCP: matching `ruling_list`, `ruling_get`, `ruling_create`, `ruling_update`, `ruling_canonize`, `ruling_note`, `ruling_reopen` and `ruling_archive` tools, wired into `mcp/server.py`'s `_TOOL_MODULES`.
  - Both share cursor paging, `get`-body continuation and identity metadata.
- **Docs, in the same change:**
  - `templates/docs/workflow.md`: the ruling domain model, naming, capture guard, lifecycle, archival independence, and the absence of formal lore links.
  - `templates/docs/tool-reference.md`: every `ruling_*` tool and `cac ruling` command, with arguments, results, identity shape and errors.

## Rationale

Rulings are b005's foundation, and every later c002 encounter builds on this record type. Modeling them on `core/rumor.py` (validated `_load`, `_editable`, `_transition` with history, `Recovery`-guarded archive) reuses a reviewed, tested pattern instead of inventing a new one.

The capture guard runs only at creation. That is where b005 locates "decision made during active development". Later edits and dispositions happen on planning, after the campaign has usually completed.

Per `cli-mcp-parity`, CLI and MCP ship together. Per `workflow-doc-source-of-truth`, the owning docs are updated in this change, not deferred to the campaign's tentative docs step.

Search indexing (the `ruling` type, `_classify`, snapshot inventory) and prime exposure are deliberately left to later encounters. Until then, ruling files are simply unclassified. `search_index._classify` returns `None` for them, so `sync_write` and `Recovery` treat them as non-indexed, and `index_snapshot.inventory` does not enumerate `rulings/`, so index freshness is unaffected.

## Plan

1. **`core/config.py`:**
   - `RULING_DIR_NAME = "rulings"`, `RULING_STATUSES`, `DEFAULT_RULING_STATUS = "recorded"`
   - `RULING_NAME_PATTERN = re.compile(r"^c([0-9]{3,})-e([0-9]{3,})-([A-Za-z0-9_.-]+)$")`
2. **`core/templates/sourcebook/ruling.md`:** default frontmatter (`status: recorded`, `archived: false`, `history: []`) and the Decision/Context/Consequences headings.
3. **`core/ruling.py`**, mirroring `core/rumor.py`:
   - `RulingError`, `RulingNotFoundError` and `RulingAlreadyExistsError`.
   - `validate_name`, `ruling_dir`, `_locations` (paths checked through `boss._safe_path`), `ruling_path`, `_names`, `list_rulings`, `_load`, `read_metadata`, `template_body` and `get_payload`.
   - `_load` validates name/status/archived/location consistency, the `resolution` vs. status pairing, the history shape, and that `campaign`/`encounter` agree with the name's numbers.
   - `create_ruling(root, name, body, summary, origin)`:
     - parse the name;
     - resolve `c<NNN>` with `references.Inventory(root).resolve("campaign", ...)`;
     - read the campaign's status and require `open`;
     - for anything other than `e000`, resolve `e<NNN>` with `Inventory.resolve("encounter", ..., campaign)`;
     - check uniqueness across live and archived rulings;
     - write the record.
   - `update_ruling`, `canonize`, `note`, `reopen` and `archive_ruling`, following rumor's `_editable`/`_transition`/`Recovery` pattern.
4. **`core/references.py`:** add a canonical-only `ruling` domain to `_PREFIXES`/`_SYNTAX`/the `Inventory.names` directory map.
   - The canonical name is the only accepted form, and `identity()` always reports `short: None`.
   - `ruling` must not take part in `SHORT_REFERENCE_PATTERN`/`NUMBERED_NAME_PATTERN` matching, because a ruling name begins with `c`.
   - The decorator's appended docstring states that rulings take canonical names only.
5. **`cli/ruling.py` and `mcp/ruling.py`:**
   - Thin wrappers following `cli/rumor.py` and `mcp/rumor.py`.
   - CLI create/update support `--body`/`--body-file`/editor, plus required `--summary`/`--origin`. Canonize, note and reopen take a required `--message`.
   - Stored content is printed with `markup=False` (`console-best-practices`).
   - Register in `cli/app.py` and in `mcp/server.py` `_TOOL_MODULES`.
6. **Docs:** update `templates/docs/workflow.md` (domain model and lifecycle sections) and `templates/docs/tool-reference.md` (a new Rulings section plus any tool-inventory lists), as described in Requirements.
7. **Tests:**
   - `tests/core/test_ruling.py`
     - **Naming and capture:** creation succeeds in an open campaign, with an existing encounter or with `e000`. Creation is refused for draft, paused, completed and abandoned campaigns; a missing campaign or encounter; a malformed name; and a live or archived duplicate. Creation succeeds in a reactivated campaign.
     - **Lifecycle:** every transition and every refusal. Required narratives, update restricted to `recorded`, reopen clearing `resolution`, history entries, and archive moving the file while leaving the campaign untouched.
     - **Campaign independence:** a later campaign completion does not affect updating or dispositioning an existing ruling.
     - **Index isolation:** with a built index, ruling writes leave `index_status` fresh and add no rows.
   - `tests/cli/test_ruling.py` and `tests/mcp/test_ruling.py`, covering the commands and tools, cursor continuation, identity shape and the `markup=False` printing of bracketed text.
   - Update `tests/mcp/test_server.py::test_all_domain_tools_are_registered`, plus any CLI-module or reference test that enumerates domains or tools.

## Verification

- `pdm run pytest -q` passes, with no skips or deletions added to dodge failures.
- `pdm run ruff check .` reports zero errors, and `pdm run ruff format .` produces no diffs.
- `pdm run cac ruling -h` lists the eight commands. Every `ruling_*` MCP tool is registered, one for each CLI command.
- A manual smoke test in a temporary bootstrapped project (not this repo's sourcebook):
  1. Create an open campaign with an encounter.
  2. Create a ruling under that encounter, and one under `e000`.
  3. Canonize one and note the other, each with a narrative.
  4. Reopen one, then dispose of it again.
  5. Archive both, and confirm `get` still reads the archived records.
  6. Pause the campaign and confirm that creating another ruling is refused.
- `workflow.md` and `tool-reference.md` describe exactly the shipped names, arguments, guards and lifecycle, checked by reading the diff against the implementation.

## Log

### Review - 2026-11-21T00:41:14Z - John Hoff

Independent review against clean-tests-and-lint, cli-mcp-parity, console-best-practices, skills-authored-only-in-templates and workflow-doc-source-of-truth: PASS-WITH-NOTES. Verification enforces the pytest and ruff gates. All eight `cac ruling` commands ship with matching thin-wrapper `ruling_*` MCP tools, registered in `cli/app.py` and `_TOOL_MODULES` with the server registration test updated, and they keep cursor paging and get-body continuation. Stored content prints with `markup=False`. No skill templates are touched. `workflow.md` and `tool-reference.md` are updated in the same change, and Verification checks them against the shipped behavior. The Rationale's index-isolation claims were confirmed in code: `_classify` returns None for ruling paths, `sync_write` and `Recovery` skip unclassified paths, and `index_snapshot.inventory` does not enumerate `rulings/`. Notes for execution:
(1) State explicitly that the CLI editor fallback becomes a required body argument on MCP create/update.
(2) In `workflow.md`, document the ruling→campaign/encounter link as one-directional, recorded only on the ruling.
(3) Reflect the references-decorator docstring change in `tool-reference.md`.
(4) Pin down how a canonical-only `ruling` domain fits into the single-prefix `_PREFIXES`/`_SYNTAX` maps, and test that a ruling name like `c002-e001-x` is never matched as a campaign reference by `NUMBERED_NAME_PATTERN`/`SHORT_REFERENCE_PATTERN`.
(5) Consider a test that `_load` validates rulings whose campaign or encounter has since been archived.

### Opened - 2026-11-21T01:45:22Z - John Hoff

Opened with developer approval. Implementation will fold in all five reviewer notes.

### Message - 2026-11-21T02:14:29Z - John Hoff

Implementation complete, pending developer confirmation.

**Reviewer notes, all five addressed:**
1. The MCP `ruling_create` docstring and the `tool-reference.md` Rulings section both state that `body` is a required string, with no editor fallback.
2. `workflow.md` Connections says the ruling→campaign/encounter link is stored only on the ruling and is never written back.
3. `tool-reference.md` (Short references, Canonical identity, operation matrix) documents the canonical-only contract text that the decorator now appends.
4. `references.py` adds a `_CANONICAL_ONLY` set outside the single-prefix `_PREFIXES`/`_SYNTAX` maps. Rulings get no numeric map, `resolve` refuses non-exact names, and `identity` reports `short: null` with reason `canonical_only`. Tests cover that `c002-e001-x` never resolves as a campaign and that `RULING_NAME_PATTERN` and `SHORT_REFERENCE_PATTERN` are disjoint.
5. A test confirms that `_load` still validates and dispositions a ruling after its encounter is abandoned and its campaign is completed and archived. `_load` checks campaign/encounter only against the name's numbers, never against live storage.

**GM rulings during execution:**
- `test_docs` capped `workflow.md` at 40,000 characters. It was about 39,600 before e001, and even a minimal Rulings section reaches about 40,750. The developer chose to raise the cap to 45,000 as a stopgap and to capture a split of the guide into development and planning flavors as rumor `r004-split-workflow-guide-by-phase`.
- The docs leak-guard regex matched `e000`. The developer chose to exempt `e000` with a lookahead, because it is a reserved sentinel, not a repository encounter name.

**Other deviation:** the workflow Rulings section was kept brief to limit growth. Contract detail lives in `tool-reference.md`.

**Verification:**
- `pdm run pytest -q`: 1670 passed.
- `ruff check` and `ruff format --check`: clean.
- `cac ruling -h` lists the 8 commands, and the 8 `ruling_*` MCP tools are registered.
- Scratch-project smoke test passed every step: create under e001 and under e000; canonize and note; reopen and re-dispose; archive both; get the archived record; pause the campaign, then create is refused with the rumor hint; and `cac ruling get c001` is refused as not canonical. The scratch world was seeded through core `world.initialize_world`, not `cac bootstrap init`.

### Completed - 2026-11-21T02:16:00Z - John Hoff

Completed with developer confirmation. Verification passed: 1670 tests passed, ruff check and format clean, 8 CLI commands matched by 8 registered MCP tools, and the scratch-project smoke test passed every step. Implementation commit 1e52f9c.
