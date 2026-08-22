# multicomponent-constraint-polytope-v1 (AUDIT_ONLY)

Theory-axis oracle for amphora-formulation-universe. Direct continuation of
simplex-mixture-geometry-v1, whose honest negative it converts into a
demonstrated positive.

**Claim under test:** the prior increment certified box-bounded mixture
regions (`sum(x)=1`, `l<=x<=u`) and recorded that the Snee-Marquardt 1974
caveat could NOT fire there: with box-only bounds every screened
McLean-Anderson candidate is necessarily extreme and the MA candidate set is
vertex-complete. Real coating windows are not box-only: a **PVC band**
(Asbeck & Van Loo 1949) and an **amine-H:epoxide stoichiometric band**
(Lee & Neville 1967) are ratio constraints that linearize to multicomponent
linear constraints on weight fractions. H0 under test: *the MA bound-only
candidate set remains vertex-complete once such constraints are added.*

**Baselines (all primary, with DOI/ISBN):**
- Snee 1979, Commun. Stat. A8(4):303-326, doi:10.1080/03610927908827762 —
  extreme vertices of linearly constrained mixture regions.
- Piepel 1988, J. Qual. Technol. 20(2):125-136,
  doi:10.1080/00224065.1988.11979094 — CONVRT/CONAEV (face centroid = average
  of vertices on the face).
- Snee & Marquardt 1974, Technometrics 16(3):399-408,
  doi:10.1080/00401706.1974.10489209 — the caveat under test.
- McLean & Anderson 1966, Technometrics 8(3):447-454,
  doi:10.1080/00401706.1966.10490377 — generator under test.
- Motzkin/Raiffa/Thompson/Thrall 1953, Annals of Math. Studies 28,
  ISBN 978-0-691-07935-6 — independent double-description parity path.
- Asbeck & Van Loo 1949, Ind. Eng. Chem. 41(7):1470-1475,
  doi:10.1021/ie50475a042 — PVC.
- Lee & Neville 1967, McGraw-Hill, ISBN 978-0-07-036997-9 — stoichiometric
  index r = (x_am/AHEW)/(x_ep/EEW).
- Cornell 2002, 3rd ed., ISBN 0-471-07916-2 — ratio constraints.

**Gates (5/5 PASS, exact rational arithmetic, no float in any decision):**
- **G1** Ratio-band linearization — PVC and stoich bands are EXACTLY
  equivalent to their linear half-space pairs at every test point (box-feasible
  {q,6} lattice + vertices + vertex midpoints; 9 region×ratio cases; up to 465
  points/case incl. points exactly on the band boundary); denominators provably
  positive from the declared lower bounds.
- **G2** Dual-method vertex parity — Snee-1979-style basic-feasible-solution
  enumeration == Motzkin-1953 sequential double description on 6 marine
  epoxy-amine regions: **76 vertices, set-equal 6/6**, every vertex feasible,
  rank-certified extreme, distinct.
- **G3** H0 REFUTED 6/6 — the MA bound-only candidate set is
  vertex-INCOMPLETE under multicomponent constraints: **70 of 76 true vertices
  are missing**, and every missing vertex has a band row active (exact).
  Feasible MA box-vertices all remain extreme (theorem, verified). Per-region
  worst case: marine-primer-4c loses 14/14 (all 12 box vertices are cut off by
  the bands and all 14 constrained vertices live on band facets).
- **G4** Piepel 1988 CONAEV conformance — face centroids (average of the
  vertices on each face with >= 1 vertex) lie exactly on the face hyperplane
  and are feasible; overall centroid feasible and strictly interior to every
  non-degenerate face; 43 face cases across 6 regions.
- **G5** Affine dimension — exact rank of the vertex set matches the declared
  dimension in 6/6, including the degenerate 1:1-stoichiometry region
  (band lower == upper) collapsing to dimension 1 with exactly 2 vertices;
  box-only vs constrained vertex counts quantified per region
  (e.g. 5-component topcoat: 25 -> 30).

**Fail-closed probes: 14/14 rejected** — inverted PVC band, PVC band that
empties the region, stoich band that empties the region, zero stoich lower,
zero density, negative density, float (non-string) density, NaN AHEW, zero
EEW, unknown pigment component, component in both pigment and binder roles,
epoxy lower bound 0 (stoich denominator may vanish), empty pigment list,
non-numeric band. Emptiness detection is fail-closed via the theorem that a
bounded non-empty polytope has a vertex.

**Two-replay:** byte-identical, sha256 `808fba87...`.

**Phase-1 implication:** a formulation-universe generator enumerating coating
windows must use a multicomponent-constraint vertex algorithm (Snee 1979 /
Piepel 1988 / double description); bound-only MA generation silently drops
92.1% of the audited regions' true extreme formulations the moment a PVC or
stoichiometric band binds. This receipt does not authorise that change; it is
AUDIT_ONLY evidence for it.

**Authority:** AUDIT_ONLY. Does not promote, flip `scientific_readiness`, edit
the portfolio manifest (66/11), any locked dataset, the signed Phase-0 KPI, or
the live Rust engine. Signed under the Phase-0 evaluator seed
(keyid `3ef6b35c...`), DSSE PAE + Ed25519; envelope sha256 `60a7a802...`.

Files: `run_multicomponent_constraint_polytope.py` (harness),
`diagnostic.canonical.json` / `diagnostic.runB.json` (two replays),
`sign_multicomponent_constraint_polytope.py` (signer),
`multicomponent-constraint-polytope-receipt.v1.dsse.json` (signed receipt).
New rights-clean anchor dataset:
`reference/mvp20/data/formulation_multicomponent_constraint_anchors.v1.json`
(CC0-1.0, sha256 `2017f08d...`).
