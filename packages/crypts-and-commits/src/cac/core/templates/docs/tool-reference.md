# Crypts and Commits Tool Reference

## About this reference

This reference holds the field-level contracts of the Crypts and Commits ("CAC")
MCP tools and `cac` CLI commands: names, arguments, result shapes, error and
guard conditions, response budgets, and cursor continuation. It is paired with
the [Workflow Reference Guide](workflow.md), which owns the domain model, status
lifecycles, cross-type connections, approval gates, and agent procedure. When a
statement here and a statement there seem to overlap, the workflow guide is
authoritative for what a rule means and when it applies, and this reference is
authoritative for how a tool or command expresses it.

Read this reference through `docs_get("tool-reference")` / `cac docs get
tool-reference`, and the workflow guide through `docs_get("workflow")` / `cac
docs get workflow`. Tool docstrings and `cac <group> <command> --help` remain
the quickest route for a single operation; read this reference when you need
the shared conventions that apply across operations.

MCP is the primary interface for agents. The CLI is the fallback when the MCP
server is unavailable, and the human interface. The two surfaces have parity,
except for developer-only maintenance (`cac bootstrap init` and `cac index
rebuild`), which is never exposed over MCP.

## Shared conventions

### CLI body input

Every CLI command that accepts `--body`/`-b` also accepts `--body-file PATH`,
including `cac boss record`. The two options conflict, even when one of them is
an empty string. A body file is read as UTF-8 with its newlines preserved, and
the result then goes through the same core validation, normalization and guards
as an inline body. An empty file produces an empty body, and the source file is
never modified. A relative path is resolved from the caller's current working
directory, not from the project root.

A missing, unreadable, directory, invalid-UTF-8 or conflicting input fails
before anything is written. File input never opens an editor. When neither
option is given, the command keeps its editor or template behavior, including
the kind-specific encounter template. MCP tools take body strings, never paths.
Body files change neither response budgets nor literal rendering.

Example: `cac campaign create c00N-example --body-file notes/plan.md`.

### Literal output

CLI `get` commands print stored text literally (Rich markup is disabled), so
bracketed text such as `[tool.pdm.workspace]` survives. Commands that return
JSON print compact JSON literally.

### Response budgets and continuation

Every `get` (world, lore, region, campaign, boss, encounter, rumor, docs) fits
its whole compact-JSON result, identity included, into a response budget. Docs
use a dedicated budget of 64,000 characters measured on the body; every other
response uses the ordinary response budget.

When a body does not fit, the result is cut and carries `next_cursor` and a
`notice`. Repeat the same get with `cursor` (CLI `--cursor`) until `next_cursor`
is absent, then join the `body` fields in order. Cursors are bound to the body
content: a malformed, out-of-range, or stale cursor (one issued before the
record changed) fails. Never read managed files to recover the rest of a body.

Paged lists (`*_list`, `boss_candidates`, `docs_list`) return `items` and
`next_cursor` and follow the same cursor rules. Cursors assume an unchanged
store; there are no snapshots.

### Canonical identity

MCP get and mutation results for bosses, campaigns and encounters add an
`identity` object without replacing any existing field. CLI target commands
print an `identity:` JSON line. An identity contains:

- `canonical` — the stored record name.
- `short` — the usable normalized short reference, or null.
- `reason` — null when `short` is usable; otherwise `unnumbered`, `ambiguous`,
  `missing`, or `invalid_storage`.

Encounter identities also contain the canonical `campaign`. When the qualified
reference is usable they add a contextual `bare_short` (the bare `eNNN` form).
An encounter whose parent has no usable short reference reports
`campaign_unnumbered`, `campaign_ambiguous`, or another `campaign_`-prefixed
parent reason. A delete result keeps the canonical identity with a null `short`
and reason `deleted`.

Boss, campaign and encounter paged lists keep their original `items` and
`next_cursor` and add a parallel `identities` array for that page only.
Encounter order rows and candidate items carry an identity per row.
`prime_applicable_lore` keeps its lore-entry shape. Prime and search expose
canonical stored names. Stored relationships always hold canonical names,
independent of identity display.

