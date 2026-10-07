# UI-01 Research Workspace Overhaul

## Canonical tracker

- Status: primary_active; initial scope planned, graph review is the first gate.
- Last refreshed: 2026-10-07 17:30:53 (America/Chicago).
- Baseline: 62ea4966; owner-reported disconnected canvas and navigation review on 2026-10-07.
- Owner: Studio experience, page models and presentation; service owners retain their contracts and state.
- Parent: none; priority and mirrors in [Master Build Tracker](Master%20Build%20Tracker.md).
- Overall implementation: **0%**; Build0%, Verification0%. Five equal delivery gates: G1, N1, N2, N3, V1. Build averages G1/N1/N2/N3; Verification is V1. G0 is a separate design/review prerequisite and earns no implementation credit.
- Design readiness: initial workflow and defect evidence identified; G0 review and bounded graph design remain.
- Demonstrated behavior: existing UI displays records; owner review exposed unusable graph presentation. Previous passing checks do not establish this plan's usability acceptance.
- Current phase/task: G0.1, review the actual default and authored graph paths against one retained campaign.
- Next task: G0.2, specify graph composition/layout and behavioral acceptance before G1 implementation.
- Blockers: none for graph review/planning. Missing producer capabilities must be identified before dependent UI work, not represented by fabricated results.
- Human acceptance: owner feedback is part of visual review; no new routine approval gates for campaign execution.
- Active exception: owner explicitly reprioritized UI over worker diagnostics; LR-01 remains paused at25%, Build33.33%, Acceptance0%, with R2 receipt diagnosis preserved.
- Pre-activation coherence: 2026-10-07 17:30:53, ready for G0. Existing topology/observation APIs, React Flow canvas and isolated Studio boundaries are available; meaningful layout and workflow acceptance are missing. No new backend contract is assumed approved by this plan.

| Phase | Completion | Prerequisite | Bounded outcome / exit gate |
|---|---:|---|---|
| G0 graph review and design | 0% | Owner report and retained campaign | Recorded actual-screen diagnosis, topology/data map, layout design and graph acceptance cases |
| G1 usable connected graph | 0% | G0 complete | One real retained campaign opens as a readable connected graph; branches, joins and nested work navigable; visual and behavioral proof |
| N1 research entry and navigation | 0% | G1 complete | Research-question landing and connected workflow navigation with preserved selection/context |
| N2 approach, execution and results | 0% | N1 complete | Understand approach, follow autonomous work, inspect/compare results and supporting evidence |
| N3 next-campaign iteration | 0% | N2 complete | Target weak/promising points, inspect proposed changes and follow predecessor/successor history |
| V1 integrated acceptance and audit | 0% | N3 complete | Actual-owner user journey, independent consumer acceptance, scoped audit and explicit limitations |

Each phase is a discrete unit of work. Complete its exit gate before dependent
implementation. Expand the nearest phase into owned tasks as evidence warrants;
do not create empty child plans or count plan-writing as delivered functionality.

## Objective and boundaries

An internal researcher should understand the question, the approach, what happened,
what the evidence supports, and what to explore next. The graph is the primary
interactive workspace; technical inventories and receipts belong in drill-down.

