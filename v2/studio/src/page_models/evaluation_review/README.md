# Evaluation design review

Owner: Studio / UI-01 N2.S. User: human SME evaluating the evaluation strategy.
Input is a bounded, versioned local design proposal, not a Runtime graph or an
attested Planning result. `parseDesign` validates exact fields, one objective,
unique IDs, reachable acyclic relationships, text/byte/node limits and explicit
proposal provenance. This is structural validation, never scientific acceptance.

`EvaluationReview` owns the immutable design and up to64 typed concerns against
its exact nodes. Export includes the entire unchanged design/revision plus local
unsubmitted next-campaign-only feedback; import restores both. No network, provider
calls, browser persistence, tool execution or owner mutation. Import origin text
is an author assertion, not an authenticated identity. Sources are inert text.

The renderer owns selection and unsaved form text; the workspace holds the review
while navigating. Reload loses unexported work; explicit warning and unload prompt.
Replacement imports must not silently discard current notes. Wrong/oversized input
leaves the prior review intact. Successful import resets selection to the objective.

`polymer_proposal.ts` is an explicit Codex-authored design example available only
in synthetic demo contexts. It cites read-only v1 source paths, identifies adapter
and evidence gaps, and deliberately leaves thresholds, biological applicability
and aggregation unresolved. No predicted measurements or execution records are
invented. This example is not selected by a runtime LLM or bound to the numeric run.

Owned verification: tests/page_models/evaluation_review and integration review
walkthrough. Accept SME identification/export/recovery of method, missing-criterion
and aggregation concerns; layout alone is insufficient. Follow-on owner adapter
requires exact question/proposal/tool/artifact pins and provider provenance.

The procedure field exposes bounded ordered method steps. The solvency example
quotes the implemented input validation and formula in hansen_ra_squared/hansen_red
without executing it or generalizing its scientific applicability.