List paging measures the compact JSON of items plus identities plus envelope
before choosing the page. Candidate identities count within the candidate
page bound before explanation text is truncated. A required identity is never
cut into a different identifier: if the minimum cannot fit, the call fails
with an explicit budget error. An encounter order too large for the budget
fails; inspect the paged lists instead of expecting rows to be dropped.

### Short references

Selectors accept canonical names and the short forms `bNNN` (boss), `cNNN`
(campaign), `rNNN` (rumor) and `cNNN/eNNN` (encounter in a campaign). A bare
`eNNN` needs an explicit campaign or the active campaign. Short references use lowercase
prefixes and at least three ASCII digits, and the ID must be positive. Padding
is normalized numerically: `c12` is rejected, while `c1000` and `c01000` both
resolve to campaign number 1000, including across the 999/1000 transition.

A numbered full name is a prefix, digits, a hyphen and a nonempty slug
(`c00N-example`). Resolution inventories live and archived records in the
current project:

- An exact canonical name always selects its own record first. A historical
  literal `b001` record therefore stays reachable beside `b001-slug`; that
  sibling then has no usable short reference and is reached by its full name.
- A numeric collision, including different padding or an archived match,
  raises an ambiguity error rather than choosing a slug.
- Duplicate canonical files across live and archive storage are integrity
  errors, even for full-name lookups.
- Malformed, unknown or wrong-domain references fail before any write.

A qualified encounter reference overrides the active-campaign fallback, and an
explicit `campaign` argument must resolve to the same campaign. Qualification
bypasses no closed-campaign, frozen, lifecycle or archive guard. Encounter IDs
and prerequisite edges stay campaign-local.

CLI and MCP share the same selection and input rules. Lower storage routines
consume exact names and never reinterpret damaged links. Resolution may cache a
request-local inventory but never keeps persistent maps, writes, reserves
numbers, performs branch or network lookups, or migrates records.

### Operation/input matrix

| Surface | Reference inputs | Literal inputs |
| --- | --- | --- |
| Boss get/update/make-available/withdraw/reactivate/archive | existing name | body, summary |
| Boss assign/unassign-dependency | source name, prerequisite | missing canonical edge on explicit removal |
| Boss assign-campaign | existing boss | new campaign_name, body |
| Campaign get/update/delete/open/pause/complete/abandon/archive/reactivate | existing name | body, message |
| Campaign create / set-bosses | boss list refs; existing campaign for set | new create name, body, message |
| Encounter get/update/delete/review/open/record-message/complete/abandon | name, optional campaign | body, message |
| Encounter assign/unassign-region | name, optional campaign | region |
| Encounter assign/unassign-dependency | source, prerequisite, optional campaign | missing canonical edge on explicit removal |
| Encounter list/order, encounter create | existing campaign | new create name, body, kind, cursor |
| Rumor get/update/dismiss/reopen/archive | existing name | body, summary, origin, message |
| Rumor promote | existing rumor, existing boss | message |
| Rumor renumber | existing rumor | new name |
| Boss/campaign/rumor create | none | new name, body, summary, origin where applicable |
| Prime applicable-lore | encounter, optional campaign | returned lore refs unchanged |
| Boss/campaign/rumor lists and candidates | none | cursor, flags, rumor status |

Lore, region and doc names, world keys and values, messages, bodies, summaries
and search phrases are always literal. There is no resolver endpoint, no boss
or rumor deletion, and no generic status setter.

Creation names are literal. Encounter create may select its campaign by
reference but cannot create a qualified path. Dependencies are canonicalized
before graph checks and persistence, so mixed spellings cannot bypass the self,
duplicate or cycle guards. Explicit removal may target a missing canonical
edge, but ambiguous shorthand cannot choose one. Reads never reinterpret or
rewrite stored links or graph names.

### Active campaign argument

Every encounter tool takes an optional `campaign` (CLI `--campaign`/`-c`).
When it is omitted, the tool uses the single open campaign and fails if none is
open. Mutating encounter tools refuse a
completed or abandoned campaign; `encounter_get`, `encounter_list` and
`encounter_order` accept any existing campaign.

### Deletion confirmation

CLI delete commands (`cac lore delete`, `cac region delete`, `cac campaign
delete`, `cac encounter delete`) prompt for confirmation
unless given `--yes`/`-y`. MCP delete tools never prompt. Confirmation never
bypasses a core guard.

## World

