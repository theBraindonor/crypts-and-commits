# Workflow guide split: design comparison

Status: design accepted by the developer during c003/e001. This document
records the selected structure; it does not replace the current packaged workflow's
authority or authorize implementation encounters. Source baseline: `44c2bde`; the measured
packaged workflow is unchanged from that commit.

## Recommendation

Start with two self-contained phase guides, `planning-workflow` and
`development-workflow`, and retain `workflow` as a short routing entry point.
Use consistent copies of shared rules, with an explicit owning section for each
rule and links identifying the copies. Do not add a separately retrieved
`common-workflow` guide initially. The developer accepted this structure and
the duplication tradeoff in ruling c003-e001-self-contained-guides-mcp-headroom.

The primary reason for the 40,000-character cap is compatibility with MCP call
character limits across clients, rather than eliminating all duplication or
minimizing the total stored documentation. The aim is broad support with
headroom; this design does not establish a universal limit or prove compatibility
with every MCP client. Each guide must satisfy the cap independently.

The allocation below reduces the existing 43,253-character combined guide to
29,660 characters of planning content and 30,277 of development content before
new wrappers. Allowing 1,000 characters per guide for titles, introductions and
new routing gives estimates of 30,660 and 31,277. Both leave substantial room
under the required 40,000-character cap. These are source-allocation experiments,
not measurements of implemented guides or proof of practical usability.

The cost is 18,018 characters of shared source text in both guides. Keeping each
phase's ordinary deep-reference path in one retrieval is a reasonable initial
tradeoff. A separate common guide can be reconsidered if implementation review
finds the synchronized copies difficult to maintain or later usage reveals
clear retrieval benefits. The developer's joint review selected Candidate A;
the measurements alone did not make that decision.

## Fixed requirements and boundaries

- Register the exact names `development-workflow` and `planning-workflow`.
- Keep `workflow` as a short index, not another full procedural guide. Aim for
  about 700 characters; the enforced maximum remains 40,000.
- Enforce 40,000 characters for each workflow guide, including a common guide
  if one is eventually selected. Count decoded text with LF newlines, as the
  existing Python resource loading does; byte count is a different quantity.
- Preserve current lifecycle rules, freezes, guards, authorization boundaries
  and all three separate encounter approvals.
- Update all six packaged skill templates and affected references. Never edit
  deployed skill copies; developer-run bootstrap redeploys them.
- Finish the campaign after joint logical review and clean automated checks.
  Final practical validation accumulates organically through later usage and
  does not block campaign completion.

## Concrete allocation and complete section coverage

The table partitions the current workflow into exact source slices. A top-level
section includes its subsections except that Bosses, Agent planning and campaign
workflow, and Developer-only maintenance are split at their level-three headings.
The cross-phase "Not separately gated" paragraph is also extracted from Explicit
user gates into its own shared slice; its remaining text stays development-only.
Each slice includes its heading and trailing whitespace through the next slice.
P = planning-only; D = development-only; S = shared. All 41,919 characters of
retained rule/procedure slices are allocated exactly once to a group.

| Source unit | Group | LF characters |
| --- | --- | ---: |
| Domain model at a glance | S | 2154 |
| World | P | 2023 |
| Lore | S | 707 |
| Region | S | 519 |
| Campaign | S | 2852 |
| Encounter | D | 2812 |
| Bosses | P | 2109 |
| Boss dependencies | P | 462 |
| Schema and compatibility | P | 603 |
| Roadmap adoption | P | 1929 |
| Candidate discovery | S | 1069 |
| Promotion and campaign coupling | S | 2230 |
| Rumors | S | 1107 |
| Rulings | S | 980 |
| Explicit user gates | D | 3192 |
| Not separately gated | S | 335 |
| Codex encounter handoffs | D | 2073 |
| Priming and the disclosure ladder | S | 1616 |
| Ownership | S | 903 |
| Orient and synchronize | S | 783 |
| Allocate numbers | S | 1184 |
| Plan goals | P | 617 |
| Select and register | D | 629 |
| Execute on the campaign branch | D | 668 |
| Capture rulings | D | 701 |
| Collision checks | S | 605 |
| Complete and reactivate | D | 682 |
| Reconciliation examples | S | 974 |
| Planning handoff | P | 1390 |
| Example: an encounter's lifecycle | D | 1502 |
| Bootstrap | P | 451 |
| Search index rebuild | P | 205 |
| Codex patch guard | P | 1853 |

