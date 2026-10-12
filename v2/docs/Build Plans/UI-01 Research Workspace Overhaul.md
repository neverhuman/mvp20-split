# UI-01 Research Workspace Overhaul

## Canonical tracker

- Status: primary_active; connected demo flow implemented; N2 complete; approved N3 curation implementation active.
- Last refreshed: 2026-10-12 00:05:20 (America/Chicago).
- Baseline: 62ea4966; owner-reported disconnected canvas and navigation review on 2026-10-07.
- Owner: Studio experience, page models and presentation; service owners retain their contracts and state.
- Parent: none; priority and mirrors in [Master Build Tracker](Master%20Build%20Tracker.md).
- Overall implementation: **66.89%**; Build83.61%, Verification0%. Five equal delivery gates: G1, N1, N2, N3, V1. Build averages G1/N1/N2/N3; Verification is V1. G0 is a separate design/review prerequisite and earns no implementation credit.
- Design readiness: G0 complete; ELK directed layout and bounded topology ownership implemented.
- Demonstrated behavior: connected graphs and question-first navigation verified against retained owner records; result-first comparison and full replacement acceptance remain.
- Current phase/task: N3/UI-01.05/I1; implementing approved [UI-01.08](UI-01.08%20Campaign%20curation%20boundary%20decision.md). N2 complete100%; launch/provenance remain closed.
- Next task: UI-01.08/P2.3c.3 managed lifecycle, heartbeat and process recovery. P1=100%, P2=72.22%; N3/I1=34.44%.
- Blocker: none for approved curation work. UI-01.01 public result index remains separate/unapproved; use the authorized bounded existing-API alternative.
- Human acceptance: owner feedback is part of visual review; no new routine approval gates for campaign execution.
- Active exception: owner explicitly reprioritized UI over worker diagnostics; LR-01 remains paused at25%, Build33.33%, Acceptance0%, with R2 receipt diagnosis preserved.
- Pre-activation coherence: 2026-10-07 17:54:00, ready for G0. Existing topology/observation APIs, React Flow canvas and isolated Studio boundaries are available; meaningful layout and workflow acceptance are missing. No new backend contract is assumed approved by this plan.

| Phase | Completion | Prerequisite | Bounded outcome / exit gate |
|---|---:|---|---|
| G0 graph review and design | 100% | Owner report and retained campaign | Recorded actual-screen diagnosis, topology/data map, layout design and graph acceptance cases |
| G1 usable connected graph | 100% | G0 complete | One real retained campaign opens as a readable connected graph; branches, joins and nested work navigable; visual and behavioral proof |
| N1 research entry and navigation | 100% | G1 complete | Research-question landing and connected workflow navigation with preserved selection/context |
| N2 approach, execution and results | 100% | N1 complete | Understand approach, follow autonomous work, inspect/compare results and supporting evidence |
| N3 next-campaign iteration | 34.44% | N2 complete | Target weak/promising points, inspect proposed changes and follow predecessor/successor history |
| V1 integrated acceptance and audit | 0% | N3 complete | Actual-owner user journey, independent consumer acceptance, scoped audit and explicit limitations |

Each phase is a discrete unit of work. Complete its exit gate before dependent
implementation. Expand the nearest phase into owned tasks as evidence warrants;
do not create empty child plans or count plan-writing as delivered functionality.

## Objective and boundaries

Owner schedule2026-10-08: target the week2026-10-12 through2026-10-16 for actual
Knowledge UI, browser-started campaigns with live per-node progress, and LLM graph
revision grounded in Knowledge. [UI-01.05](UI-01.05%20Knowledge%20Run%20and%20LLM%20Integration.md)
decomposes this existing unfinished N2/N3 scope: K1=100%, R1=100%, I1=0%. N2.2 owns service
provenance, N2.4 Knowledge/reasoning and honest node-quality evidence, N2.5 admission/
worker engagement, and N3 the between-campaign LLM/successor loop. Complete all N2
gates, including remaining comparison, before dependent N3 work. V1 verifies the
combined journey. No additional parent task weight or implementation credit is
introduced by this decomposition. Qualified R1 completes N2.5, yielding
overall56.25%/Build70.31%/N2=81.25%; other N2 groups retain their earned credit.
Formula/structure production and visualization belong to UI-02, with an explicit
handoff of retained candidate references rather than duplicated Studio chemistry.
Owner sequencing clarification2026-10-08 19:07:02: complete the end-to-end gate,
including inventory-fed LLM curation and durable new-capability requests under
UI-01.05/I1, before standalone ML-01 inherited-model migration. Preserve current
phase credit; N3 remains0%. This is a prerequisite sequence, not a calendar shortcut.
Owner refinement2026-10-08 20:19:11: after this workflow and UI-02, complete
[POP-01](POP-01%20Population%20Campaign%20Execution%20and%20Experience.md) population
execution/experience before ML-01. Do not pull the population-scale tranche into
the current Knowledge/LLM demonstration or reopen completed graph-layout phases.

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

