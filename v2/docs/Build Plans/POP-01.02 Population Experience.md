# POP-01.02 Population Experience

- Status: queued; parent [POP-01](POP-01%20Population%20Campaign%20Execution%20and%20Experience.md).
- Last refreshed: 2026-10-08 20:58:22 (America/Chicago).
- Implementation: 0%; U1/U2/U3/U4=0%, four equal delivery gates.
- Prerequisite: POP-01.01 complete. Current: none; next U1 authoritative read model.
- Owners: Runtime generic execution reads; Research population/evidence projections;
  Studio bounded loaders/page models/visualization; Data protected artifact reads.
- Blockers: route and projection contracts must be reviewed at U1; proposed design
  is not an implemented endpoint. Acceptance: actual-owner browser proof pending.

## U1: authoritative population summaries and bounded queries

Reuse accepted checkpoint/selection manifests and execution records. Runtime owns
generic accepted-reference discovery and aggregate execution state at a snapshot;
Research owns population/candidate/evaluation semantics and comparable evidence.
Do not make Runtime interpret chemical properties or let Research accept executions.
Coordinate with UI-01.01's proposed result discovery contract; explicitly supersede
or reuse the reviewed decision rather than create a competing unapproved API.

Define versioned query contracts for campaign-generation summary, generation members,
candidate-method results, selection/ancestry and semantic method-node aggregates.
Each page binds tenant/project/run/search, graph/spec revision, generation, source
observation cut, filters, sort and cursor. Source changes require resnapshot, not
silently mixed pages. Authorization is checked on source artifacts as well as rows.
Permission loss clears protected detail. Projection lag is visible, with last applied
source revision; cached data is never a second execution truth.

Node aggregates explicitly distinguish planned candidate slots, generated unique
candidates, pending evaluations, invocation attempts, terminal results, exclusions,
reused results and selected survivors. Within each state axis, define mutually
exclusive categories that reconcile to the stated cohort; selection and reuse are
separate attributes, not extra candidates added to lifecycle counts. Do not sum retries as additional candidates.
One candidate can be complete for solvency and pending for viscosity. Missing pages
must not turn into zero counts. Selection/rank comes from accepted receipts only.

Page defaults50/max100 records, maximum1MiB response, bounded requested histories,
and declared count/omission/next-page fields are proposed first-profile limits.
Server-side filtering/sorting/aggregates precede paging. Plots use exact bounded
frontier queries or explicit sampled/aggregated datasets; sampling never chooses
survivors or claims the visible points are the complete population. Avoid browser
fan-out per candidate and fetching the entire history merely to hide it.

Exit: real-owner summary/page parity against source manifests; duplicate/out-of-order
notifications, cursor tampering, stale cut, missing artifact, access loss and
projection rebuild tests. Independent query plan/payload measurements recorded.

## U2: stable scientific graph plus generation navigation

Main canvas renders the admitted reusable method graph. Distinct evaluator nodes
remain named and connected; the graph must not collapse into an opaque Evaluate box.
Semantic layout size depends on authored methods, not candidate population size.
Separate edge kinds: authored dependency, data binding, iteration and drill-down
projection. Show real fan-out/join structure; aggregate display is not a new graph.

Overlay each method with selected-generation counts and states, such as 320/500
evaluations terminal and12 running, with labels specifying the denominator. Concurrent
activity requires actual overlapping execution evidence, not merely parallel topology.
Unknown totals or future generations have no invented percentage or finish-time ETA.

Generation strip shows generation zero/offspring indices, lifecycle and counts;
live versus pinned historical selection is explicit. Do not jump the user to the
latest generation while they inspect an older one. Compare-mode uses two explicit
generation contexts. Preserve pan/zoom and selection through updates/reconnect.

Selecting a method opens a bounded candidate/result list. Selecting a candidate
opens its evaluation path and concrete attempts, with breadcrumbs back to the
method graph. Expanded execution detail has a separate200-node bound and visible
omissions; no 1000-candidate graph automatically rendered offscreen.

Exit: actual state-to-screen checks for running/queued/failed/reused/partial states,
readable joins, generation transitions, keyboard/list equivalent, viewport retention
and no ordinary page overflow. Follow local UI Coding Guidelines and inspect screenshots.

## U3: population comparison, chemistry detail and lineage

U1/U2 must expose process-stage/intermediate identity separately from population
membership. Render repeated fork/merge/fork patterns across a19-stage fixture with
expandable subgraphs, local focus and bounded overview. Unequal path lengths must
not imply synchronization across visual columns. A selected combination node shows
its consumed precursor states and resulting intermediate, not only completed counts.
U3 supports backward traversal across all material inputs and forward traversal
through split outputs; keep this separate from genetic parentage and selection.
No graph width reduction may silently hide a required input or imply chemical merging
where the graph only waits for independent evaluations.

Population table includes candidate ID/name, generation membership, evaluation
completeness, feasibility, objective values/units, scientific evidence posture,
selection disposition and reason. Support filters for survivors, excluded/incomplete,
weak evidence and failures. A stopped search or empty feasible set has an explanation,
not an empty success screen. No unsupported overall recommendation score.

Use a two-objective trade-off plot first, with Pareto/constraint distinctions; add
bounded parallel-coordinate views only when dimensionality warrants them. Across
generations show counts, objective distributions, feasibility and diversity with
declared definitions. Compare only matching objective/unit/tool/context policies;
incompatible generations are side-by-side contexts without a misleading improvement
delta. If hypervolume is used, pin the reference point and normalization first.

Link a candidate to UI-02 formula/2D representation, its actual input/evaluation
artifacts, parents, operator and selection decision. Fetch lineage progressively;
cycles, missing ancestors and cross-scope links fail explicitly. Distinguish a new
candidate occurrence, unchanged survivor, duplicate attempt and equivalent material.
Do not display synthetic numerical genes as molecular structure or inherit a sample
molecule image. Chemical detail uses the exact retained representation or says absent.

Useful concerns can be attached to methods, candidates or generations and passed to
the established future-campaign Planning/Knowledge flow with exact source pins.
Do not introduce human approval inside every generation or LLM calls per candidate.

Exit: compare two actual generations, explain survival/exclusion, follow ancestry
and structure, export reproducible filter/context references and return to the same
run view. Node execution metrics and scientific performance remain distinct.

## U4: bounded load, visual verification and module boundaries

Create focused Studio transport/projection/page-model/layout/presentation modules
with replacement READMEs; extend existing components where behavior fits, do not
grow campaign_flow into a monolith. Keep scientific ranking in Search/Research.

Test1000 candidate rows and at least20 generation summaries with deterministic
recorded fixtures, labeled as visualization evidence. Real campaigns are qualified
in POP-01.03. Compare main graph node/edge count across2/128/1000 candidate datasets:
same method means same base scene size. Assert bounded requests, DOM rows, payloads
and expanded scene size, not just that SVG paths exist.

Proposed same-host browser targets: summary/table visible within2s p95 after response
availability, selection feedback within200ms, and active status within5s of an
accepted Runtime change under the declared poll/load profile. Record hardware,
network/API latency separately and test at least30 scripted interactions; a missed
target is a recorded gate failure or explicit reviewed scope change, not hidden.
Measure memory/long tasks, 1440/390 widths,200% zoom, keyboard navigation, contrast
and reduced motion. Unauthorized/stale/error/empty views must remain useful.

Exit: scoped tests, real-browser visual inspection, independent consumer install,
documented measurements and scoped drift audit. No whole-universe download fallback.
