# UI-02 Candidate Structure and Recommendation Views

## Canonical tracker

- Status: P1 active; owner approved UI-02.01; P1.1-P1.3 complete; P1.4 blocked on Registry profile decision UI-02.02.
- Last refreshed: 2026-10-13 11:53:07 (America/Chicago).
- Overall implementation: 18.75%; Build25%, Verification0%. Four equal delivery phases;
  Build averages P1/P2/P3, Verification is P4. Planning earns no implementation credit.
- Owner: Studio candidate inspection; scientific tools own candidate representations
  and evaluation/selection outputs, Runtime owns accepted execution references,
  Data owns immutable artifact access.
- Current focus: [UI-02.01 chemical structure boundary](UI-02.01%20Chemical%20structure%20boundary%20decision.md); P1.1 contracts verified; P1.3 opt-in Research registration verified; P1.4 registered handoff blocked: Registry activation_profile_denied; [UI-02.02](UI-02.02%20Structural%20tool%20registry%20profile%20decision.md) is reviewable.
- Next gate: owner direction on UI-02.02, then configured Registry activation/selection and actual P1.4 handoff.
- Dependencies: retained candidate structures and explicit recommendation evidence;
  existing demo parameter sets provide neither. New public contracts require the
  normal schema-first review. No dependency is assumed implemented by this plan.
- Acceptance: not started; [activation audit](../Audits/UI-02_Activation.md) identifies the synthetic-only admission gap. P1.1/P1.2/P1.3=100%, P1.4=0%; existing frozen local/LAN demo restored after source work; UI-02 features not served.
- Parent: none; priority is owned by [Master Build Tracker](Master%20Build%20Tracker.md).

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
not permission to bypass producer or selection gates. P1 is75% from three of four equal deliveries; P2/P3/P4 remain0%.

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
| P1 representation and provenance contracts | 75% | Activation audit | Inventory producers; define supported representations, identity/revision binding, unsupported/unknown states and artifact validation. Specify missing producer work explicitly; do not fabricate structures from scalar inputs. |
| P2 recommendation evidence | 0% | P1 complete | Consume an explicit retained selection result, including objective/constraints/policy, candidate set and trade-offs. Verify missing policy, ties, incomparable candidates and insufficient evidence remain truthful. |
| P3 candidate inspector | 0% | P2 complete | Results entry point, 2D structure/repeat-unit or composition rendering, property/synthesis evidence and selection rationale, linked to exact execution and lineage. Safe bounded rendering and module replacement README. |
| P4 verification and audit | 0% | P3 complete | Module-scoped contract/model/rendering tests and actual retained-artifact browser proof; inspect desktop/mobile/accessibility, wrong candidate/revision, malformed structures and missing evidence. Complete scoped architecture drift audit before closeout. |

## Integration boundaries and exclusions

Owner sequence2026-10-08 20:19:11: complete this candidate-level inspector and
the Knowledge/LLM end-to-end workflow before POP-01. Its population experience
will reuse this inspector for a selected candidate and own generation tables,
aggregate execution and lineage navigation. Keep that larger tranche separate;
ML-01 now follows POP-01 qualification.

Reuse existing bounded output reads where sufficient. Coordinate broader discovery
with [UI-01.01 result discovery](UI-01.01%20Campaign%20result%20discovery%20decision.md);
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

Latest checkpoint 2026-10-13 11:30:04: P1.1 complete;12 focused checks,24 unaffected publication checks plus2 corrected historical-count checks pass; all668 predecessor pins unchanged; dependency boundary guard passes. [History](UI-02%20Planning%20History.md).

2026-10-13 11:37:38: P1.2 complete;32 copied tests pass in independent wheel installation, exact public schemas, two fresh-process deterministic results and visually inspected PNG. No service implementations installed;0model calls. Actual graph/Research acceptance remains P1.4.

2026-10-13 11:43:38: P1.3 complete;75 actual PostgreSQL/registration/identity regressions pass, explicit chemical host configuration, exact candidate binding, denial/replay/immutable history and malformed bundles. Schema compatibility2 and dependency guard pass.