The remaining 1,334 characters are the original title/preamble (47), Purpose
(1,215), and the two container headings (41 and 31). Replace their presentation,
but carry forward their substance: CAC's purpose, developer authority,
MCP-first/CLI fallback, the distinction between procedural and tool-contract
authority, on-demand disclosure and same-change documentation obligations.
Container headings become appropriate phase-guide headings. Nothing in those
1,334 characters is permission to drop a rule.

P-only maintenance and World detail remain available to development through
explicit links to planning and the migration guide. Development introductions
must still state the MCP/CLI-only rule, developer-only bootstrap/index recovery,
and that branch settings do not create branches or prove integration. A linked
maintenance reference supplements those boundaries rather than hiding them.

## Candidate A: two guides with synchronized shared sections

`planning-workflow` outline, in reading order:

1. Purpose, authority and phase routing.
2. Domain model, World, Lore and Region; branch settings and schema routing.
3. Bosses, dependencies, compatibility, roadmap adoption and candidate discovery.
4. Campaign lifecycle, archival and promotion/campaign coupling.
5. Rumors and Rulings, including their statuses and one-way relationships.
6. Priming; skill ownership; synchronization and complete number inventories;
   the shared rule on actions not separately gated.
7. Goal planning; collision checks; reconciliation and integrated planning handoff.
8. Developer-only maintenance, with migration-guide links.

`development-workflow` outline:

1. Purpose, authority, maintenance boundaries and phase routing.
2. Domain model, Lore and Region; campaign lifecycle and archival.
3. Candidate discovery and campaign coupling needed for selection and execution.
4. Encounter lifecycle, kinds, region/dependency guards and closed-history rules.
5. Explicit gates and review flow; the shared rule on actions not separately
   gated; Codex draft/review handoffs.
6. Rumors and Rulings as context for capture and later disposition.
7. Priming; ownership; synchronization, numbering and collision checks.
8. Selection/registration; execution branch; ruling capture; completion/reactivation.
9. Reconciliation and encounter lifecycle example; link to planning for triage.

All shared slices appear in each guide. Reorder and repair heading levels, local
anchors and cross-references; do not copy the old monolithic section references
without checking their destination. Candidate A permits one deep-guide retrieval
per phase for the scenarios below, with unusual maintenance or roadmap questions
explicitly routed across phases.

## Candidate B: separate common guide

Register `common-workflow` in addition to the two required phase guides. Put
every S slice in common, retaining their source order or a documented equivalent.
Planning contains the P slices in the outline above; development contains the D
slices. Both phase guides identify which common sections are prerequisites to
their procedure and link directly to them. The workflow entry point routes by
task and says that phase and common rules together constitute the authority.

This is a concrete extraction alternative, not an assumption that all context
must be preloaded. A phase-specific question may need only the phase guide when
the skill already supplies the required shared context. A complete rule reading
for selection, dependencies or triage generally needs common as well.

| Candidate | Planning | Development | Common | Index allowance |
| --- | ---: | ---: | ---: | ---: |
| A: exact retained slices | 29,660 | 30,277 | none | not part of slices |
| A: with wrapper allowances | 30,660 | 31,277 | none | 700 |
| B: exact retained slices | 11,642 | 12,259 | 18,018 | not part of slices |
| B: with wrapper allowances | 12,642 | 13,259 | 19,018 | 700 |

