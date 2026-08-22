# amphora-solver-lab

A genuine constrained formulation optimizer whose AUTHORITY is bounded, not its
capability.

## Authority posture

capability real, authority AUDIT_ONLY, promotion requires human ceremony.

The solver actually optimizes: exhaustive DoE enumeration, deterministic
continuous blend optimization over the composition simplex (projected gradient
with sort-based simplex projection), and NSGA-II multi-objective fronts with a
pinned seed. What it refuses to do is claim authority for the results. Every
output carries `authority: "AUDIT_ONLY"` and claim locks
(`promotes_authority: false`, `modifies_manifest: false`), is DSSE-Ed25519
signed under the pinned phase0 evaluator key, and passes a two-replay
byte-stability gate. Nothing this crate emits promotes evidence, flips
scientific readiness, or modifies the portfolio manifest; promotion requires
human ceremony.

## Oracles

Property sources are read EXCLUSIVELY from already-signed KPI/receipt JSON in
the tree (ingredient-library `facts.json` constants, GHS/CLP hazard KPI,
coating-candidate design-card KPI, formulation-universe known-answer fixture,
envelope-gates known-answer fixture). No live model calls, no new science.
Every oracle read is sha256-pinned against `pins/source_pins.v1.json`; a
tampered or relocated source is refused (fail-closed), and every diagnostic
records the source path + sha256 it read.

## Determinism by construction

f64 only; ordered reductions (sorted iteration and sequential sums where order
matters); pinned splitmix64 seeds for NSGA-II with deterministic tournament and
index tie-breaks; `serde_json` with `float_roundtrip` (workspace convention);
no HashMap anywhere on a result path (BTreeMap only). Each demo binary run
twice must produce byte-identical diagnostics; the signer refuses to sign if
the two replays differ.

## Demos

- `evidence/phase0/demos/p1-voc-min-solvent-blend/` — VOC-minimizing solvent
  blend under volume-solids, Hansen-RED, flash-point and VOC-cap constraints.
- `evidence/phase0/demos/p3-hazard-constrained-hardener-selection/` —
  hazard-constrained hardener selection; honestly reports an EMPTY feasible set
  with named blocking constraints per candidate (`pareto_status: BLOCKED`).
- `evidence/phase0/demos/p4-2to4-full-factorial-screen/` — 2^4 full-factorial
  DoE screen with mass-balance + envelope-gate + GHS constraints; reports the
  solved/infeasible partition with per-cell reasons.

Receipts are produced by `benchmarks/sign_solver_lab_demos.py`, which
replicates the portfolio DSSE conventions (PAE, evaluator seed, trust-store
key-id pinning, self-verification) from
`amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py`.
