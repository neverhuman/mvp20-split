# UI-02 Candidate Structure and Recommendation Views

## Canonical tracker

- Status: complete100%; component-audited and archived. Closed scope stays closed.
- Last refreshed: 2026-10-13 18:16:04 (America/Chicago).
- Overall implementation:100%; Build100%, Verification100%; P1/P2/P3/P4=100%.
- Owner: Studio candidate inspection; tools own representation, Runtime execution,
  Data artifacts and Research candidate identity.
- Current task: none. Next plan: POP-01 activation/compatibility gate, then ML-01.
- Latest checkpoint: Studio0.36;473 full Studio tests, production boundary guard,
  scripted/actual-owner local and LAN browsers, existing scalar/Knowledge/curation
  journey regression, held-example invitation/drain all pass. No model calls.
- Blockers: none for this bounded plan. Molecular ranking, property and synthesis
  evidence absent; supplied finite molecule remains explicitly unranked.
- Acceptance: actual installed owner/Gateway1440/390/200% proof and audit complete.
  Frozen serving h qualified, priorf preserved. Wrappers drained during source work;
  live availability and scientific acceptance are separate from implementation100%.
- Audit: [candidate inspector](../../Audits/UI-02_Candidate_Inspector.md),
  [P1 producer](../../Audits/UI-02_Chemical_Representation.md).
- Handoff: [supplied structure review](../../Demo/Candidate_Structure_Review.md).
- Parent: none; [MBT](../Master%20Build%20Tracker.md) owns successor priority.

## User outcome and current gap

From Results, an SME can open a recommended candidate and see what it is, why it
was selected, which alternatives were considered, and which evidence is missing.
The current demo compares two supplied Hansen/viscosity parameter sets. It has no
generated polymer structure and no overall winner. A renderer cannot recover a
chemical structure from those parameters or turn them into a recommendation.

## Bounded first delivery

Owner's weekly target explicitly includes the **chemical formula and molecule
visualization**. P1 must include a real candidate-representation producer dependency:
an independently packaged scientific tool that accepts or generates explicit
structures, validates them and retains a versioned normalized representation plus
derived formula. A declared input structure can support the first bounded demo;
label it as supplied, and do not call it generated or optimized. If demonstrating
generation, the producing tool and graph node must actually execute. Identify source
reuse and missing contracts in P1 before choosing that route. Structure and property
artifacts must share exact candidate identity; do not attach a convenient molecule
to the existing synthetic scalar fixtures or guess chemistry from those parameters.

Formula semantics must match the representation: full molecular formula for a
fully specified molecule/finite chain; repeat-unit formula and symbolic degree of
polymerization/end-group assumptions for an unspecified polymer; component formulas
and composition for mixtures. Unknown chain length/distribution must not become an
invented exact molecular formula. The displayed2D structure and formula must derive
from the same retained representation, with explicit unavailable/invalid states.

Week handoff: UI-01 supplies real run/result navigation; P1 supplies candidate
contracts/tool output, P2 selection evidence, P3 formula/structure detail, and P4
the actual browser proof. Show candidates even when unranked; use Recommended only
when the retained policy/evidence supports it. Thu2026-10-15 is the target for P3,
Fri2026-10-16 for P4, conditional on P1/P2 completion. These are scheduling targets,
not permission to bypass producer or selection gates. P1/P2/P3 are100%; P4 is complete100%.

Show a two-dimensional chemical structure or polymer repeat-unit representation,
with composition and available architecture details: connectivity/attachment points,
end groups, copolymer arrangement, and chain-length or molecular-weight distribution
when supplied. Unknown details stay explicit; a repeat unit is not a fully specified
chain. Formulations need a component/composition view rather than a fabricated molecule.
Use typed representation adapters so biological molecules and other candidate types
can have appropriate renderers without forcing them into polymer assumptions.

Alongside the representation, show predicted and measured properties with units,
conditions, provenance and uncertainty; synthesis-feasibility evidence or unknown
status; and traceable links to evaluation steps and source artifacts. Recommendation
details must name the campaign's objective, constraints, selection policy/weights,
trade-offs and evaluation snapshot. Support a recommended set or Pareto frontier;
do not force every campaign to declare one winner. No policy or insufficient
evidence means an explicit unranked candidate view, not an inferred recommendation.