| Operation | MCP | CLI |
| --- | --- | --- |
| Read | `world_get(cursor=None)` | `cac world get [--cursor]` |
| Set an attribute | `world_set(key, value)` | `cac world set KEY VALUE` |
| Replace body | `world_set_body(body)` | `cac world set-body [--body/-b \| --body-file]` |
| Assign/unassign lore | `lore_assign_world(name)` / `lore_unassign_world(name)` | `cac lore assign-world NAME` / `unassign-world NAME` |

World reads, world-returning setters, lore-link operations and prime return the
effective `merge_target_branch` and `planning_branch` values. Persist a branch
override with `world_set(key="planning_branch", value="plans/team")` / `cac
world set planning_branch plans/team`, or `merge_target_branch` similarly. Only
that attribute and the audit stamps are written. The generic setter accepts any
string, with no Git branch-name validation.

## Lore

| Operation | MCP | CLI |
| --- | --- | --- |
| Read | `lore_get(name, cursor=None)` | `cac lore get NAME [--cursor]` |
| List | `lore_list(cursor=None)` | `cac lore list [--cursor]` |
| Create | `lore_create(name, body, summary)` | `cac lore create NAME --summary/-s [--body/-b \| --body-file]` |
| Replace body and summary | `lore_update(name, body, summary)` | `cac lore update NAME --summary/-s [--body/-b \| --body-file]` |
| Set summary only | `lore_set_summary(name, summary)` | `cac lore set-summary NAME SUMMARY` |
| Delete | `lore_delete(name)` | `cac lore delete NAME [--yes/-y]` |
| Enable / disable | `lore_enable(name)` / `lore_disable(name)` | `cac lore enable NAME` / `disable NAME` |
| Assign/unassign world | `lore_assign_world(name)` / `lore_unassign_world(name)` | `cac lore assign-world NAME` / `unassign-world NAME` |
| Assign/unassign region | `lore_assign_region(name, region)` / `lore_unassign_region(name, region)` | `cac lore assign-region NAME REGION` / `unassign-region NAME REGION` |

Summaries are at most 500 characters and are required with every body write.

## Region

| Operation | MCP | CLI |
| --- | --- | --- |
| Read | `region_get(name, cursor=None)` | `cac region get NAME [--cursor]` |
| List | `region_list(cursor=None)` | `cac region list [--cursor]` |
| Create | `region_create(name, body, summary, path="")` | `cac region create NAME --summary/-s [--path/-p] [--body/-b \| --body-file]` |
| Replace body and summary | `region_update(name, body, summary)` | `cac region update NAME --summary/-s [--body/-b \| --body-file]` |
| Set summary only | `region_set_summary(name, summary)` | `cac region set-summary NAME SUMMARY` |
| Set path | `region_set_path(name, path)` | `cac region set-path NAME PATH` |
| Delete | `region_delete(name)` | `cac region delete NAME [--yes/-y]` |

Region-lore links are made through the lore tools above, because the region is
the target object.

## Campaign

| Operation | MCP | CLI |
| --- | --- | --- |
| Read | `campaign_get(name, cursor=None)` | `cac campaign get NAME [--cursor]` |
| List names and status | `campaign_list(cursor=None, include_archived=False)` | `cac campaign list [--cursor] [--include-archived]` |
| Create (starts draft) | `campaign_create(name, body, bosses=None)` | `cac campaign create NAME [--boss REF ...] [--body/-b \| --body-file]` |
| Replace draft membership | `campaign_set_bosses(name, bosses, message)` | `cac campaign set-bosses NAME [--boss REF ...] --message/-m REASON` |
| Replace body | `campaign_update(name, body)` | `cac campaign update NAME [--body/-b \| --body-file]` |
| Delete | `campaign_delete(name)` | `cac campaign delete NAME [--yes/-y]` |
| Open / pause | `campaign_open(name)` / `campaign_pause(name)` | `cac campaign open NAME` / `pause NAME` |
| Complete / abandon (postmortem) | `campaign_complete(name, message)` / `campaign_abandon(name, message)` | `cac campaign complete NAME -m TEXT` / `abandon NAME -m TEXT` |
| Reopen completed (reason) | `campaign_reactivate(name, message)` | `cac campaign reactivate NAME -m REASON` |
| Archive with all encounters | `campaign_archive(name)` | `cac campaign archive NAME` |