## G0 review checkpoint

2026-10-07 17:36:30: G0 complete100%; implementation remains0%. Reviewed the actual retained
original-focus-d/execution-1440.png and authored-1440.png against source: default
39 activation nodes, no links; two clicks (Authored graph, Root graph) reach9 root
nodes with links, still list-ordered grid. Same bounded campaign is the replacement
oracle; source is monitor_workspace/navigation_pane/GraphCanvas plus NavigationModel.
Runtime scope/topology pages provide exact authored control links and child scope
counts. They do not publish a universal dataflow graph; do not invent those edges.

Selected ELK layered layout behind a Studio-owned geometry adapter, with explicit
node dimensions, top-to-bottom ports and orthogonal routed connections. React Flow
remains renderer. Source: https://github.com/kieler/elkjs. Exact dependency pinned
in package-lock. Layout is local, bounded to the existing200-node window, deterministic
input ordering and no graph mutation; asynchronous results must be fenced on scope
change. Layout failure must be explicit, not silently fall back to a grid. Initial
fit and saved per-scope viewport are distinct. Expanded occurrences remain separate
bounded scenes with root navigation and exact iteration labels.

G1 checks: branch/join and disconnected/cyclic geometry, long labels, empty/invalid
edge endpoints, stale async layout; source-target routing and node intersections;
automatic root, scope changes and viewport retention; real1440/390 canvas visibility,
keyboard/list equivalence, zero document overflow, contrast and actual retained
campaign screenshot comparison. Existing API permissions and omissions remain.

## G1 implementation checkpoint - 2026-10-07 17:54:00

ELK0.12 routes authored links in dependency order; root loads automatically.
Scope-keyed canvases fit after measurement; scope viewports survive refresh.
Parallel/iteration counts link to exact occurrence groups; inventory is a list.
291 Studio tests pass. Navigation, dense navigation, monitor and drafts browser
regressions pass. A legacy pan assertion assumed fixed-grid x=24; replacement
waits for the actual 100px movement before testing retained viewport.
Actual-owner evidence: `../../.test-results/ui01-g1/browser-e/evidence.json` and
root1440/390, parallel-group and iteration screenshots. Reviewed connected paths,
no overlap, automatic fit, nested navigation, selection, refresh, accessibility.
Browser-d exposed automatic-fit timing failure; retained as failed evidence.
Candidate assets public-e only; frozen demo remains unchanged pending integrated
replacement qualification. Header/control density remains N1/N2 scope.

## N1 checkpoint - 2026-10-07 18:00:00

Question-first landing uses exact Research question/need pins; optional assessment
reads cannot hide the objective. Four connected perspectives group the workflow:
Question / Approach and run / Results and evidence / Next iteration. Navigation
retains mounted selections/viewports; allowlisted URL view restores on reload.
Missing/invalid pins and denied reads stay explicit; launch ticket is erased.
292 Studio tests pass. Actual-owner workflow browser-a passes real question,
criteria, graph selection/viewport roundtrip, reload and 1440/390 accessibility.
Evidence `../../.test-results/ui01-n1/browser-a/evidence.json`; both landing images
reviewed. N2 still owns inner-view density, result-first hierarchy and comparison.

## N2 bounded task tracker - 2026-10-07 18:07:35

Eight equal tasks define N2 credit: all eight complete give100%. Proposed public-contract additions require an
explicit scope/denominator update after the owner decision; they earn no credit now.

