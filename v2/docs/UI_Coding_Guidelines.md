# UI Coding Guidelines

- Status: active instructions for v2 UI design and implementation; no UI implementation claimed
- Last reviewed: `2026-09-22 20:46:34` (America/Chicago)
- Owner: experience layer; used with [Development Process](Development_Process.md)
- Design authority: [Human Research Workspace](Architecture/Experience/Experience_Architecture.md)

## Provenance and Scope

Adapted at the user's request from JARVIS `Docs/UI/2.0/Architecture.md`, especially Non-Negotiable Principles, performance rules, Referential Runtime Data and Message Contract, reviewed read-only on the date above. The older `Docs/UI/1.0/UI Developer.md` supplies a general role description, not the substantive rules. This local document is self-contained; routine UI work does not require access to JARVIS.

The layout, data ownership, progressive disclosure, truthful state and realistic verification rules below carry over from JARVIS. Graph interaction, scientific evidence, visual styling and accessibility details are Amphora adaptations. JARVIS-specific Professor/session restrictions, deployment commands, permissions and numeric latency targets are not imported.

## Start with the User's Task

Before coding a surface, name its user, primary question, primary action, owning backend projection, mutation commands and information layout. Describe loading, empty, partial, stale, denied, failed and successful states. Identify the existing components and design tokens it will reuse. Put these decisions in the owning task/module contract rather than creating a parallel planning hierarchy.

Default to a working research interface: a clear focal area, compact context and detail on demand. Avoid generic dashboard scaffolding, decorative metric cards, giant introduction banners, gratuitous gradients and nested rounded panels. Typography, spacing, contrast and alignment must establish hierarchy before decoration. Use shared tokens and components; do not invent another visual language per page.

## Layout Follows Information

- Comparable records belong in sortable/filterable tables or lists. Cards serve discrete summaries or genuinely standalone objects.
- One primary growing region owns the page. Use tabs or selection-driven detail for other collections instead of stacking several expanding tables.
- Keep navigation and status bands compact and consistent. Aim for one task context per screen without hiding necessary content or forcing unreadably dense layouts.
- Give repeated context one owning surface. Elsewhere show a compact status or a link, not another full copy.
- Paginate large collections with visible totals and filters; virtualize where appropriate. Define a bounded API page size and payload expectation. The JARVIS default of 20 rows is a starting reference, not a universal Amphora constraint.
- Ordinary screens must not require horizontal scrolling. Wide scientific matrices and the explicitly pannable graph canvas are intentional exceptions with their own navigation.

## One Data Owner per Visual Region

Use `backend projection -> page/view model -> render props -> presentation components`. A page model may compose focused loaders, each owning a distinct slice. Components must not independently fetch competing copies of the same data.

Keep transport clients, view models, domain rules and presentation separate. Decompose by behavior and state ownership; avoid giant page components containing request logic, scientific rules and rendering. Module READMEs document actual responsibilities and interfaces.

Actions submit commands through the owner, then reconcile affected projections. Local selection, layout, filters and unsaved drafts are UI state. Execution, evidence, permissions and published graph revisions remain backend authority. Optimistic feedback must be visibly pending, recoverable on rejection and safe against stale responses. Expected revisions protect edits; conflicts preserve the draft and offer a meaningful reconciliation path.

Notifications invalidate the relevant slices; visible views refresh, hidden views mark stale until activation. Reconnection reconciles with authoritative reads. Avoid blanket polling and full-page refetches. This rule is transport-independent and can use the proposed SSE channel rather than inheriting JARVIS's WebSocket choice.

## Summary, Detail and Honest Status

The initial view answers what is happening, what is blocked, what needs the user and where to inspect the evidence. Fetch heavy detail when selected. A slow section must not freeze the whole workspace.

Use stable linked objects for runs, node invocations, candidates, experiments and artifacts. Users should never need to copy an opaque ID to follow a result. Tool and capability menus come from scoped registry projections, not hardcoded lists of polymers or biological tools.

Show lifecycle outcome as well as compute status: a calculation can finish while its result is unvalidated, rejected or awaiting adoption. Distinguish execution failure, scientific infeasibility and missing evidence. Display acceptance, start, completion and rendering times accurately; never fabricate durations or progress percentages.

Keep prompt scaffolding, routing traces, raw payloads and implementation diagnostics in inspectable technical detail. Primary workflows show the scientific result, uncertainty, actionable errors and provenance. LLM chat shows user-facing answers and linked proposals; generated drafts do not masquerade as accepted knowledge or active graph changes.

## Amphora Graph and Evidence Interaction

Initial-profile interaction: live campaigns are autonomous and inspectable; human edits are next-campaign drafts. Do not insert required human approval steps or live scientific-edit controls. Preview/validation/activation flows below apply between campaigns. Emergency termination remains a separate operational control with truthful in-flight-effect status.

Give Graph Studio a primary canvas with scoped navigation and selection-driven inspectors. Clearly distinguish campaign, domain and derived lineage views, and show which revision/run/iteration is being inspected. Keep graph layout preferences separate from executable topology.

Large graphs require bounded subgraph queries, clustering or progressive expansion with visible scope and omission counts. Do not download the entire knowledge universe merely to hide most of it in the browser. Preserve selection, viewport and draft work across refreshes. Supply searchable lists and keyboard-accessible details alongside canvas interaction.

Proposed edits need a readable diff, affected scope and validation result before activation. Running, draft and historical graphs must be visibly distinct. Evidence views distinguish measured, predicted and hypothesized claims and expose source, uncertainty and applicability. Color alone cannot encode these distinctions.

## Accessibility and Verification

Use semantic controls, accessible names, visible focus, keyboard navigation and sensible focus restoration after dialogs/actions. Check contrast, zoom, reduced motion, long labels and narrow layouts. A graph canvas does not excuse inaccessible essential actions.

For each meaningful UI delivery, render and inspect the actual screen at its intended viewport and a narrower size. Exercise the primary task, loading/error/empty states and long or numerous records. Check overflow, overlays, tab order and preserved selection. A successful build alone is not visual acceptance.

Use focused component checks for presentation states and actual backend integration for authority, permissions and mutations. Recorded realistic fixtures can supplement large-data and failure scenarios, but label fixture evidence clearly. Relevant workflow checks include reconnect/stale revisions, a slow worker, duplicate notifications, rejected graph edits and completed-but-unaccepted results. Report what was actually inspected; browser or backend unavailability remains an explicit verification gap.

Update the owning module contract and plan evidence when behavior changes. This guidance does not add a separate approval ceremony or select a frontend framework.