The 1,000-character wrapper allowances are estimates, not prototyped prose.
They cover replacement purpose/authority text, titles and routing; measure the
actual result before acceptance. Content-only reductions in A are about 31.4%
for planning and 30.0% for development relative to 43,253. Shared duplication
makes A's two bodies total 59,937 characters before wrappers; B's three bodies
total 41,919. Fewer stored characters do not necessarily mean fewer retrieved
characters: full planning+common in B has the same retained text as A's planning
guide, with another wrapper and another call. The same holds for development.

A common section inside the short workflow index is a less attractive variant:
it would expand the index toward 18,018 characters and turn an apparent router
into an implicit prerequisite. A common section copied inside both phase guides
is Candidate A under a different heading. A later selective extraction is also
possible, but has not been measured as a third candidate here.

## Retrieval walkthroughs

These are desk walkthroughs over the allocations, not fresh-session tests.
Counts below concern deep workflow retrieval only; prime, lore hydration and
optional tool-reference or branching-guide calls remain unchanged. Skills must
continue to avoid fetching deep docs during routine orientation.

| Task | Candidate A path | Candidate B complete-rule path | Check preserved |
| --- | --- | --- | --- |
| Refine a goal and assess readiness | planning-workflow: Bosses, dependencies, roadmap, candidates, Plan goals | planning-workflow + common-workflow: candidates, numbering and synchronization | Complete retained inventory; explicit readiness; available is not eligible; design freezes and graph checks |
| Register a campaign | development-workflow: candidates/coupling, allocation, selection and reconciliation | development-workflow + common-workflow | Numeric reservations; reciprocal ownership; integrate draft registration before opening on matching execution branch; publication still needs authorization |
| Review and open an encounter | development-workflow: Encounter, gates, review flow and Codex handoffs | development-workflow + common-workflow for region/lore resolution and priming | Fresh independent reviewer; new approval for re-review; auto-transition only on pass/authorized override; separate open and complete approvals; dependency and region guards |
| Triage a recorded ruling | planning-workflow: Rulings, synchronization, Not separately gated and Planning handoff | planning-workflow + common-workflow | Integrated execution history; developer-approved lore/region/world changes before canonization, or narrative note; independent archival; no extra lifecycle gate invented for context edits |

The short index can direct an unfamiliar user at the cost of an additional call;
updated skills should route directly to the phase guide when the phase is known.
Do not make the reader fetch both phase guides merely to perform one ordinary
task. In A, planning points to development for full encounter gates; development
points to planning for goal editing, roadmap recording, maintenance and triage.

## Ownership and consistency review

The tool reference remains the owner of MCP/CLI names, arguments, results,
errors, budgets and cursor contracts. Phase guides own the existing procedural
meaning. No runtime behavior or approval policy changes are proposed.

For A, designate these primary homes when updating the governing lore:

| Rule family | Primary home | Treatment of other copies |
| --- | --- | --- |
| World, static context, priming and role ownership | planning-workflow | Development carries matching context needed for execution |
| Boss lifecycle, graph, readiness and roadmap | planning-workflow | Development repeats complete candidate eligibility needed for selection |
| Campaign lifecycle, selection coupling and reconciliation | development-workflow | Planning repeats rules needed to trust integration and archive outcomes |
| Encounter lifecycle, all gates, override and handoff reports | development-workflow | Planning links to full execution procedure |
| Actions not separately gated | development-workflow | Planning carries the complete matching paragraph, subject to existing authorization rules |
| Rumor/ruling statuses and triage; integrated archival | planning-workflow | Development repeats record semantics and owns capture procedure |
| Synchronization, numbering and collision checks | planning-workflow | Development has synchronized copies with execution context |
| Bootstrap/index recovery and patch-guard detail | planning-workflow, with migration-guide upgrade procedure | Development repeats prohibitions and links for detail |