`bosses` is a list of boss references; repeat `--boss` once per member. On
create, omitting it (or passing an empty list) creates a bossless campaign. On
`set-bosses`, passing no `--boss` (MCP `[]`) clears the set. Duplicate members
after alias resolution are rejected. A same-set `set-bosses` request is
read-only regardless of order. Membership changes log the old names, new names
and reason once, and later body updates preserve that Log entry.

Campaign reads expose the canonical `bosses` list. Legacy singular `boss`
storage reads as a one-member list and an absent or null field reads as empty;
storage with both fields, malformed values or duplicates fails. Reads never
write; supported mutations normalize storage to `bosses`. Campaign lists sort
canonical names numerically, then legacy names lexically; order is not
priority.

`campaign_list` and `encounter_list` default to live records.
`include_archived=True` / `--include-archived` returns the live and archived
union for that scope, with the same identities, status fields, sorting and
cursor budgets; ambiguous or unsafe storage fails. This archive inventory is
read-only and independent of search. Use every page when allocating IDs.
`encounter_order` is live-only. Get resolves live or archived identities, and
reading an archived record never restores it.

## Encounter

| Operation | MCP | CLI |
| --- | --- | --- |
| Read | `encounter_get(name, campaign=None, cursor=None)` | `cac encounter get NAME [-c] [--cursor]` |
| List, oldest-updated first | `encounter_list(campaign=None, cursor=None, include_archived=False)` | `cac encounter list [-c] [--cursor] [--include-archived]` |
| Dependency order | `encounter_order(campaign=None)` | `cac encounter order [-c]` |
| Create (starts draft) | `encounter_create(name, body, campaign=None, kind="scripted")` | `cac encounter create NAME [-c] [--kind/-k] [--body/-b \| --body-file]` |
| Replace body (draft only) | `encounter_update(name, body, campaign=None)` | `cac encounter update NAME [-c] [--body/-b \| --body-file]` |
| Delete | `encounter_delete(name, campaign=None)` | `cac encounter delete NAME [-c] [--yes/-y]` |
| Review | `encounter_review(name, message, campaign=None)` | `cac encounter review NAME [-c] -m TEXT` |
| Open | `encounter_open(name, campaign=None, message=None)` | `cac encounter open NAME [-c] [-m TEXT]` |
| Record a message | `encounter_record_message(name, message, campaign=None)` | `cac encounter record-message NAME [-c] -m TEXT` |
| Complete | `encounter_complete(name, campaign=None, message=None)` | `cac encounter complete NAME [-c] [-m TEXT]` |
| Abandon | `encounter_abandon(name, message, campaign=None)` | `cac encounter abandon NAME [-c] -m TEXT` |
| Assign/unassign region | `encounter_assign_region(name, region, campaign=None)` / `encounter_unassign_region(...)` | `cac encounter assign-region NAME REGION [-c]` / `unassign-region` |
| Assign/unassign dependency | `encounter_assign_dependency(name, dependency, campaign=None)` / `encounter_unassign_dependency(...)` | `cac encounter assign-dependency NAME DEPENDENCY [-c]` / `unassign-dependency` |

`encounter_open` fails while any direct prerequisite is not completed, listing
every unsatisfied prerequisite with its status. `encounter_delete` fails while
another encounter depends on the target. When `--body` and `--body-file` are
both absent, `cac encounter create` opens an editor on the template for the
chosen kind.

## Boss

