# UI-02 Candidate Structure and Recommendation Views

## Canonical tracker

- Status: scheduled for2026-10-12 through2026-10-16; planning only, implementation not started.
- Last refreshed: 2026-10-08 18:42:19 (America/Chicago).
- Overall implementation: 0%; Build0%, Verification0%. Four equal delivery phases;
  Build averages P1/P2/P3, Verification is P4. Planning earns no implementation credit.
- Owner: Studio candidate inspection; scientific tools own candidate representations
  and evaluation/selection outputs, Runtime owns accepted execution references,
  Data owns immutable artifact access.
- Current focus: capture the missing candidate structure and recommendation experience.
- Next gate: bounded activation audit, inventory actual candidate-producing contracts,
  then freeze the initial representation and selection-evidence boundary.
- Dependencies: retained candidate structures and explicit recommendation evidence;
  existing demo parameter sets provide neither. New public contracts require the
  normal schema-first review. No dependency is assumed implemented by this plan.
- Acceptance: not started; current demo and active-plan percentages remain unchanged.
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
not permission to bypass producer or selection gates. All phase percentages stay0%.

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
| P1 representation and provenance contracts | 0% | Activation audit | Inventory producers; define supported representations, identity/revision binding, unsupported/unknown states and artifact validation. Specify missing producer work explicitly; do not fabricate structures from scalar inputs. |
| P2 recommendation evidence | 0% | P1 complete | Consume an explicit retained selection result, including objective/constraints/policy, candidate set and trade-offs. Verify missing policy, ties, incomparable candidates and insufficient evidence remain truthful. |
| P3 candidate inspector | 0% | P2 complete | Results entry point, 2D structure/repeat-unit or composition rendering, property/synthesis evidence and selection rationale, linked to exact execution and lineage. Safe bounded rendering and module replacement README. |
| P4 verification and audit | 0% | P3 complete | Module-scoped contract/model/rendering tests and actual retained-artifact browser proof; inspect desktop/mobile/accessibility, wrong candidate/revision, malformed structures and missing evidence. Complete scoped architecture drift audit before closeout. |

## Integration boundaries and exclusions

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