Candidate identity, revision, generation/ancestry where available, and content hashes
must bind structure, properties and selection evidence to the same retained record.
Results-to-candidate-to-execution navigation must preserve campaign/read-cut context.
Keep illustrative, generated, predicted and experimentally supported material distinct.

## Ordered phases

| Phase | Completion | Prerequisite | Deliverable / exit gate |
|---|---:|---|---|
| P1 representation and provenance contracts | 100% | Activation audit | Inventory producers; define supported representations, identity/revision binding, unsupported/unknown states and artifact validation. Specify missing producer work explicitly; do not fabricate structures from scalar inputs. |
| P2 recommendation evidence | 100% | P1 complete | Consume an explicit retained selection result, including objective/constraints/policy, candidate set and trade-offs. Verify missing policy, ties, incomparable candidates and insufficient evidence remain truthful. |
| P3 candidate inspector | 100% | P2 complete | Results entry point, 2D structure/repeat-unit or composition rendering, property/synthesis evidence and selection rationale, linked to exact execution and lineage. Safe bounded rendering and module replacement README. |
| P4 verification and audit | 100% | P3 complete | Module-scoped contract/model/rendering tests and actual retained-artifact browser proof; inspect desktop/mobile/accessibility, wrong candidate/revision, malformed structures and missing evidence. Complete scoped architecture drift audit before closeout. |

## P3 bounded deliveries

Three equal deliveries: P3.1 authenticated owner reads, projection and protected PNG
loading (100%); P3.2 Results discovery, candidate panel and execution navigation (100%);
P3.3 integrated scoped regression and replacement boundary closeout (100%).
Actual owner/browser/local-LAN acceptance remains P4.

## P4 bounded deliveries

Four equal gates: actual installed-owner/Gateway browser (100%); existing TLS/LAN
browser path (100%); frozen demo static upgrade/regression and operational handoff
(100%); final component drift audit (100%). Second-computer firewall path remains the
previous LAN-01 acceptance unless separately rechecked; do not infer it from localhost.

## Integration boundaries and exclusions

Owner sequence2026-10-08 20:19:11: complete this candidate-level inspector and
the Knowledge/LLM end-to-end workflow before POP-01. Its population experience
will reuse this inspector for a selected candidate and own generation tables,
aggregate execution and lineage navigation. Keep that larger tranche separate;
ML-01 now follows POP-01 qualification.

Reuse existing bounded output reads where sufficient. Coordinate broader discovery
with [UI-01.01 result discovery](../UI-01/UI-01.01%20Campaign%20result%20discovery%20decision.md);
that proposal is not approval for a new Runtime API and is not a molecule renderer.
Do not duplicate scientific ranking in Studio or add chemical interpretation to Runtime.
Candidate generation/optimization remains a scientific-tool responsibility; this
plan must identify and sequence any missing producer dependency before claiming an
end-to-end recommendation experience. Keep tests within their owning modules.

Three-dimensional visualization is a separately scoped follow-on. It needs actual
coordinates or conformational/ensemble modeling, method and conditions, provenance,
and uncertainty. A polymer does not acquire one authoritative physical shape from
a repeat-unit drawing. Do not invent coordinates or display an illustrative model
as a predicted conformation. Simulation capability, compute budgets and scientific
validation are outside this first delivery.

Latest checkpoint 2026-10-13 11:30:04: P1.1 complete;12 focused checks,24 unaffected publication checks plus2 corrected historical-count checks pass; all668 predecessor pins unchanged; dependency boundary guard passes. [History](../UI-02/Completed/UI-02%20Planning%20History.md).

2026-10-13 11:37:38: P1.2 complete;32 copied tests pass in independent wheel installation, exact public schemas, two fresh-process deterministic results and visually inspected PNG. No service implementations installed;0model calls. Actual graph/Research acceptance remains P1.4.

2026-10-13 11:43:38: P1.3 complete;75 actual PostgreSQL/registration/identity regressions pass, explicit chemical host configuration, exact candidate binding, denial/replay/immutable history and malformed bundles. Schema compatibility2 and dependency guard pass.

2026-10-13 17:19:28: approved UI-02.03 execution correction37.5% (100/50/0/0); Runtime234 and SDK105 source tests pass; independent handoff next. Parent P1.4 remains0%, overall18.75%.