Authority: [Studio architecture](../Architecture/Experience/Studio.md),
[human graph requirements](../Architecture/Requirements/Product_Requirements.md#human-graph-studio),
[UI guidelines](../UI_Coding_Guidelines.md),
[interaction references](../Architecture/Experience/Interaction_References.md) and
[Studio module boundary](../../studio/README.md).

Keep transport, page models, graph layout and rendering functionally isolated.
Runtime owns executable topology and execution acceptance; Research/Knowledge own
evidence and claims; Planning owns proposals. Local layout and selection cannot
rewrite those records. Human edits target future campaigns; current campaigns run
autonomously. Scientific uncertainty never becomes an execution failure by default.

This is a successor to closed Studio plans, not their reopening. It does not claim
new scientific validity, unrestricted LLM graph generation, multi-user operation or
worker reliability. Preserve the separately qualified demo assets as a comparison
and fallback; build and qualify replacement assets separately before switching.

## G0 — Graph review first

1. **G0.1 actual-screen baseline.** Review the default route and authored route on
   the retained demo campaign. Record screenshots, viewport, selected scope,
   node/edge counts and the clicks needed to reach a connected graph. Include the
   owner's reported experience; don't substitute a small idealized fixture.
2. **G0.2 explain the defects and define the replacement boundary.** Current
   Monitor defaults to activation inventory, passes no edges, and positions nodes
   in four fixed columns. NavigationPane uses the same grid even with authored
   edges. Inspect the shared canvas, topology page model, nested scope semantics,
   selection and viewport ownership. Distinguish authored control links, data
   dependencies and derived execution lineage; never invent links from proximity
   or response ordering. Record what existing public APIs can actually supply.
3. **G0.3 layout/interaction specification.** Define a consistent flow direction,
   dependency-based ranks, branches/joins, spacing based on node dimensions,
   readable edge routing/arrowheads and group expansion. Define initial fit,
   pan/zoom, selection highlighting, breadcrumbs and stable refresh behavior.
   Resolve layout-engine choice at this gate with a bounded prototype if needed.

Exit: reproducible defect baseline plus focused design and measurable acceptance
cases. Existing screenshot/DOM checks are evidence inputs, not this gate's completion.

## G1 — Make one real campaign readable

- Open the connected campaign graph by default; automatically load its root scope.
  Put execution inventory in a secondary table/list, not an unconnected canvas.
- Position by actual dependencies, with visible direction and readable labels;
  route edges around nodes and reduce crossings. Do not treat a four-column grid
  or merely present SVG paths as successful graph layout.
- Group repeated iterations and parallel work, show counts/status and expand on
  demand. Preserve exact occurrence identity and provide a clear way back.
- Fit the initial graph to its canvas; retain user pan/zoom and selection across
  refresh. Offer fit-to-view and selected-node reveal. Highlight relevant incoming
  and outgoing connections without losing surrounding context.
- Make partial topology, omitted nodes/links, loading, empty, denied, stale and
  failed states explicit. Keep keyboard and list equivalents.

Exit: reviewed actual campaign screenshots and interaction evidence at desktop and
narrow widths; connected paths traceable from start through branches/joins to end;
no node overlaps or edges hidden beneath unrelated nodes in the accepted cases.
Cover nested iteration/scatter, long labels and a bounded large graph separately.
Add module-owned layout/scene invariants and real-browser geometry/visibility checks.
Edge DOM existence alone is insufficient. Record unresolved visual defects honestly.

## N1 — Research entry and connected navigation

Land on the research question: objective, evidence available, uncertainty, campaign
intent and status. Organize the workflow around **Question → Approach → Run →
Results → Next iteration**; these are task stages, not necessarily five separate
pages or five top-level tabs. Choose the final information hierarchy in this phase.

Preserve project, campaign, revision, selected candidate/claim and relevant viewport
as users navigate. Campaign graph and domain graph are connected perspectives on
the same research, with explicit cross-links and return paths. Keep opaque IDs,
receipts and implementation terminology in technical detail. State clearly when
the user is viewing a draft, a running campaign or retained history.

Exit: a user can identify the research purpose and next useful action from the
landing view, and navigate out and back without reconstructing their context.
Verify refresh/deep-link behavior and cancellation of hidden views.

## N2 — Understand approach, execution and results

- **Approach:** explain the participating tools, data sources and models and their
  relationships. Provide graph inspection and future-draft editing. Scope LLM
  explanation/revision to actual supported proposal contracts; expose capability
  gaps before implementing a control that implies unavailable behavior.
- **Run:** show autonomous progress, parallel work, failures and retained LLM
  decisions in ordinary language, with technical evidence on demand. Stage human
  changes for later campaigns. Distinguish successful execution from strong science.
- **Results:** start with candidates/results/claims, then trace to inputs, tools,
  model decisions and domain evidence. Make generation/campaign comparison a
  primary task with exact comparable context and visible missing/uncertain evidence.

Exit: actual retained results can be followed back to their evidence and compared
without inventing fitness, accuracy, causation or scientific improvement. Data
permission failures clear protected detail. Producer gaps require a named bounded
contract task before dependent functionality, not an inert or misleading control.

## N3 — Prepare the next iteration

Select promising results and weak/questionable points; describe intended improvement
and expected learning. Inspect the engine's retained next-campaign proposal and its
relationship to those points, including unresolved items. Present changes against
the predecessor and preserve navigation to both campaign histories.

Reuse SQ-01 focus/criterion/proposal boundaries. Clearly separate a local focus
draft, a retained AI proposal, a validated campaign draft and an admitted successor.
Expose supported validation/admission through existing authoritative commands;
missing live-model support remains visible and cannot be simulated as production.

Exit: demonstrate the complete between-campaign interaction with a documented
fixture/provider boundary and unchanged prior history. Several unresolved points
must remain compatible with useful progress; no routine in-campaign approval queue.

## V1 — Acceptance that matches the user's task

Walk the actual local UI from question through approach, graph inspection, results
and next iteration. Inspect real rendered screens, keyboard behavior, browser zoom,
desktop/narrow layout, failures and context preservation. Verify independent Studio
installation against public contracts; record exactly what was replaced or rebuilt.
Tests remain in module-owned folders with scoped commands and coverage gaps.

Perform a component-scoped architecture drift audit, update touched module READMEs,
assign nonblocking findings and archive only when the defined gates are satisfied.
User-facing readiness must not be inferred from test counts or backend completion.

## Future additions and scope control

This is the initial bounded tranche, not a claim that the UI backlog is complete.
Add owner feedback as named items with phase, dependency and acceptance criteria.
Unscoped ideas receive no percentage weight. If accepted scope grows, revise the
denominator and remaining-work estimate visibly; substantial work after closure
belongs in a successor. Keep this tracker compact and create a companion history
when completed checkpoints warrant it.

UI-R01 retains the intermittent feedback-read investigation; pull it forward if it
blocks a UI-01 gate rather than duplicating diagnosis. LR-01 resumes at R2 only
after the UI priority is released; finishing a UI viewing session no longer resumes
worker diagnostics automatically. No application code changes are part of this
initial planning checkpoint.
