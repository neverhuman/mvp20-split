# RG-01 LLM Research Graph Generation

## Canonical tracker

- Status: critical successor placeholder; queued immediately after POP-01, before ML-01.
- Last refreshed: 2026-10-14 21:14:16 America/Chicago.
- Owner direction: the LLM generates and improves the research graph. Knowledge enhances that ability with context; it is not the generator or a prerequisite populated corpus.
- Priority: [Master Build Tracker](Master%20Build%20Tracker.md). No implementation activated by this placeholder.
- Owners: Planning owns model generation/proposals; Knowledge owns durable graph revisions and structural acceptance; Studio owns visualization; Runtime alone owns execution.
- Overall: 0%; four equal gates. Build: 0% (R1/R2/R3 mean); Verification: 0% (V1). Every phase below is 0%.
- Current task: none until POP-01 completes. Next: bounded activation audit and R1 contract/behavior review.
- Evidence: existing extraction/proposal/owner-handoff seams exist; the current live campaign-curation call is not evidence of this research-graph workflow.
- Blockers: none to planning. Exact contracts, supported model configuration and bounded qualification allowance are resolved at activation.
- Acceptance: usable LLM-generated research graphs and subsequent improvements through actual owner APIs and Studio; source-only or scripted fixtures cannot close V1.
- Active exception: owner-requested planning interruption; return to POP-01.01 E2 afterward.

## Required behavior

From a research objective, the LLM must generate a coherent research/domain graph
using its own capabilities, including concepts, relationships, questions, hypotheses,
uncertainties and useful research directions. This is distinct from the executable
campaign graph and derived execution lineage. Exact record types are reviewed in R1.

Selected Knowledge supplies additional domain context, prior results, evidence,
constraints and contradictions. It should improve generation and refinement without
restricting the model to rearranging existing nodes or extracting supplied sources.
An empty or sparse Knowledge graph must still permit useful generation. Source
extraction remains a supporting capability, not the whole generation workflow.

Persist model-attributed proposals through Knowledge's public revision/acceptance
boundary. Preserve the difference between model inference, sourced assertions,
measured results and unresolved hypotheses; model output does not become proven
science merely by entering the graph. Subsequent calls can expand, challenge and
improve earlier graph revisions. Keep original revisions and provenance, and preserve
active campaign pins; changes inform future campaigns under the existing policy.

## Delivery outline

| Gate | Completion | Delivery and exit |
|---|---:|---|
| R1: boundary and gap review | 0% | Trace the actual live call, existing proposal/publication seams and UI; specify initial generation versus refinement, typed output and acceptance criteria. Reconcile architecture claims with this owner correction. |
| R2: first-class LLM generation | 0% | Generate and retain a research graph from an objective with empty/sparse Knowledge. Publish through actual owner boundaries and expose it in Studio, separately from campaign execution. |
| R3: Knowledge-enhanced refinement | 0% | Add selected context and prior graph revisions to subsequent calls; retain attributed, inspectable changes, contradictions and uncertainties without overwriting history. |
| V1: usable-path qualification | 0% | Actual supported-model generation and refinement, useful graph inspection, replay/restart and scoped drift audit. Compare empty-context and Knowledge-enhanced cases; do not claim scientific validation from software acceptance. |

KB-01 remains a separate corpus-content successor and is not a prerequisite for
generation. Reuse existing seams after review; do not reopen completed plans or
implement a second execution engine. Activation decomposes this outline into bounded
tasks without inventing a manual corpus requirement or blanket human gates per call.