For B, S rules instead have their primary home in common; P and D rules remain
with their phase. Under either structure, state authority explicitly and update
the existing workflow-doc-source-of-truth lore through world-manager after the
developer approves its body and summary. Its current single-owner wording must
be reconciled with synchronized copies; copies must not become competing
definitions. Neither this proposal nor the later lore update waives existing
approval gates or same-change ownership requirements.

A substantive rule change must update its primary section and every affected
mirror in the same change. Primary ownership is an authoring and reconciliation
rule, not a requirement to retrieve another guide during ordinary phase work.
An accidentally divergent mirror is a documentation defect: reconcile it against
the primary rule and the implementation, and correct all affected copies.

Joint review should trace the tables above against the current source, not rely
on a phrase-presence test as semantic proof. Check at least: all campaign states
and terminal/archive distinctions; assignment freeze versus membership lock;
vanquished prerequisites versus unmerged work; immutable roadmap provenance;
encounter kinds/locked sections/dependencies; all three user gates and the
REJECT-only override; summary-versus-body authority; each record's relationship
direction; capture versus triage branches; no delete/restore shortcuts; and
developer-only maintenance. Duplication must preserve the same exceptions and
negative cases, not just the happy path.

Cross-phase exception check: both guides carry the full "Not separately gated"
paragraph, covering the authorized draft-to-reviewed transition, ruling capture,
campaign transitions and lore/region/world edits. Its authorization cross-reference
must resolve in each guide; this is not blanket permission or a waiver of required
developer approval for context changes. The three separate encounter gates remain
in development, with planning linking there for encounter procedure. This corrects
the initial section-level allocation, which overlooked that the final paragraph
of Explicit user gates also governs planning's context edits.

## Consumers and implementation checks

Paths below are relative to `packages/crypts-and-commits/` unless stated otherwise.

| Consumer | Required follow-up |
| --- | --- |
| src/cac/core/docs.py | Add phase registrations (and common only if selected), update workflow summary to advertise an index and preserve importlib.resources loading |
| tests/core/test_docs.py | Extend actual registry/resource coverage to new names; apply 40,000-character cap to every workflow-family body; adapt old workflow-title expectations and extend repository-name leak guard with the reserved e000 exemption |
| tests/cli/test_docs.py; tests/mcp/test_docs.py | Retrieve complete bodies of every registered new guide through both surfaces, verify listing and existing continuation/error behavior; avoid fixed four-guide inventories |
| tests/core/test_skills.py | Verify new doc names/routing resolve and all six flavors preserve callable examples, metadata and ruling guidance; pair with explicit review of the three gates |
| src/cac/core/templates/skills/{claude,codex}/world_planner/SKILL.md | Route goal, readiness, triage, archival and planning branch questions to planning-workflow; link development for campaign execution detail |
| src/cac/core/templates/skills/{claude,codex}/campaign_manager/SKILL.md | Route tactics, registration, encounters and execution questions to development-workflow; retain every explicit stop-and-ask gate inline in both templates |
| src/cac/core/templates/skills/{claude,codex}/world_manager/SKILL.md | Make disclosure task-specific: planning for static context/maintenance, development for encounter procedure; preserve exact-contract and migration routes |
| src/cac/core/templates/docs/tool-reference.md | Update procedural-authority links and Docs inventory in the same registration change; no operation contracts change |
| src/cac/core/templates/docs/branching-guide.md | Route planning and execution portions to their authority; repair old workflow section references without duplicating full contracts |
| src/cac/core/templates/docs/migration-guide.md | Include new target artifacts, phase retrieval and developer redeployment; keep schema migration separate; reconcile its hard-coded guide-count wording |
| Repository CLAUDE.md | Update procedural-authority and template-doc descriptions and owning-document references |
| Repository AGENTS.md | Shared guidance is imported from CLAUDE.md; no direct workflow link requires changing this file based on the present inventory |
| Repository README.md; docs/QUICKSTART.md; package README.md | Replace claims that workflow returns the full reference with index/phase routes and useful direct links |
| Managed world, crypts-and-commits region and workflow-doc-source-of-truth lore | Recheck approved context via MCP for stale full-workflow/paired-authority wording; update only approved body/summary changes, never edit managed files directly |