| Task | Completion | Exit |
|---|---:|---|
| N2.E scientific execution | 100% | [Scientific execution MVP](UI-01.03%20Scientific%20Execution%20MVP.md): actual solvency/viscosity tool invocations with retained evidence |
| N2.S SME evaluation review | 100% | [MVP task](UI-01.02%20SME%20Evaluation%20Review%20MVP.md); inspect and challenge criteria, methods, assumptions and aggregation before further result work |
| N2.C visible concurrency | 100% | Inline sibling branches and joins in campaign context; actual-state/omission proof and SME-visible behavior before result work |
| N2.1 screen hierarchy | 100% | Single shell, compact execution status/actions, secondary technical controls, truthful absent-result notice |
| N2.2 participating capabilities and result discovery | 100% | Retained plan/bounded discovery and exact Planning/Research provenance qualified; UI-01.07 audit |
| N2.3 typed results and comparison | 100% | Candidate and bounded retained-generation comparison qualified |
| N2.4 evidence and reasoning traversal | 100% | Actual domain/source traversal and exact retained OpenAI request/response/rationale/outcome qualified |
| N2.5 actual-owner acceptance | 100% | Retained walkthrough plus actual local/LAN browser admission/workers/results, same-run/container recovery and installed replacement qualification; UI-01.06 closeout audit |

Each remaining N2 task has two equally scoped delivery groups named in its row.
[UI-01.04](UI-01.04%20Connected%20Demo%20Flow.md) proves the first group; it does not
claim full Runtime LLM orchestration, launch controls or generational discovery.
Next-iteration review export is pulled into this demo by owner direction, without
crediting N3 successor execution. UI-01.01's new public index remains unapproved;
the demo uses its bounded existing-API consumer alternative. No closed plan reopened.

292 Studio checks pass on N2 source. Isolated gateway checks use retained owner
APIs with candidate assets; no execution/model calls. Final evidence is under
`../../.test-results/ui01-n2/`. Earlier graph-a/b denied session exchange because
browser probes exhausted the existing gateway's eight-session ceiling; probes now
log out, and separate gateway checks avoid affecting the user session. This is
not an authentication bypass or a repaired scientific-worker reliability claim.
Frozen demo assets remain unchanged; V1 still owns full replacement qualification.

Final N2.1 evidence: isolated workflow and graph reviews both PASS against retained
owner APIs, `workflow-isolated-b` and `graph-isolated-b`; gateway closed cleanly.
Execution screenshot reviewed after compact action/scope layout. Candidate public-b
remains separate from the frozen demo. Browser session exhaustion evidence is
retained, and future probes revoke their own sessions on exit.

## Owner review availability correction - 2026-10-07 19:43:04

Owner reported UI unavailable. Previous2hour session ended normally at18:08:26;
all7owners drained. Latest public-b UI is now served as an explicit review preview
at http://127.0.0.1:57013. Session20261007-194053-57ebf095 opened19:41:56 and has a
24hour window through2026-10-08 19:41:56CT. Launcher defaults24h and snapshots
selected preview assets without overwriting the frozen baseline. Actual HTTP hashes
and served-asset workflow browser passed; evidence ui01-live-review-20261007.
This restores owner review; it does not imply approval of UI-01.01 or V1 completion.

## Visible-concurrency correction - 2026-10-07 19:48:12

Owner requires concurrency to be directly visible to an SME. G1 proved routing and
isolated nested navigation, not simultaneous sibling visibility. Preserve historical
bounded G1 credit; it is not full graph acceptance. Add N2.C before remaining N2 work.
N2 denominator grows5->6, completion20->16.67%; overall44->43.33%, Build55->54.17%.
No closed plan reopened. V1 cannot pass without visible-concurrency acceptance.

Show fan-out/siblings/join on one canvas, named tools, authoritative states, stable
occurrence/read-cut identity, bounded load and explicit omissions. Distinguish
parallel topology from observed execution overlap. Do not create synthetic execution
links across scopes; identify container boundaries and real control/data relations.
Test a slow sibling, completed sibling, failure/wait and nested generation without
hiding other branches. The current numeric demo is not the polymer formulation
baseline. Solvency is absent from that campaign, not hidden by its canvas. A
representative formulation campaign must distinguish actual tools from planned or
synthetic replacements. No fabricated solvency execution or scientific result.

## N2.C delivery checkpoint - 2026-10-07 20:13:27

Studio0.18 InlineScopes reads sibling topologies at the parent snapshot token/cut.
Root scatter expands on opening; siblings and joins remain on the same canvas.
Iterations expand in sequence and retain nested parallel groups. Real activation
states and selection are preserved. Dashed scope-entry/completion/continuation
edges and synthetic rounded completion boundaries are distinct from authored links.
No additional executable tool, solvency evaluation or observed CPU overlap is claimed.