| Operation | MCP | CLI |
| --- | --- | --- |
| Capture | `boss_create(name, body, summary)` | `cac boss create NAME --summary/-s [--body/-b \| --body-file]` |
| Record a roadmap goal | `boss_record(name, body, summary, progress, source, message, completed_on=None, depends_on=None)` | `cac boss record NAME --progress --source --message/-m --summary/-s [--completed-on] [--depends-on ...] [--body/-b \| --body-file]` |
| Read | `boss_get(name, cursor=None)` | `cac boss get NAME [--cursor]` |
| List canonical names | `boss_list(cursor=None, include_archived=False)` | `cac boss list [--cursor] [--include-archived]` |
| Replace body and summary | `boss_update(name, body, summary)` | `cac boss update NAME --summary/-s [--body/-b \| --body-file]` |
| Make available | `boss_make_available(name)` | `cac boss make-available NAME` |
| Withdraw | `boss_withdraw(name)` | `cac boss withdraw NAME` |
| Reactivate withdrawn | `boss_reactivate(name)` | `cac boss reactivate NAME` |
| Archive | `boss_archive(name)` | `cac boss archive NAME` |
| Add / remove prerequisite | `boss_assign_dependency(name, dependency)` / `boss_unassign_dependency(name, dependency)` | `cac boss assign-dependency NAME DEPENDENCY` / `unassign-dependency NAME DEPENDENCY` |
| Select into a new draft campaign | `boss_assign_campaign(name, campaign_name, body)` | `cac boss assign-campaign NAME CAMPAIGN_NAME [--body/-b \| --body-file]` |
| Candidate discovery | `boss_candidates(cursor=None)` | `cac boss candidates [--cursor]` |

Create, update and record take the body and summary together. The CLI accepts
`--body`, `--body-file`, or an editor initialized from the template or the
current body; MCP requires explicit strings. Output preserves literal Markdown.
MCP get and mutation results contain `metadata`, `summary`, `body` (bounded)
and `identity`. Lists return canonical names with cursor paging; their order is
not priority.

### Roadmap recording

`boss_record` is create-only: a name that already exists live or archived
fails without updating anything. `progress` is one of `planned`,
`in_progress` or `completed`. `source` must be nonblank. `completed_on` is an
optional `YYYY-MM-DD` date, accepted only with `completed` progress; an invalid
date or a date in the future (UTC) fails. The CLI takes `--completed-on` and a
repeatable `--depends-on`. Dependency references resolve against existing
goals, including archived ones, before a single atomic write.

The stored `provenance` object contains `kind` (`roadmap`), `progress`,
`source`, `message` and `completed_on` (null when unknown). Recorded reads keep
provenance and identity whole and continue the body by cursor. Impossible
provenance metadata fails explicitly, and is checked before a record or
archive operation.

### Selection result

`boss_assign_campaign` returns `boss`, `campaign`, `status`, `reused`,
`boss_identity`, `campaign_identity` and `identity`. A consistent retry
returns the existing state with `reused` set and ignores the retry body.

### Candidate page

`boss_candidates` returns read-only compact JSON with:

- `items`, `next_cursor`
- `counts`: `total_live`, `total_archived`, `pool`, `eligible`, `blocked`,
  `not_ready`, `excluded`, `invalid` (unreadable live records)
- `healthy` (true when there are no diagnostics), `diagnostics`,
  `diagnostics_omitted`, `diagnostics_ref` (`boss_list` when diagnostics exist,
  otherwise null)

Each item carries `name`, `summary`, `status`, `classification`, `eligible`,
`reason_codes`, `prerequisite_count`, `unsatisfied_count`, `diagnostic_count`,
`prerequisites`, `diagnostics`, `ref` (`boss_get`) and `identity`. Each
prerequisite detail carries `name`, `status`, `archived`, `satisfied`, and
optionally `campaign` and `campaign_status`.

Top-level reason codes are `not_ready`, `prerequisite_unsatisfied` and
`integrity_error`. Diagnostic codes are `invalid_record`, `invalid_summary`,
`invalid_dependencies`, `duplicate_dependency`, `self_dependency`,
`missing_prerequisite`, `dependency_cycle`, `dependency_integrity`,
`invalid_campaign_link`, `campaign_not_found`, `ambiguous_campaign`,
`invalid_campaign_record`, `campaign_boss_mismatch` and
`campaign_state_mismatch`. Diagnostic entries carry `name`, `code`, `message`
and optional prerequisite or campaign names. A cycle diagnostic on a dependent
does not imply that the dependent is a cycle member.

Recorded goals add `roadmap` with `recorded_progress`, `source` (a bounded
preview), `source_truncated` and `ref` (`boss_get`). An externally completed
prerequisite adds `completion_origin: "roadmap"` and `ref`; this never implies
campaign ownership.