The inventory above covers the cited current consumer surface. During
implementation, search the ordinary package/docs paths for additional references
to workflow and its section anchors, keeping managed records excluded. A newly
found reference is an inventory finding, not permission to broaden behavior.
Do not bundle the unrelated b004 description-accuracy sweep into this work.

## Suggested follow-up encounters

1. Implement the agreed structure and registration together with the tool
   reference, supporting guides and test adjustments needed to leave no broken
   package references. Update all six packaged skill routes in that same coherent
   change, with gates preserved inline. Obtain approval for the accompanying
   authority-lore update before changing its body and summary. Keep phase-guide
   structure open to concrete joint review rather than using allocation totals
   as an automatic acceptance decision.
2. Review the complete result jointly, repair material consistency/reference
   findings, check public and local instruction routing and developer-redeployed
   templates, and run the full checks before requesting campaign completion.
   An implementation encounter may need to be split further after design review;
   each follow-up retains independent review/open/complete gates.

There is no scheduled fresh-session testing milestone in this campaign. Record
later organic usage findings as rumors. Do not claim those observations before
they occur or hold completion open waiting for them.

## Reproducing the allocation experiment

Run this Python block from the repository root with the existing environment
(`pdm run python`), while workflow.md is still at the baseline above. It reads
only ordinary docs, builds slices in memory and writes nothing. The table is the
explicit allocation input; assertions detect missing or differently measured
slices. A later guide rewrite will intentionally invalidate this baseline.

```python
from pathlib import Path
import re

root = Path("packages/crypts-and-commits/src/cac/core/templates/docs")
source = (root / "workflow.md").read_text(encoding="utf-8")
design = Path("docs/workflow-guide-split-design.md").read_text(encoding="utf-8")
split_sections = {"Bosses", "Agent planning and campaign workflow", "Developer-only maintenance"}
units = {}
for section in re.split(r"(?m)(?=^## )", source)[1:]:
    name = section.splitlines()[0][3:]
    pieces = re.split(r"(?m)(?=^### )", section) if name in split_sections else [section]
    for piece in pieces:
        label = piece.splitlines()[0].lstrip("# ")
        assert label not in units
        units[label] = piece

gates = units["Explicit user gates"]
start = gates.index("Not separately gated:")
end = gates.index("### Review flow", start)
units["Not separately gated"] = gates[start:end]
units["Explicit user gates"] = gates[:start] + gates[end:]

allocation = re.findall(r"^\| ([^|]+) \| ([PSD]) \| (\d+) \|$", design, re.M)
groups = {key: [] for key in "PSD"}
seen = set()
for label, group, expected in allocation:
    assert label not in seen
    seen.add(label)
    assert len(units[label]) == int(expected), label
    groups[group].append(units[label])
wrappers = {"Purpose", "Agent planning and campaign workflow", "Developer-only maintenance"}
assert set(units) == seen | wrappers
assert len(source) == 43253
sizes = {key: len("".join(parts)) for key, parts in groups.items()}
assert sizes == {"P": 11642, "S": 18018, "D": 12259}
print("Baseline:", len(source))
print("A planning/development:", sizes["P"] + sizes["S"], sizes["D"] + sizes["S"])
print("B planning/development/common:", sizes["P"], sizes["D"], sizes["S"])
```

## Verification record

The allocation experiment and desk walkthroughs support joint design review;
they do not prove future-session usability. Required full-suite and Ruff results
are recorded in the encounter log after execution. Only this design artifact is
an ordinary-file deliverable of this encounter. The packaged guides, tests,
templates and managed lore remain unchanged here.