Bounds: four siblings/group, eight groups, depth3 and200nodes; omissions visible.
Read cancellation, denial, mismatched cuts/identity and refresh restoration covered.
Focus expanded work preserves readability; pannable overview map and Fit graph
retain whole-projection navigation. The all-generations overview requires zoom to
read labels. Manual focus uses tested geometry instead of a queued renderer fit
that lost focus during refresh; failed browser-e evidence retained.

301 Studio tests pass. Navigation, dense-navigation and drafts browser regressions
pass. Actual SERVED concurrency/workflow checks PASS under ui01-concurrency/
concurrency-g-served and workflow-g-served. Checks include 14node initial fan-out,
43node expansion of all generations (39 real activations plus4display boundaries),
restoring all expansions after refresh, real node detail, 1440/390 accessibility,
and a separately labelled intercepted failed-sibling/blocked-join presentation
fixture. The failure fixture never changes owner records or the user's browser.

Live preview http://127.0.0.1:57013; session20261007-200936-1106c8c9. Started
2026-10-07 20:10:37CT, scheduled stop2026-10-08 20:10:37CT. Immutable copy of
public-g; real HTTP asset hashes match ready.json. Previous preview drained all
seven owners before startup. No workers/provider calls. Owner review pending;
N2.C scoped work100, N2=33.33, overall46.67, Build58.33, Verification0.

## SME acceptance correction - 2026-10-07 23:08:25

Owner explicitly rejected generic parallel evaluator instances as product delivery.
Added N2.S as a seventh equal task: denominator reset N2 from33.33 to28.57 before
implementation; completion of the local review MVP brings N2 to42.86, overall48.57,
Build60.71. G1/N2.C retain infrastructure credit only. [UI-01.02](UI-01.02%20SME%20Evaluation%20Review%20MVP.md)
owns bounded scope and evidence. SME inspection of criteria, evaluation procedures,
assumptions and aggregation is now mandatory product acceptance, independent of
execution monitoring. Future N2.2 must bind actual retained Planning proposals,
Research criteria and registered tools; a local authored proposal is not that link.

2026-10-11 19:26:42: UI-01.07 complete100% with [provenance audit](../Audits/UI-01.07_Campaign_Provenance.md).
N2.2=100%, N2=87.5%, overall57.5%, Build71.88%, Verification0%. Actual local/LAN
Research/Knowledge origin traversal and original-run completion pass; deterministic
provider earns no N2.4/N3 credit. N2.3 generational comparison is the next task.

## N2.3 retained generation checkpoint

2026-10-11 19:44:00 America/Chicago: exact published search schema, bounded100-node/128-output
discovery, two explicit protected checkpoint selections, objective/candidate comparison
and workspace presentation implemented.13 focused/362 full Studio checks pass;
scripted1440/390 browser passes. Actual original retained campaign qualification
and scoped audit remain. N2.3 stays50% until its second delivery group passes.
No population-wave engine, new Runtime result index or scientific validity claimed.

2026-10-11 19:50:00: N2.3 second group qualified100%; parentN2=93.75%,
overall58.75%, Build73.44%, Verification0%. [Scoped audit](../Audits/UI-01_N2.3_Generation_Comparison.md)
records actual retained generations0/2,362 tests, desktop/narrow inspection and
restored original-run LAN regression. N2.4 live-provider reasoning is next.

N2.4 scope checkpoint2026-10-11 19:55:00: reuse actual retained BP09 OpenAI
request/context/response/capture/outcome via existing public inspection contracts.
Expose direct results/run navigation; qualify original history and honest empty
scientific-campaign state. No new paid call or new campaign-input profile is needed
for this read-only gate. Live graph conversation remains N3/I1.

2026-10-11 21:11:13: N2.4 second group complete100%, N2=100%, overall60%,
Build75%, Verification0%. [Scoped reasoning audit](../Audits/UI-01_N2.4_Recorded_Model_Inspection.md)
records actual retained OpenAI request/rationale/outcome,362tests, desktop/narrow
and restored LAN unavailable-history regression. Zero new paid calls. N3/I1
requires the concrete additive public boundaries in UI-01.08; no code for those
unapproved boundaries is implemented.