The whole page fits the shared response budget. Each detail list (an item's
prerequisites or diagnostics, and the global diagnostics) holds at most 16
entries, and global diagnostics use at most a quarter of the budget,
reduced further when needed. Cuts are reported through
`prerequisites_omitted`, `diagnostics_omitted` and `summary_truncated`; counts
and eligibility are never cut. No bodies are included; hydrate with `boss_get`
or `campaign_get`. If the envelope and required identifiers cannot fit, the
call fails explicitly. Unsafe or ambiguous storage fails.

### Failure and recovery

Boss and campaign coupling operations preflight the whole affected cohort
(records, audit stamps, paths and output) before writing. Changed boss metadata
preserves the design body bytes, summary, dependencies and creation stamps. If
a write fails, the affected bytes, index rows and fingerprints are restored,
including encounters, while unrelated records and drift are preserved. A
`RecoveryError` names any residual paths or rows that could not be restored.
There is no automatic rebuild or retry, number allocation, Git check, crash
journal, or cross-process guarantee.

## Rumors

| Operation | MCP | CLI |
| --- | --- | --- |
| Capture | `rumor_create(name, body, summary, origin)` | `cac rumor create NAME --summary/-s --origin/-o [--body/-b \| --body-file]` |
| Read | `rumor_get(name, cursor=None)` | `cac rumor get NAME [--cursor]` |
| List canonical names | `rumor_list(cursor=None, include_archived=False, status=None)` | `cac rumor list [--cursor] [--include-archived] [--status]` |
| Replace body, summary and origin | `rumor_update(name, body, summary, origin)` | `cac rumor update NAME --summary/-s --origin/-o [--body/-b \| --body-file]` |
| Promote to a boss | `rumor_promote(name, boss, message=None)` | `cac rumor promote NAME BOSS [--message/-m]` |
| Dismiss | `rumor_dismiss(name, message)` | `cac rumor dismiss NAME --message/-m` |
| Reopen | `rumor_reopen(name, message)` | `cac rumor reopen NAME --message/-m` |
| Archive | `rumor_archive(name)` | `cac rumor archive NAME` |
| Renumber | `rumor_renumber(name, new_name)` | `cac rumor renumber NAME NEW_NAME` |

Rumors live at `rumors/<name>.md` and, once archived, `archive/rumors/<name>.md`.
Create and update take the body, summary and origin together. The summary is
required, nonblank and at most 500 characters; the origin is required, nonblank
free text and is never validated against records. The body may be empty. The
CLI accepts `--body`, `--body-file`, or an editor initialized from the empty
template or the current body; MCP requires explicit strings. Update is a full
replacement and requires an `open` rumor.

`status` is `open`, `promoted` or `dismissed`. Promote requires an `open` rumor
and an existing unassigned, unarchived `proposed` or `available` boss, given by
canonical name or `bNNN`; it records `boss` and an optional `resolution` and
never writes the boss. Many rumors may share a boss. Dismiss requires an `open`
rumor and a nonblank reason, stored as `resolution`. Reopen requires an
unarchived promoted or dismissed rumor and a nonblank message, and clears
`boss` and `resolution`. Promote, dismiss and reopen each append an
`{action, message, by, on}` entry to `history`, which update never changes.
Archive requires a promoted or dismissed rumor; archived rumors are read-only.
There is no delete.

Renumber renames a live `open` or `dismissed` rumor to an unused literal name,
live or archived, changing its file and `name` and refreshing the update stamp.
Promoted and archived rumors are refused; reopen a promoted rumor first.

MCP get and mutation results contain `metadata` (including `origin`, `status`,
`boss`, `resolution`, `history` and `archived`), `summary`, `body` (bounded) and
`identity`; renumber reports the new name's identity. List returns canonical
names and parallel identities with cursor paging, and its order is not
priority; `status` filters by status, and an unknown status fails. CLI get
prints metadata, summary and body literally. Unsafe names, storage links or
junctions, and path or type collisions fail before writes.

## Prime

| Operation | MCP | CLI |
| --- | --- | --- |
| Global bundle | `prime_get()` | `cac prime get` |
| Applicable lore for an encounter | `prime_applicable_lore(encounter, campaign=None)` | `cac prime applicable-lore NAME [-c] [--cursor]` |

`prime_get` returns `world` (metadata with effective branch settings, and
body), `world_lore` (enabled world-assigned lore summaries), `regions` (each
with summary, path and assigned-lore names), `active_campaign`,
`campaign_body`, `active_boss_names`, `active_bosses`,
`active_boss_diagnostics` and `truncations`.

- `active_boss_names` lists every declared member.
- `active_bosses` holds validated entries with `metadata` (`name`, `status`,
  `archived`, `depends_on`, `campaign`), `summary` and `body`.
- `active_boss_diagnostics` holds entries with `code`, `campaign`, `boss` and
  `message`; group or storage errors may use `boss: null`.
- With no active campaign, or a bossless one, all three lists are empty. There
  is no singular `active_boss` field and no first-boss alias.

The serialized bundle shares one response budget. Metadata and routing are
reserved first, then the remaining space is divided among the bodies in world,
campaign, boss order. `truncations` is empty when everything fits; each cut
adds `{field, notice: "TRUNCATED", ref: {tool, name?}}` pointing at `world_get`,
`campaign_get` or `boss_get`. If metadata alone cannot fit, the call fails;
routing is never silently dropped. The CLI renders the same facts literally.

`prime_applicable_lore` returns a list of `{name, summary, ref}` entries, where
`ref` is the lore name to pass to `lore_get`.

## Search index

| Operation | MCP | CLI |
| --- | --- | --- |
| Status | `index_status()` | `cac index status` |
| Search | `index_search(phrase, max_results=10, skip=0, object_type=None, snippet_tokens=20, include_archived=False)` | `cac index search PHRASE [-n] [--skip/-s] [--type/-t] [--snippet-tokens] [--include-archived]` |
| Rebuild (developer-only) | none | `cac index rebuild` |

Search covers world, lore, region, boss, campaign, encounter and rumor
records. Boss hits index the summary and body, and rumor hits index the
summary, origin and body, each with name, status, audit and archive
metadata; every status is searchable, and a hit is not an eligibility
assertion. Archived
records are excluded unless `include_archived` is set. Each hit has `rank`,
`score`, `object_type`, `campaign`, `name`, `status`, `updated_on`, `archived`
and `excerpt`. An oversized response fails with guidance to lower
`max_results` or `snippet_tokens`; hits are never silently dropped. An empty
phrase, `max_results` below 1, negative `skip`, an unknown `object_type` or an
out-of-range `snippet_tokens` fails.

MCP results always include `built` and `stale`:

- Never built: `{built: false, stale: false, hits: []}`.
- Fresh: `{built: true, stale: false, hits: [...]}`.
- Stale: `{built: true, stale: true, hits: [], diagnostic: {code:
  "stale_index", message, recovery}}`.

The core search raises `StaleIndexError` before returning stale hits, and the
CLI exits nonzero with no hits. `index_status` returns counts plus `freshness`
(`missing`, `fresh` or `stale`) and a nullable `diagnostic`; stale counts
describe the indexed snapshot. Counts total live and archived content together.

Freshness compares each record's identity, relative location and SHA-256 of
its raw UTF-8 bytes (metadata included) against a versioned manifest. The
inventory covers world, lore, region, and live and archived boss, campaign,
encounter and rumor records, including orphaned encounters; it excludes
unrelated files. Git state and modification times are never used. Legacy,
unsupported, divergent, unreadable or invalid index data requires a developer
rebuild. Reads never write, migrate or rebuild the index. Returning to the
indexed source snapshot restores freshness.

Writes through CAC atomically update the affected rows and fingerprints
without blessing unrelated drift. Archiving changes the record's indexed
location. Scoped rollback restores bytes, rows and fingerprints or reports
incomplete recovery. Rebuild publishes transactionally and is never used as
automatic failure recovery. These guarantees cover local operations, not
concurrent writers or crashes. The index format is independent of the
sourcebook schema version.

## Docs

| Operation | MCP | CLI |
| --- | --- | --- |
| List | `docs_list(cursor=None)` | `cac docs list [--cursor]` |
| Read | `docs_get(name, cursor=None)` | `cac docs get NAME [--cursor]` |

`docs_list` pages `{name, summary}` pairs. `docs_get` returns `name`,
`summary` and `body`, using the dedicated docs budget and the shared
continuation rules. Docs are packaged, read-only and framework-owned. The
registered docs are `workflow`, `tool-reference`, `branching-guide` and
`migration-guide`.
